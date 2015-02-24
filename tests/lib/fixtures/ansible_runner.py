import pytest
import logging


log = logging.getLogger(__name__)


@pytest.fixture(scope='class')
def ansible_runner(ansible_module_cls):
    return ansible_module_cls


if False:
    @pytest.fixture(scope='class')
    def ansible_runner(request):
        '''
        Return initialized ansibleWrapper
        '''

        log.debug("Using ansible_runner")

        import pytest_ansible
        class AnsibleSingleHostRunner(pytest_ansible.AnsibleModule):
            def __run(self, *args, **kwargs):
                raise Exception("jlaska!")
                result = super(AnsibleSingleHostRunner, self).__run(*args, **kwargs)
                assert 'contacted' in result and len(result['contacted']) == 1
                return result['contacted'].values()[0]

        cls = pytest_ansible.initialize(request)
        cls.__class__ = AnsibleSingleHostRunner
        return cls
