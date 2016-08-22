import types

from utils import PseudoNamespace

config = PseudoNamespace()


def getvalue(self, name):
    return self.__getitem__(name)

# kludge to mimic pytest.config
config.getvalue = types.MethodType(getvalue, config)
