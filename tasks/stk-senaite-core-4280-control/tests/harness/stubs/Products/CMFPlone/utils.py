def safe_unicode(value, encoding="utf-8"):
    if value is None:
        return None
    if isinstance(value, unicode):  # noqa: F821  (python 2)
        return value
    if isinstance(value, str):
        return value.decode(encoding, "replace")
    return value


def base_hasattr(obj, name):
    return hasattr(obj, name)


def _createObjectByType(type_name, container, id):
    return container._create(type_name, id)
