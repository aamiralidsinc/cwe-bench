class MessageFactory(object):
    def __init__(self, domain):
        self.domain = domain

    def __call__(self, msg, **kw):
        return msg
