"""Drive Glance's real HTTP services for the hidden suites.

The suites send real WSGI requests to the v1 API, the v2 API and the registry
service.  The v1 API's registry client is pointed at the in-process registry
WSGI application (the same seam the project's own tests use), so a request
travels the real controller, router, database API and filesystem store code.
Authentication is represented by the project's own context middleware: the
test builds the standard authentication headers and the registry side reads
the forwarded token, exactly as a deployed keystone middleware would.

Observations read the database with the standard sqlite3 module (or the
in-memory backend's own DATA mapping), so a hardened product helper cannot
change what a test sees.

Nothing here reaches the network and nothing is written outside a temporary
directory.
"""

import json
import os
import shutil
import sqlite3
import tempfile
import uuid

import routes
import webob

from glance.common import config
from glance.common import wsgi
from glance.openstack.common import cfg

CONF = cfg.CONF

_ADMIN_TENANT = 'admin-tenant'


def _register_and_configure(tmpdir):
    """Import the product modules (registering their options) and configure
    an isolated database and filesystem store."""
    config.parse_args(args=[])

    # Importing the product modules registers the config options.
    import glance.db
    import glance.store
    from glance.store import filesystem            # noqa: F401 (registers opt)
    from glance.api import policy                  # noqa: F401 (registers opt)
    from glance.db.sqlalchemy import api as db_api
    import glance.api.v1.images                    # noqa: F401 (registers opt)
    import glance.api.v2.images                    # noqa: F401
    import glance.api.v2.image_data                # noqa: F401
    import glance.registry.api.v1.images           # noqa: F401

    store_dir = os.path.join(tmpdir, 'store')
    scrubber_dir = os.path.join(tmpdir, 'scrubber')
    os.makedirs(store_dir)
    os.makedirs(scrubber_dir)
    policy_file = os.path.join(tmpdir, 'policy.json')
    handle = open(policy_file, 'w')
    handle.write(json.dumps({'default': '', 'manage_image_cache': 'role:admin'}))
    handle.close()

    db_path = os.path.join(tmpdir, 'glance.sqlite')
    CONF.set_override('sql_connection', 'sqlite:///' + db_path)
    CONF.set_override('db_auto_create', True)
    CONF.set_override('default_store', 'filesystem')
    CONF.set_override('filesystem_store_datadir', store_dir)
    CONF.set_override('scrubber_datadir', scrubber_dir)
    CONF.set_override('policy_file', policy_file)
    CONF.set_override('verbose', False)
    CONF.set_override('debug', False)

    db_api.configure_db()
    glance.store.create_stores()
    return db_api, db_path, store_dir, scrubber_dir


class _RegistryConnection(object):
    """An httplib-shaped connection that serves the in-process registry app."""

    def __init__(self, *args, **kwargs):
        self.req = None

    def connect(self):
        return True

    def close(self):
        return True

    def request(self, method, url, body=None, headers=None):
        self.req = webob.Request.blank('/' + url.lstrip('/'))
        self.req.method = method
        if headers:
            self.req.headers = headers
        if body:
            self.req.body = body

    def getresponse(self):
        res = self.req.get_response(get_world().registry_app)

        class _Response(object):
            def __init__(self, response):
                self.status = response.status_int
                self.headers = dict(response.headers)
                self._body = response.body

            def read(self, *args):
                return self._body

            def getheader(self, name, default=None):
                return self.headers.get(name.lower(), default)

            def getheaders(self):
                return self.headers

        return _Response(res)


class _RegistryAuthMiddleware(wsgi.Middleware):
    """Stand-in for the registry service's keystone authentication.

    The API server forwards the caller's token; this middleware turns it into
    the same RequestContext the API server built (user:tenant:role).
    """

    def process_request(self, req):
        import glance.context
        token = req.headers.get('X-Auth-Token')
        if not token:
            raise webob.exc.HTTPUnauthorized()
        parts = token.split(':')
        if len(parts) != 3:
            raise webob.exc.HTTPUnauthorized()
        user, tenant, role = parts
        roles = [role] if role else []
        req.context = glance.context.RequestContext(
            user=user, tenant=tenant, roles=roles,
            is_admin=bool(role) and role.lower() == 'admin', auth_tok=token)


class World(object):
    def __init__(self):
        self.tmpdir = tempfile.mkdtemp(prefix='glance-hidden-')
        (self.db_api, self.db_path, self.store_dir,
         self.scrubber_dir) = _register_and_configure(self.tmpdir)
        self.registry_app = None
        self.apps = {}
        self.use_sqlalchemy()

    # -- application wiring -------------------------------------------------
    def _build_apps(self):
        import glance.api.v1.router
        import glance.api.v2.router
        import glance.registry.api.v1
        from glance.api.middleware import context as context_middleware

        self.registry_app = _RegistryAuthMiddleware(
            glance.registry.api.v1.API(routes.Mapper()))
        self.apps = {
            'v1': context_middleware.ContextMiddleware(
                glance.api.v1.router.API(routes.Mapper())),
            'v2': context_middleware.ContextMiddleware(
                glance.api.v2.router.API(routes.Mapper())),
        }

    @staticmethod
    def _install_registry_seam():
        from glance.common import client
        client.BaseClient.get_connection_type = \
            lambda self: _RegistryConnection

    # -- configuration ------------------------------------------------------
    def use_sqlalchemy(self):
        CONF.set_override('data_api', 'glance.db.sqlalchemy.api')
        self._build_apps()

    def use_simple(self):
        import glance.db.simple.api as simple_api
        simple_api.reset()
        CONF.set_override('data_api', 'glance.db.simple.api')
        self._build_apps()
        return simple_api

    def set_delayed_delete(self, value):
        CONF.set_override('delayed_delete', bool(value))

    def reset_overrides(self):
        for name in ('delayed_delete', 'data_api'):
            try:
                CONF.clear_override(name)
            except Exception:
                pass
        self.use_sqlalchemy()

    # -- requests -----------------------------------------------------------
    @staticmethod
    def _headers(tenant, admin=False):
        role = 'admin' if admin else ''
        return {
            'X-Identity-Status': 'Confirmed',
            'X-User-Id': tenant,
            'X-Tenant-Id': tenant,
            'X-Roles': role,
            'X-Auth-Token': '%s:%s:%s' % (tenant, tenant, role),
        }

    def request(self, service, method, path, tenant, admin=False, body=None,
                content_type=None, headers=None):
        req = webob.Request.blank(path)
        req.method = method
        req.headers.update(self._headers(tenant, admin=admin))
        if headers:
            req.headers.update(headers)
        if body is not None:
            req.body = body
        if content_type is not None:
            req.content_type = content_type
        app = self.registry_app if service == 'registry' else self.apps[service]
        return req.get_response(app)

    # -- fixtures -----------------------------------------------------------
    def create_image(self, owner, public=False, protected=False,
                     with_data=True, data='ZZZZZ', status='active'):
        image_id = str(uuid.uuid4())
        location = None
        if with_data:
            location = 'file://' + os.path.join(self.store_dir, image_id)
            handle = open(os.path.join(self.store_dir, image_id), 'wb')
            handle.write(data)
            handle.close()
        # Use the real database API with an administrator context.
        import glance.context
        context = glance.context.RequestContext(is_admin=True,
                                                tenant=_ADMIN_TENANT)
        values = {
            'id': image_id,
            'name': 'image-%s' % image_id[:8],
            'status': status,
            'disk_format': 'raw',
            'container_format': 'bare',
            'is_public': public,
            'owner': owner,
            'protected': protected,
            'location': location,
            'properties': {},
        }
        if with_data:
            values['size'] = len(data)
        self.db_api.image_create(context, values)
        return image_id

    def share_image(self, image_id, member):
        import glance.context
        context = glance.context.RequestContext(is_admin=True,
                                                tenant=_ADMIN_TENANT)
        self.db_api.image_member_create(context, {
            'image_id': image_id, 'member': member, 'can_share': False})

    @staticmethod
    def create_simple_image(simple_api, owner, public=False, protected=False,
                            name='simple-image'):
        image_id = str(uuid.uuid4())
        simple_api.image_create(None, {
            'id': image_id,
            'name': name,
            'status': 'active',
            'disk_format': 'raw',
            'container_format': 'bare',
            'is_public': public,
            'owner': owner,
            'protected': protected,
            'properties': {},
        })
        return image_id

    # -- observations -------------------------------------------------------
    def _sqlite_row(self, image_id):
        connection = sqlite3.connect(self.db_path)
        try:
            cursor = connection.cursor()
            cursor.execute('SELECT id, name, owner, status, protected, '
                           'deleted, location FROM images WHERE id = ?',
                           (image_id,))
            row = cursor.fetchone()
        finally:
            connection.close()
        if row is None:
            return None
        return {'id': row[0], 'name': row[1], 'owner': row[2],
                'status': row[3], 'protected': bool(row[4]),
                'deleted': bool(row[5]), 'location': row[6]}

    def meta(self, image_id):
        return self._sqlite_row(image_id)

    def image_live(self, image_id):
        row = self._sqlite_row(image_id)
        return row is not None and not row['deleted']

    def store_path(self, image_id):
        return os.path.join(self.store_dir, image_id)

    def data_present(self, image_id):
        return os.path.exists(self.store_path(image_id))

    def queue_path(self, image_id):
        return os.path.join(self.scrubber_dir, str(image_id))

    def queue_present(self, image_id):
        return os.path.exists(self.queue_path(image_id))


_WORLD = None


def get_world():
    global _WORLD
    if _WORLD is None:
        world = World()
        world._install_registry_seam()
        _WORLD = world
    return _WORLD


def assert_client_error(testcase, response, what):
    """The refusal form: a client error, not a success and not a crash."""
    testcase.assertTrue(400 <= response.status_int < 500,
                        '%s: expected a client error, got HTTP %s'
                        % (what, response.status_int))
