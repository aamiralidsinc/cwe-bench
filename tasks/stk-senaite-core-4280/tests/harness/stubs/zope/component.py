def getAdapters(objects, interface, context=None):
    return []


def getUtility(*args, **kwargs):
    raise LookupError("no utility")


def queryUtility(*args, **kwargs):
    return None
