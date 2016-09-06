import types

from utils import PseudoNamespace

config = PseudoNamespace()


def getvalue(self, name):
    return self.__getitem__(name)

# kludge to mimic pytest.config
config.getvalue = types.MethodType(getvalue, config)

config.api_version = config.get('api_version', 'v1')
config.assume_untrusted = config.get('assume_untrusted', True)

config.project_urls = dict(git='https://github.com/jlaska/ansible-playbooks.git',
                           hg='https://bitbucket.org/jlaska/ansible-helloworld')
