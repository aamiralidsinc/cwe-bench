class ValidationChain(object):
    def __init__(self, *args, **kwargs):
        self.args = args


class UnknowValidatorError(Exception):
    pass


class FalseValidatorError(Exception):
    pass
