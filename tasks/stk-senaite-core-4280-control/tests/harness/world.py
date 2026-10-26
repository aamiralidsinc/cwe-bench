# -*- coding: utf-8 -*-
"""Offline harness for the SENAITE JSON API routes.

It synthesises the parts of the Plone/Archetypes runtime that the JSON API
modules import, then drives the *real* route classes from the product tree
(``/workspace/src``) with a fake portal, request and content objects.

The permission model follows the SENAITE rolemap: a content object answers
``allowed_roles(permission)`` from its own map or its parent's.
"""

import ast
import os
import sys
import types

HERE = os.path.dirname(os.path.abspath(__file__))
STUBS = os.path.join(HERE, "stubs")
PRODUCT_SRC = os.environ.get("SENAITE_SRC", "/workspace/src")
for _path in (STUBS, PRODUCT_SRC):
    if _path not in sys.path:
        sys.path.insert(0, _path)

API_SOURCE = os.path.join(PRODUCT_SRC, "bika", "lims", "api", "__init__.py")

from AccessControl import SecurityManager  # noqa: E402
from AccessControl import setSecurityManager  # noqa: E402
from AccessControl.Permissions import DeleteObjects  # noqa: E402,F401
from AccessControl.Permissions import ModifyPortalContent  # noqa: E402,F401
from AccessControl.Permissions import View  # noqa: E402,F401

ROLE_ALL = ["Analyst", "Client", "LabClerk", "LabManager", "Manager",
            "Publisher", "Sampler", "SamplingCoordinator", "Verifier"]

PERM_ACCESS_JSONAPI = "senaite.core: Access JSON API"
PERM_EDIT_REMARKS = "senaite.core: Field: Edit Remarks"


def _module(name, path=None):
    mod = types.ModuleType(name)
    if path:
        mod.__path__ = [path]
    mod.__file__ = os.path.join(path or "", "__init__.py")
    return mod


class _Placeholder(object):
    """Permissive stand-in for a dependency that is not available offline."""

    def __init__(self, name):
        self._name = name

    def __call__(self, *args, **kwargs):
        return _Placeholder(self._name)

    def __getattr__(self, name):
        if name.startswith("__") and name.endswith("__"):
            raise AttributeError(name)
        return _Placeholder("%s.%s" % (self._name, name))

    def __iter__(self):
        return iter(())

    def __nonzero__(self):
        return True

    def __repr__(self):
        return "<placeholder %s>" % self._name


class _PlaceholderModule(types.ModuleType):
    def __getattr__(self, name):
        if name.startswith("__") and name.endswith("__"):
            raise AttributeError(name)
        value = _Placeholder("%s.%s" % (self.__name__, name))
        setattr(self, name, value)
        return value


def _placeholder_module(name):
    mod = _PlaceholderModule(name)
    mod.__path__ = []
    return mod


def _ensure_module(name, created, links):
    """Return ``name`` imported, or a placeholder standing in for it."""
    if name in sys.modules:
        return sys.modules[name], False
    try:
        __import__(name)
    except Exception:
        pass
    if name in sys.modules:
        return sys.modules[name], False
    parts = name.split(".")
    for i in range(1, len(parts) + 1):
        prefix = ".".join(parts[:i])
        if prefix in sys.modules:
            continue
        mod = _placeholder_module(prefix)
        sys.modules[prefix] = mod
        created.append(prefix)
        if i > 1:
            parent = sys.modules[".".join(parts[:i - 1])]
            setattr(parent, parts[i - 1], mod)
            links.append((parent, parts[i - 1]))
    return sys.modules[name], True


_real_api = [None]
_real_api_loading = [False]


def _load_real_api():
    """Run the product's own ``bika.lims.api`` source and return its namespace.

    The stub above only defines the helpers the harness drives directly.  A
    fix may add a helper to the product's API module, so the real module is
    executed once with its unimportable dependencies replaced by placeholders.
    """
    if _real_api[0] is not None:
        return _real_api[0]
    if _real_api_loading[0]:
        raise AttributeError("bika.lims.api")
    _real_api_loading[0] = True
    created, patched, links = [], [], []
    try:
        handle = open(API_SOURCE)
        try:
            source = handle.read()
        finally:
            handle.close()
        tree = ast.parse(source, API_SOURCE)
        for node in tree.body:
            if isinstance(node, ast.ImportFrom):
                if node.level:
                    continue
                mod, _ = _ensure_module(node.module, created, links)
                for alias in node.names:
                    if alias.name == "*" or hasattr(mod, alias.name):
                        continue
                    # Prefer a real submodule over a placeholder.
                    try:
                        __import__("%s.%s" % (node.module, alias.name))
                    except Exception:
                        pass
                    if hasattr(mod, alias.name):
                        continue
                    setattr(mod, alias.name, _Placeholder(alias.name))
                    patched.append((mod, alias.name))
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    _ensure_module(alias.name, created, links)
        namespace = {"__name__": "bika.lims.api", "__file__": API_SOURCE}
        try:
            exec(compile(source, API_SOURCE, "exec"), namespace)
        finally:
            for name in created:
                sys.modules.pop(name, None)
            for mod, attr in patched:
                try:
                    delattr(mod, attr)
                except AttributeError:
                    pass
            for parent, attr in links:
                try:
                    delattr(parent, attr)
                except AttributeError:
                    pass
        _real_api[0] = namespace
        return namespace
    finally:
        _real_api_loading[0] = False


class _StubApi(types.ModuleType):
    def __init__(self):
        types.ModuleType.__init__(self, "bika.lims.api")

    def __getattr__(self, name):
        # Anything a fix adds to the product API module is still reachable.
        if name.startswith("__") and name.endswith("__"):
            raise AttributeError(name)
        namespace = _load_real_api()
        try:
            return namespace[name]
        except KeyError:
            raise AttributeError(
                "module 'bika.lims.api' has no attribute %r" % (name,))

    def get_fields(self, instance):
        return dict(instance.Schema().items())

    def is_dexterity_content(self, instance):
        return False

    def get_uid(self, obj):
        return getattr(obj, "_uid", None)

    def get_object(self, uid, default=None):
        return _PORTAL.resolve_uid(uid) if _PORTAL is not None else default

    def get_portal(self):
        return _PORTAL

    def get_request(self):
        return getattr(_PORTAL, "_request", None)

    def get_current_user(self):
        from AccessControl import getSecurityManager
        return getSecurityManager().getUser()

    def is_anonymous(self):
        from AccessControl import getSecurityManager
        return getSecurityManager().getUser().getId() == "Anonymous User"

    def has_permission(self, permission, obj=None):
        from AccessControl import getSecurityManager
        return getSecurityManager().checkPermission(permission, obj)

    def to_int(self, value, default=0):
        try:
            return int(value)
        except (TypeError, ValueError):
            return default

    def to_utf8(self, value):
        return value

    def safe_unicode(self, value, encoding="utf-8"):
        if isinstance(value, unicode):  # noqa: F821
            return value
        if isinstance(value, str):
            return value.decode(encoding, "replace")
        return value

    def text_to_html(self, value):
        return value

    def is_uid(self, value):
        return isinstance(value, str) and len(value) == 32


class _StubUtils(types.ModuleType):
    def __init__(self):
        types.ModuleType.__init__(self, "bika.lims.utils")

    def to_utf8(self, value):
        if isinstance(value, unicode):  # noqa: F821
            return value.encode("utf-8")
        return value

    def tmpID(self):
        return "tmp00000000000000000000000000000"


def install():
    """Put the stubs and the product source on sys.path and pre-seed packages."""
    for path in (STUBS, PRODUCT_SRC):
        if path not in sys.path:
            sys.path.insert(0, path)

    import zope.interface  # noqa: F401  (real dependency)

    # ``bika`` / ``bika.lims`` are namespace-ish packages whose real __init__
    # pulls the whole Plone stack.  Seed them so only the submodules we need load.
    if "bika" not in sys.modules:
        bika = _module("bika", os.path.join(PRODUCT_SRC, "bika"))
        sys.modules["bika"] = bika
    bika = sys.modules["bika"]
    if "bika.lims" not in sys.modules:
        lims = _module("bika.lims", os.path.join(PRODUCT_SRC, "bika", "lims"))
        lims.api = _StubApi()
        lims.utils = _StubUtils()
        lims.logger = _logger()
        lims.bikaMessageFactory = _message_factory()
        lims.senaiteMessageFactory = lims.bikaMessageFactory
        lims._ = lims.bikaMessageFactory
        lims.PROJECTNAME = "bika.lims"
        sys.modules["bika.lims"] = lims
        sys.modules["bika.lims.api"] = lims.api
        sys.modules["bika.lims.utils"] = lims.utils
        bika.lims = lims

        # ``bika.lims.api.security`` is imported by the product's permission
        # package; seed it so the constants module loads without the full API.
        security = types.ModuleType("bika.lims.api.security")

        def check_permission(permission, context):
            from AccessControl import getSecurityManager
            return getSecurityManager().checkPermission(permission, context)

        security.check_permission = check_permission
        security.get_current_user = lambda: lims.api.get_current_user()
        security.is_anonymous = lambda: lims.api.is_anonymous()
        sys.modules["bika.lims.api.security"] = security
        lims.api.security = security
        lims.api.__path__ = [os.path.join(PRODUCT_SRC, "bika", "lims", "api")]
    lims = sys.modules["bika.lims"]
    for name, path in (("bika.lims.browser", os.path.join(PRODUCT_SRC, "bika", "lims", "browser")),
                       ("bika.lims.browser.fields", os.path.join(PRODUCT_SRC, "bika", "lims", "browser", "fields")),
                       ("senaite.core.browser.widgets", os.path.join(PRODUCT_SRC, "senaite", "core", "browser", "widgets"))):
        if name not in sys.modules:
            sys.modules[name] = _module(name, path)

    interfaces = types.ModuleType("bika.lims.interfaces")
    class _I(object):
        pass
    interfaces.IJSONReadExtender = _I
    interfaces.IRemarksField = _I
    interfaces.IClient = _I
    sys.modules["bika.lims.interfaces"] = interfaces
    lims.interfaces = interfaces


def _logger():
    import logging
    return logging.getLogger("senaite.core")


def _message_factory():
    def factory(msg, **kw):
        return msg
    return factory


# ---------------------------------------------------------------------------
# permission + content model
# ---------------------------------------------------------------------------

class Schema(object):
    def __init__(self, fields):
        self._fields = fields

    def __contains__(self, name):
        return name in self._fields

    def __getitem__(self, name):
        return self._fields[name]

    def __iter__(self):
        return iter(self._fields)

    def items(self):
        return self._fields.items()

    def keys(self):
        return self._fields.keys()

    def values(self):
        return self._fields.values()

    def fields(self):
        return list(self._fields.values())


class Content(object):
    def __init__(self, uid, path, title="", fields=None, permissions=None,
                 parent=None, methods=None):
        self._values = {}
        self._uid = uid
        self._path = path
        self._parent = parent
        self._fields = fields or {}
        self._permissions = permissions or {}
        self._methods = methods or {}
        self._created = 0
        if title:
            self._values["Title"] = title

    # -- schema -----------------------------------------------------------
    def Schema(self):
        return Schema(self._fields)

    # -- acquisition ------------------------------------------------------
    @property
    def aq_parent(self):
        return self._parent

    def absolute_url(self):
        return "http://localhost" + self._path

    def getPhysicalPath(self):
        return tuple(self._path.split("/"))

    def getId(self):
        return self._path.rsplit("/", 1)[-1]

    def UID(self):
        return self._uid

    @property
    def id(self):
        return self.getId()

    # -- permissions ------------------------------------------------------
    def allowed_roles(self, permission):
        if permission in self._permissions:
            return set(self._permissions[permission])
        if self._parent is not None:
            return self._parent.allowed_roles(permission)
        return set()

    # -- mutation ---------------------------------------------------------
    def reindexObject(self, *args, **kwargs):
        self._created += 0

    def _create(self, type_name, id):
        obj = Content("uid-" + id, self._path.rstrip("/") + "/" + id,
                      fields={}, permissions=self._permissions, parent=self)
        return obj

    # -- generated Archetypes mutators ------------------------------------
    def __getattr__(self, name):
        if name.startswith("set") and len(name) > 3:
            fieldname = name[3:]
            fields = self.__dict__.get("_fields", {})
            if fieldname in fields:
                field = fields[fieldname]

                def mutator(value, _field=field):
                    return _field.set(self, value)

                return mutator
        methods = self.__dict__.get("_methods", {})
        if name in methods:
            return methods[name]
        raise AttributeError(name)


class Brain(object):
    def __init__(self, obj):
        self._obj = obj
        self.UID = obj.UID()
        self.id = obj.getId()

    def getObject(self):
        return self._obj

    def getPath(self):
        return self._obj.getPhysicalPath()

    def indexes(self):
        return ["UID", "id", "portal_type", "path", "Title"]

    def __contains__(self, name):
        try:
            getattr(self, name)
            return True
        except AttributeError:
            return False

    def __getattr__(self, name):
        return getattr(self._obj, name)


class Catalog(object):
    def __init__(self, portal):
        self._portal = portal

    def indexes(self):
        return ["UID", "id", "portal_type", "path"]

    def __call__(self, **query):
        results = []
        for obj in self._portal._objects.values():
            ok = True
            if "UID" in query:
                wanted = query["UID"]
                if isinstance(wanted, (list, tuple)):
                    ok = obj.UID() in wanted
                else:
                    ok = obj.UID() == wanted
            if ok and "id" in query:
                ok = obj.getId() == query["id"]
            if ok and "portal_type" in query:
                ok = getattr(obj, "portal_type", None) == query["portal_type"]
            if ok:
                results.append(Brain(obj))
        return results


class _PortalURL(object):
    def __init__(self, portal):
        self._portal = portal

    def getPortalObject(self):
        return self._portal


class Portal(Content):
    def __init__(self, *args, **kwargs):
        Content.__init__(self, *args, **kwargs)
        self._objects = {}
        self.portal_url = _PortalURL(self)
        self.uid_catalog = Catalog(self)
        self.portal_catalog = Catalog(self)
        self.archetype_tool = self
        self.portal_workflow = WorkflowTool()
        self.portal_membership = MembershipTool()
        self.portal_type = "Plone Site"

    def register(self, obj):
        self._objects[obj.getId()] = obj
        return obj

    def resolve_uid(self, uid):
        for obj in self._objects.values():
            if obj.UID() == uid:
                return obj
        return None

    def restrictedTraverse(self, path):
        path = path.split("?")[0]
        parts = [p for p in path.split("/") if p]
        if parts and parts[-1] in self._objects:
            return self._objects[parts[-1]]
        for obj in self._objects.values():
            if obj.getPhysicalPath() == tuple(parts):
                return obj
        raise KeyError("not found: " + path)

    def getCatalogsByType(self, portal_type):
        return [self.portal_catalog]


class WorkflowTool(object):
    def __init__(self):
        self.calls = []

    def doActionFor(self, obj, action):
        self.calls.append((obj, action))
        obj._values["review_state"] = action

    def getTransitionsFor(self, obj):
        return []


class MembershipTool(object):
    def searchForMembers(self, roles=None):
        return []


class Request(object):
    """A Zope-like request: mapping access covers form values and CGI env."""

    def __init__(self, values=None, path_info="", method="POST"):
        self.form = dict(values or {})
        self.other = {}
        self.environ = {"REQUEST_METHOD": method, "PATH_INFO": path_info}

    @property
    def PATH_INFO(self):
        return self.environ.get("PATH_INFO", "")

    def __getitem__(self, key):
        if key in self.form:
            return self.form[key]
        if key in self.environ:
            return self.environ[key]
        raise KeyError(key)

    def __setitem__(self, key, value):
        self.form[key] = value

    def __contains__(self, key):
        return key in self.form

    def get(self, key, default=None):
        try:
            return self[key]
        except KeyError:
            return default

    def items(self):
        return self.form.items()

    def keys(self):
        return self.form.keys()

    def values(self):
        return self.form.values()

    def __iter__(self):
        return iter(self.form)


_PORTAL = None


def login(userid="analyst", roles=("Analyst", "Member")):
    from AccessControl import _User
    setSecurityManager(SecurityManager(_User(userid, roles)))


def logout():
    setSecurityManager(SecurityManager())


def user(userid, roles):
    from AccessControl import _User
    setSecurityManager(SecurityManager(_User(userid, list(roles))))
