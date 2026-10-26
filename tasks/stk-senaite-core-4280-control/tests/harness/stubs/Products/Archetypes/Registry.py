_FIELDS = {}
_WIDGETS = {}
_PROPERTY_TYPES = {}


def registerField(field, title="", description="", **kwargs):
    _FIELDS[getattr(field, "__name__", str(field))] = field


def registerWidget(widget, title="", description="", **kwargs):
    _WIDGETS[getattr(widget, "__name__", str(widget))] = widget


def registerPropertyType(property, title="", description="", **kwargs):
    _PROPERTY_TYPES[property] = title


def getFieldByName(name):
    return _FIELDS.get(name)
