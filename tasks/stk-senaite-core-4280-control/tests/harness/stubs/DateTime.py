class DateTime(object):
    def __init__(self, value=None):
        self._value = value

    def ISO(self):
        return "2000-01-01T00:00:00Z"

    def __str__(self):
        return "2000-01-01 00:00:00"
