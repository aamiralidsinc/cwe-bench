class DisplayList(dict):
    def __init__(self, *args, **kwargs):
        super(DisplayList, self).__init__(*args, **kwargs)

    def add(self, key, value):
        self[key] = value


def listTypes():
    return []


def process_types(*args, **kwargs):
    return [], []
