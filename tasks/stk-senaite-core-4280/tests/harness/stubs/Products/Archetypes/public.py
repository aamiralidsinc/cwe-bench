from Products.Archetypes.atapi import DisplayList  # noqa: F401
from Products.Archetypes.Field import (  # noqa: F401
    BooleanField, ComputedField, DateTimeField, Field, FileField, FloatField,
    ImageField, IntegerField, LinesField, ObjectField, ReferenceField,
    StringField, TextField,
)


class StringWidget(object):
    _properties = {"label": "", "description": "", "visible": True}

    def __init__(self, **kwargs):
        for key, value in self._properties.items():
            setattr(self, key, value)
        for key, value in kwargs.items():
            setattr(self, key, value)


class TextWidget(StringWidget):
    pass


class LabelWidget(StringWidget):
    pass


class RecordsWidget(StringWidget):
    pass


class ReferenceWidget(StringWidget):
    pass


class ComputedWidget(StringWidget):
    pass


class DateTimeWidget(StringWidget):
    pass


class BooleanWidget(StringWidget):
    pass
