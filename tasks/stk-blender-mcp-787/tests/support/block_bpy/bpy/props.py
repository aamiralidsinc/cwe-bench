"""Property constructors used by the add-on's class annotations."""


class _Prop:
    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs


def IntProperty(*args, **kwargs):
    return _Prop(*args, **kwargs)


def BoolProperty(*args, **kwargs):
    return _Prop(*args, **kwargs)


def StringProperty(*args, **kwargs):
    return _Prop(*args, **kwargs)


def EnumProperty(*args, **kwargs):
    return _Prop(*args, **kwargs)


def FloatProperty(*args, **kwargs):
    return _Prop(*args, **kwargs)
