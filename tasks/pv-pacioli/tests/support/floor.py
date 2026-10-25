"""A bench-free stand-in for the frappe site the consent gate runs on.

The product modules do ``import frappe`` at module top, so a module of that name is installed into
``sys.modules`` before they are imported and is kept pointed at one mutable ``Site``. Only the
surface the gate touches is modelled: the signed-in principal, the request headers, the *API Key
Scope* grant, the *Pacioli Consent Marker* table (including the conditional UPDATE that spends a
marker) and the document rows the marker loader may consult.

Nothing here is product code, and the tests compute their own expectations: a hardened product must
not be able to change what a test believes.
"""
import importlib
import sys
import time
import types

CONSENT_DOCTYPE = "Pacioli Consent Marker"
SCOPE_DOCTYPE = "API Key Scope"
CONSENT_HEADER = "X-Pacioli-Consent"


class Refusal(Exception):
    """What ``frappe.throw(..., frappe.PermissionError)`` raises on a real bench."""


class Row:
    def __init__(self, **kw):
        self.__dict__.update(kw)


class Grant:
    """An *API Key Scope* document. Deliberately lacks the verb_* columns, i.e. a grant loaded
    before ``bench migrate`` added them, which the wall reads as "all verbs"."""

    def __init__(self, require_consent=1):
        self.require_consent = require_consent
        self.enabled = 1
        self.allow_resource = 0
        self.methods = []
        self.resource_doctypes = []


class _Cursor:
    rowcount = None


class Site:
    """One site's state. A fresh one per test."""

    def reset(self, **kw):
        self.__init__(**kw)
        return self

    def __init__(self, *, user="broker@example.com", grant=True, require_consent=1):
        self.user = user
        self.headers = {}
        self.grants = {user: Grant(require_consent)} if grant else {}
        self.markers = {}        # {(ref_doctype, ref_docname): row}
        self.amended_from = {}   # {(doctype, name): origin name}
        self.burned = []         # marker names claimed, in order
        self.refusals = []       # refusal messages the site was asked to raise
        self.erased = []         # (doctype, name) the site would have erased
        self.reversed = []       # (doctype, name) the site would have cancelled
        self._seq = 0

    # -- arrangement -----------------------------------------------------------
    def present(self, header):
        self.headers[CONSENT_HEADER] = header
        return self

    def mint(self, doctype, docname, action, token, *, minted_by="accountant@example.com",
             ttl=900, burned=0, token_hash=None):
        from pacioli_guard.scope import consent_token_hash
        self._seq += 1
        name = f"PCM-{self._seq:04d}"
        self.markers[(doctype, docname)] = {
            "name": name,
            "token_hash": consent_token_hash(token) if token_hash is None else token_hash,
            "ref_doctype": doctype,
            "ref_docname": docname,
            "ref_action": action,
            "expires_at": time.time() + ttl,
            "burned": burned,
            "minted_by": minted_by,
        }
        return name

    def marker(self, doctype, docname):
        return self.markers.get((doctype, docname))

    def amends(self, doctype, name, origin):
        self.amended_from[(doctype, name)] = origin

    def burn_state(self, doctype, docname):
        row = self.markers.get((doctype, docname))
        return None if row is None else row.get("burned")


SITE = Site()
_CURSOR = _Cursor()


def _get_value(doctype, filters, fieldname=None, as_dict=False):
    if doctype == CONSENT_DOCTYPE:
        row = SITE.markers.get((filters.get("ref_doctype"), filters.get("ref_docname")))
        return dict(row) if (row and as_dict) else row
    if doctype == SCOPE_DOCTYPE and isinstance(filters, dict) and "user" in filters:
        return f"AKS::{filters['user']}" if filters["user"] in SITE.grants else None
    if isinstance(filters, str) and fieldname == "amended_from":
        return SITE.amended_from.get((doctype, filters))
    return None


def _sql(query, values=None, **kwargs):
    """The conditional UPDATE that spends a marker: exactly one caller may win an unburned row."""
    name = values[0] if isinstance(values, (list, tuple)) else values
    won = 0
    for row in SITE.markers.values():
        if row.get("name") == name and not row.get("burned"):
            row["burned"] = 1
            SITE.burned.append(name)
            won = 1
    _CURSOR.rowcount = won
    return []


def _get_doc(doctype, name):
    assert doctype == SCOPE_DOCTYPE, doctype
    return SITE.grants[name[len("AKS::"):]]


def _throw(message, exc=None):
    SITE.refusals.append(message)
    raise (exc or Refusal)(message)


def _install():
    module = sys.modules.get("frappe")
    if module is None or not getattr(module, "_pv_floor", False):
        module = types.ModuleType("frappe")
        module._pv_floor = True
        sys.modules["frappe"] = module
    module.session = types.SimpleNamespace(user=SITE.user)
    module.db = types.SimpleNamespace(
        get_value=_get_value,
        sql=_sql,
        _cursor=_CURSOR,
        has_column=lambda doctype, column: False,
        set_value=lambda *a, **k: None,
    )
    module.local = types.SimpleNamespace(request=None)
    module.form_dict = {}
    module.PermissionError = Refusal
    module.throw = _throw
    module.log_error = lambda *a, **k: None
    module.get_doc = _get_doc
    module.get_request_header = lambda key, default=None: SITE.headers.get(key, default)
    module.whitelist = lambda *a, **k: (lambda fn: fn)
    return module


FRAPPE = _install()


def handler(event):
    """The callable frappe itself would run for ``event``, resolved through the app's own
    ``hooks.doc_events`` registration. A gate that is not registered is a missing handler here,
    not a silently passing test."""
    from pacioli_guard import hooks
    path = (getattr(hooks, "doc_events", {}) or {}).get("*", {}).get(event)
    if not path:
        raise AssertionError(f"no handler registered for {event!r}")
    module_name, _, attr = path.rpartition(".")
    return getattr(importlib.import_module(module_name), attr)


# --- frappe's document-write frames, reproduced ---------------------------------------------
# The production signal reads three things off a live frame: the code name, the module the frame
# belongs to, and the document held in ``self``. A plain def can supply only one of them, so these
# are compiled into namespaces whose ``__name__`` really is the one frappe uses.
_DOCUMENT_NS = {"__name__": "frappe.model.document"}
exec(compile(
    "def _save(self, fn, *args):\n"
    "    return fn(*args)\n"
    "def insert(self, fn, *args):\n"
    "    return fn(*args)\n",
    "<frappe.model.document>", "exec"), _DOCUMENT_NS)
_save = _DOCUMENT_NS["_save"]
insert = _DOCUMENT_NS["insert"]

_CLIENT_NS = {"__name__": "frappe.client"}
exec(compile(
    "def insert(fn, *args):\n"
    "    return fn(*args)\n",
    "<frappe.client>", "exec"), _CLIENT_NS)
client_insert = _CLIENT_NS["insert"]


class Doc:
    """A document arriving at a lifecycle handler.

    ``in_insert`` mirrors frappe's own flag: True for a document the act itself creates and submits
    in one write, False for a document that already existed (loaded by name, or being cancelled)."""

    def __init__(self, doctype="Sales Invoice", name="SI-0001", in_insert=True, docstatus=0):
        self.doctype = doctype
        self.name = name
        self.docstatus = docstatus
        self.flags = {"in_insert": in_insert}


def submit(doc):
    handler("before_submit")(doc, "before_submit")


def cancel(doc):
    handler("before_cancel")(doc, "before_cancel")


def erase(doc):
    handler("on_trash")(doc, "on_trash")
