class RichTextValue(object):
    def __init__(self, raw=""):
        self.raw = raw

    @property
    def output(self):
        return self.raw
