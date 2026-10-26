class Expression(object):
    def __init__(self, expression):
        self.text = expression

    def __call__(self, econtext):
        return True


def createExprContext(folder, portal, object):
    return {}
