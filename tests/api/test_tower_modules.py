
from awxkit.config import config
from awxkit import utils

import pytest
import json
import os

from tests.api import APITest

TOWER_MODULES_PARAMS = [
    'common',
    'credential',
    'credential_type',
    'group',
    'host',
    'inventory',
    'inventory_source',
    'job_cancel',
    'job_launch',
    'job_list',
    'job_template',
    'job_wait',
    'label',
    'notification',
    'project',
    pytest.param('receive', marks=pytest.mark.serial),
    'role',
    'send',
    'settings',
    'team',
    'user',
    'workflow_template',
]


'''
Note: We include ansible + psutil in both environments so that the streams aren't crossed.
The streams get crossed when the ansible virtualenv contains a different version of python
than the version in the custom virtualenv. When a package is not found in the custom
virtualenv, the ansible virtualenv is the fallback virtualenv. This is problematic when
the python lib found doesn't support both versions of python.
'''
CUSTOM_VENVS = [
    {
        'name': 'python2_tower_modules',
        'packages': 'ansible-tower-cli psutil ansible',
        'python_interpreter': 'python2'
    },
    {
        'name': 'python3_tower_modules',
        'packages': 'ansible-tower-cli psutil ansible',
        'python_interpreter': 'python36'
    },
]


CUSTOM_VENVS_NAMES = [venv['name'] for venv in CUSTOM_VENVS]


@pytest.fixture(scope='module')
def os_python_version(session_ansible_python):
    """Return the Tower base OS Python version."""
    return session_ansible_python['version']['major']


@pytest.fixture(autouse=True)
def skip_if_wrong_python(request, os_python_version):
    """Skip when the venv python version does not match the OS base Python
    version.

    This is to avoid getting the test failed because Python 3 on RHEL7 doens't
    have libsexlinux-python available.
    """
    python_venv_name = request.getfixturevalue('python_venv_name')
    if not python_venv_name.startswith(f'python{os_python_version}'):
        pytest.skip(f'OS Python version is {os_python_version} but')


@pytest.fixture
def tower_credential(factories, admin_user):
    return factories.credential(kind='tower', username=admin_user.username,
                                password=admin_user.password, host=config.base_url)


@pytest.mark.fixture_args(venvs=CUSTOM_VENVS, cluster=True)
@pytest.mark.usefixtures('skip_if_openshift', 'authtoken', 'tower_modules_collection', 'shared_custom_venvs')
@pytest.mark.parametrize('python_venv_name', CUSTOM_VENVS_NAMES)
class Test_Ansible_Tower_Modules_via_Playbooks(APITest):
    @pytest.mark.parametrize('tower_module', TOWER_MODULES_PARAMS)
    def test_ansible_tower_module(self, v2, factories, tower_module, project, tower_credential, venv_path, python_venv_name):
        """
        Ansible modules that interact with Tower live in an Ansible Collection.
        Along side those modules live playbooks that test the modules in the
        collection.
        This test invokes those test that live along side the collection.
        """
        virtual_env_path = venv_path(python_venv_name)

        extra_vars = {
            'tower_module_under_test': tower_module,
            'ansible_python_interpreter': os.path.join(virtual_env_path, 'bin/python'),
        }
        jt = factories.job_template(project=project, playbook='tower_modules/wrapper.yml',
                                    extra_vars=json.dumps(extra_vars), verbosity=5)
        jt.add_credential(tower_credential)
        jt.custom_virtualenv = virtual_env_path
        job = jt.launch().wait_until_completed()

        job.assert_successful()


@pytest.mark.fixture_args(venvs=CUSTOM_VENVS, cluster=True)
@pytest.mark.usefixtures('skip_if_openshift', 'authtoken', 'tower_modules_collection', 'shared_custom_venvs')
@pytest.mark.parametrize('python_venv_name', CUSTOM_VENVS_NAMES)
class Test_Ansible_Tower_Modules(APITest):
    def test_ansible_tower_module_organization_create(self, request, v2, factories, project, tower_credential, venv_path, python_venv_name):
        org_name = utils.random_title()
        virtual_env_path = venv_path(python_venv_name)

        extra_vars = {
            'module_name': 'tower_organization',
            'module_args': {
                'name': org_name,
                'description': 'hello world',
            },
            'ansible_python_interpreter': os.path.join(virtual_env_path, 'bin/python'),
        }
        request.addfinalizer(lambda *args: v2.organizations.get(name=org_name).results[0].delete())

        jt = factories.job_template(playbook='invoke_x.yml', extra_vars=json.dumps(extra_vars),
                                    credential=tower_credential, project=project, verbosity=5)
        jt.custom_virtualenv = virtual_env_path
        job = jt.launch()
        job.wait_until_completed()
        job.assert_successful()

        org = v2.organizations.get(name=org_name).results[0]
        assert org_name == org['name']
        assert extra_vars['module_args']['description'] == org['description']

    def test_ansible_tower_module_organization_delete(self, request, v2, factories, project, tower_credential, venv_path, python_venv_name):
        org = factories.organization()
        virtual_env_path = venv_path(python_venv_name)

        extra_vars = {
            'module_name': 'tower_organization',
            'module_args': {
                'name': org.name,
                'state': 'absent',
            },
            'ansible_python_interpreter': os.path.join(virtual_env_path, 'bin/python'),
        }

        jt = factories.job_template(playbook='invoke_x.yml', extra_vars=json.dumps(extra_vars),
                                    credential=tower_credential, project=project, verbosity=5)
        jt.custom_virtualenv = virtual_env_path
        job = jt.launch()
        job.wait_until_completed()
        job.assert_successful()

        assert 0 == len(v2.organizations.get(name=org.name).results)

    def test_ansible_tower_module_organization_check_mode(self, request, v2, factories, project, tower_credential, tower_version, venv_path, python_venv_name):
        '''
        Ensure that orgnization check_mode: True returns the tower_version
        '''
        org = factories.organization()
        virtual_env_path = venv_path(python_venv_name)

        extra_vars = {
            'module_name': 'tower_organization',
            'module_args': {
                'name': org.name,
            },
            'check_mode': True,
            'ansible_python_interpreter': os.path.join(virtual_env_path, 'bin/python'),
        }

        jt = factories.job_template(playbook='invoke_x.yml', extra_vars=json.dumps(extra_vars),
                                    credential=tower_credential, project=project, verbosity=5)
        jt.custom_virtualenv = virtual_env_path
        job = jt.launch()
        job.wait_until_completed()
        job.assert_successful()

        job_event = job.get_related('job_events').get(event='runner_on_ok', task='invoke_arbitrary_module').results[0]
        module_tower_version = job_event['event_data']['res']['tower_version']

        assert tower_version == module_tower_version
