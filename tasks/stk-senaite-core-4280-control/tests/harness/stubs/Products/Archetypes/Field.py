"""Minimal Archetypes Field model for the offline harness.

Only the parts the JSON API and the record fields touch are modelled.  A field
stores its value in the instance's ``_values`` mapping through ``ObjectField.set``.
"""

from AccessControl import getSecurityManager
from AccessControl.Permissions import ModifyPortalContent
from AccessControl.Permissions import View

from Products.CMFCore.permissions import ModifyPortalContent as _MPC  # noqa: F401


def className(instance):
    klass = instance.__class__
    return klass.__module__ + "." + klass.__name__


def decode(value, instance=None, **kwargs):
    return value


def encode(value, instance=None, **kwargs):
    return value


class _Storage(object):
    pass


class BaseField(object):
    _properties = {
        "old_field_name": None,
        "required": False,
        "default": None,
        "default_method": None,
        "vocabulary": (),
        "vocabulary_factory": None,
        "enforceVocabulary": False,
        "multiValued": False,
        "searchable": False,
        "isMetadata": False,
        "accessor": None,
        "edit_accessor": None,
        "mutator": None,
        "mode": "rw",
        "read_permission": View,
        "write_permission": ModifyPortalContent,
        "storage": _Storage(),
        "generateMode": "veVc",
        "force": "",
        "type": None,
        "widget": None,
        "validators": (),
        "index": None,
        "index_method": "_at_accessor",
        "schemata": "default",
        "languageIndependent": False,
    }

    def __init__(self, name=None, **kwargs):
        self.__name__ = name
        for key, value in self._properties.items():
            setattr(self, key, value)
        for key, value in kwargs.items():
            setattr(self, key, value)
        if not getattr(self, "mutator", None) and name:
            self.mutator = "set" + name

    # -- identity ---------------------------------------------------------
    def getName(self):
        return self.__name__

    def getType(self):
        return className(self)

    def getWidgetName(self):
        widget = getattr(self, "widget", None)
        if widget is None:
            return None
        if isinstance(widget, type):
            return widget.__name__
        return getattr(widget, "__name__", widget.__class__.__name__)

    def getSubfields(self):
        return getattr(self, "subfields", ())

    # -- access -----------------------------------------------------------
    def getMutator(self, instance):
        mutator = getattr(self, "mutator", None)
        if mutator:
            found = getattr(instance, mutator, None)
            if found is not None:
                return found
        return None

    def getAccessor(self, instance):
        accessor = getattr(self, "accessor", None)
        if accessor:
            return getattr(instance, accessor, None)
        return None

    # -- permissions ------------------------------------------------------
    def checkPermission(self, mode, instance):
        if mode in ("w", "write", "edit", "set"):
            permission = self.write_permission
        elif mode in ("r", "read", "view", "get"):
            permission = self.read_permission
        else:
            return None
        return getSecurityManager().checkPermission(permission, instance)

    def getWritePermission(self):
        return self.write_permission

    def getReadPermission(self):
        return self.read_permission

    def writeable(self, instance, debug=False):
        if "w" not in (getattr(self, "mode", "") or ""):
            return False
        if not self.getMutator(instance):
            return False
        return bool(self.checkPermission("edit", instance))


class Field(BaseField):
    pass


class ObjectField(BaseField):
    def get(self, instance, **kwargs):
        return instance._values.get(self.getName(), self.default)

    def set(self, instance, value, **kwargs):
        instance._values[self.getName()] = value

    def unset(self, instance, **kwargs):
        instance._values.pop(self.getName(), None)


class StringField(ObjectField):
    _properties = ObjectField._properties.copy()
    _properties.update({"type": "string", "default": "", "widget": None})


class TextField(StringField):
    _properties = StringField._properties.copy()
    _properties.update({"type": "text", "default": "", "widget": None})


class BooleanField(ObjectField):
    _properties = ObjectField._properties.copy()
    _properties.update({"type": "boolean", "default": False})


class LinesField(ObjectField):
    _properties = ObjectField._properties.copy()
    _properties.update({"type": "lines", "default": []})


class IntegerField(ObjectField):
    _properties = ObjectField._properties.copy()
    _properties.update({"type": "integer", "default": 0})


class FloatField(ObjectField):
    _properties = ObjectField._properties.copy()
    _properties.update({"type": "float", "default": 0.0})


class FixedPointField(FloatField):
    _properties = FloatField._properties.copy()
    _properties.update({"type": "fixedpoint"})


class DateTimeField(ObjectField):
    _properties = ObjectField._properties.copy()
    _properties.update({"type": "datetime", "default": None})


class FileField(ObjectField):
    _properties = ObjectField._properties.copy()
    _properties.update({"type": "file", "default": None})


class ImageField(FileField):
    _properties = FileField._properties.copy()
    _properties.update({"type": "image"})


class Image(ImageField):
    pass


class ReferenceField(ObjectField):
    _properties = ObjectField._properties.copy()
    _properties.update({"type": "reference", "default": None, "multiValued": False})


class ComputedField(ObjectField):
    _properties = ObjectField._properties.copy()
    _properties.update({"type": "computed", "default": None})


class CMFObjectField(ReferenceField):
    pass


def log(message):
    pass
