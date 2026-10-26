class ObjectInitializedEvent(object):
    def __init__(self, object):
        self.object = object


class ObjectEditedEvent(object):
    def __init__(self, object):
        self.object = object
