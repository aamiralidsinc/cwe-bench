"""Minimal transaction stub: savepoints do not roll back the harness state."""


class Savepoint(object):
    def rollback(self):
        return None


def savepoint(optimistic=False):
    return Savepoint()


def commit():
    return None


def abort():
    return None


def get():
    return None


def begin():
    return None
