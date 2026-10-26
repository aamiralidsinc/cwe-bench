_TOKEN = "deadbeefcafe1234"


class AuthenticatorView(object):
    def __init__(self, context, request=None):
        self.context = context
        self.request = request

    def authenticator(self):
        return '<input type="hidden" name="_authenticator" value="%s" />' % _TOKEN


def createToken():
    return _TOKEN


def check(request):
    return True
