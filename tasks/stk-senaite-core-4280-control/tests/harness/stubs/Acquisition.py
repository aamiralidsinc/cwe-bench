def aq_parent(obj):
    return getattr(obj, "_parent", None)


def aq_inner(obj):
    return obj


def aq_base(obj):
    return obj


def aq_acquire(obj, name, default=None):
    return getattr(obj, name, default)
