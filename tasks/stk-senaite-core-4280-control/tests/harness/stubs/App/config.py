class _Config(object):
    debug_mode = False


class _ConfigHolder(object):
    def getConfiguration(self):
        return _Config()


_config = _ConfigHolder()


def getConfiguration():
    return _Config()
