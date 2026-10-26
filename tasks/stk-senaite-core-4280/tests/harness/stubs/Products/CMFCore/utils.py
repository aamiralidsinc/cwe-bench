def getToolByName(context, name, default=None):
    tool = getattr(context, name, None)
    if tool is None:
        return default
    return tool


def getToolInterface(name):
    return None
