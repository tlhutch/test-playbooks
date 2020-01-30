from awxkit.config import config
from awxkit import utils

import pytest
import os

from tests.api import APITest
from tests.collection import CUSTOM_VENVS, CUSTOM_VENVS_NAMES


k_v_config = f"host={config.base_url} username={config.credentials.users.admin.username} password={config.credentials.users.admin.password} verify_ssl=0\n"

ini_config = f"""[general]
host = {config.base_url}
username = {config.credentials.users.admin.username}
password = {config.credentials.users.admin.password}
verify_ssl = 0"""

yaml_config = f"""host: {config.base_url}
username: {config.credentials.users.admin.username}
password: {config.credentials.users.admin.password}
verify_ssl: 0"""

bad_config = """host: invalid
username: invalid
password: invalid
verify_ssl: 0"""

user_config = os.path.join(os.environ['HOME'], '.tower_cli.cfg')
local_config = os.path.join(os.environ['HOME'], 'local_tower_config.cfg')
global_config = '/etc/tower/tower_cli.cfg'


@pytest.fixture(scope='session')
def ini_config_oauth(session_oauth2_authtoken):
    return f"""[general]
host = {config.base_url}
oauth_token = {session_oauth2_authtoken}
verify_ssl = 0\n"""


@pytest.fixture(scope='session')
def yaml_config_oauth(session_oauth2_authtoken):
    return f"""host: {config.base_url}
oauth_token: {session_oauth2_authtoken}
verify_ssl: 0\n"""


@pytest.fixture(scope='session')
def k_v_config_oauth(session_oauth2_authtoken):
    return f"host={config.base_url} oauth_token={session_oauth2_authtoken} verify_ssl=0\n"


def write_config(ansible_adhoc, location, content, mode=None, owner=None):
    if not mode:
        mode = '600'
    if not owner:
        owner = os.environ['USER'],

    ansible_adhoc()['local'].copy(
        dest=location,
        mode=mode,
        owner=owner,
        content=content,
    )


def delete_file(ansible_adhoc, location):
    ansible_adhoc()['local'].file(
        dest=location,
        state='absent'
    )


def reset_environment_vars(tower_host=None, tower_username=None, tower_password=None, tower_verify_ssl=None):
    if tower_host:
        os.environ['TOWER_HOST'] = tower_host
    elif 'TOWER_HOST' in os.environ:
        del os.environ['TOWER_HOST']
    if tower_username:
        os.environ['TOWER_USERNAME'] = tower_username
    elif 'TOWER_USERNAME' in os.environ:
        del os.environ['TOWER_USERNAME']
    if tower_password:
        os.environ['TOWER_PASSWORD'] = tower_password
    elif 'TOWER_PASSWORD' in os.environ:
        del os.environ['TOWER_PASSWORD']
    if tower_verify_ssl:
        os.environ['TOWER_VERIFY_SSL'] = tower_verify_ssl
    elif 'TOWER_VERIFY_SSL' in os.environ:
        del os.environ['TOWER_VERIFY_SSL']


@pytest.fixture(scope='function')
def clear_config(request, ansible_adhoc, is_docker):
    # I feel uncomfortable deleting /etc/tower/tower_cli.cfg on people's
    # laptops, so instead of just doing it, lets ask them to do it
    if os.path.exists('/etc/tower/tower_cli.cfg') and is_docker:
        pytest.skip('/etc/tower/tower_cli.cfg exists, please delete it before running the collection config tests')
    delete_file(ansible_adhoc, user_config)
    delete_file(ansible_adhoc, global_config)

    # We dont want to use the environment variables accidentally
    old_tower_host = os.environ.get('TOWER_HOST', None)
    if old_tower_host:
        del os.environ['TOWER_HOST']
    old_tower_username = os.environ.get('TOWER_USERNAME', None)
    if old_tower_username:
        del os.environ['TOWER_USERNAME']
    old_tower_password = os.environ.get('TOWER_PASSWORD', None)
    if old_tower_password:
        del os.environ['TOWER_PASSWORD']
    old_tower_verify_ssl = os.environ.get('TOWER_VERIFY_SSL', None)
    if old_tower_verify_ssl:
        del os.environ['TOWER_VERIFY_SSL']

    request.addfinalizer(lambda *args: reset_environment_vars(old_tower_host,
        old_tower_username, old_tower_password, old_tower_verify_ssl))


@pytest.fixture(scope='function')
def local_config_yaml(request, ansible_adhoc, clear_config):
    write_config(ansible_adhoc, local_config, yaml_config)
    request.addfinalizer(lambda *args: delete_file(ansible_adhoc, local_config))


@pytest.fixture(scope='function')
def local_config_k_v(request, ansible_adhoc, clear_config):
    write_config(ansible_adhoc, local_config, k_v_config)
    request.addfinalizer(lambda *args: delete_file(ansible_adhoc, local_config))


@pytest.fixture(scope='function')
def local_config_yaml_oauth(request, ansible_adhoc, clear_config, yaml_config_oauth):
    write_config(ansible_adhoc, local_config, yaml_config_oauth)
    request.addfinalizer(lambda *args: delete_file(ansible_adhoc, local_config))


@pytest.fixture(scope='function')
def local_config_k_v_oauth(request, ansible_adhoc, clear_config, k_v_config_oauth):
    write_config(ansible_adhoc, local_config, k_v_config_oauth)
    request.addfinalizer(lambda *args: delete_file(ansible_adhoc, local_config))


@pytest.fixture(scope='function')
def user_config_yaml(request, ansible_adhoc, clear_config):
    write_config(ansible_adhoc, user_config, yaml_config)
    request.addfinalizer(lambda *args: delete_file(ansible_adhoc, user_config))


@pytest.fixture(scope='function')
def user_config_ini(request, ansible_adhoc, clear_config):
    write_config(ansible_adhoc, user_config, ini_config)
    request.addfinalizer(lambda *args: delete_file(ansible_adhoc, user_config))


@pytest.fixture(scope='function')
def user_config_yaml_oauth(request, ansible_adhoc, clear_config, yaml_config_oauth):
    write_config(ansible_adhoc, user_config, yaml_config_oauth)
    request.addfinalizer(lambda *args: delete_file(ansible_adhoc, user_config))


@pytest.fixture(scope='function')
def user_config_ini_oauth(request, ansible_adhoc, clear_config, ini_config_oauth):
    write_config(ansible_adhoc, user_config, ini_config_oauth)
    request.addfinalizer(lambda *args: delete_file(ansible_adhoc, user_config))


@pytest.fixture(scope='function')
def global_config_yaml(request, ansible_adhoc, skip_docker, clear_config):
    ansible_adhoc()['local'].file(
        dest='/etc/tower',
        mode='755',
        state='directory'
    )
    write_config(ansible_adhoc, global_config, ini_config, mode='644', owner=0)
    request.addfinalizer(lambda *args: delete_file(ansible_adhoc, global_config))


@pytest.fixture(scope='function')
def global_config_ini(request, ansible_adhoc, skip_docker, clear_config):
    ansible_adhoc()['local'].file(
        dest='/etc/tower',
        mode='755',
        state='directory'
    )
    write_config(ansible_adhoc, global_config, ini_config, mode='644', owner=0)
    request.addfinalizer(lambda *args: delete_file(ansible_adhoc, global_config))


@pytest.fixture(scope='function')
def global_config_yaml_oauth(request, ansible_adhoc, skip_docker, clear_config, yaml_config_oauth):
    ansible_adhoc()['local'].file(
        dest='/etc/tower',
        mode='755',
        state='directory'
    )
    write_config(ansible_adhoc, global_config, yaml_config_oauth, mode='644', owner=0)
    request.addfinalizer(lambda *args: delete_file(ansible_adhoc, global_config))


@pytest.fixture(scope='function')
def global_config_ini_oauth(request, ansible_adhoc, skip_docker, clear_config, ini_config_oauth):
    ansible_adhoc()['local'].file(
        dest='/etc/tower',
        mode='755',
        state='directory'
    )
    write_config(ansible_adhoc, global_config, ini_config_oauth, mode='644', owner=0)
    request.addfinalizer(lambda *args: delete_file(ansible_adhoc, global_config))


@pytest.mark.fixture_args(venvs=CUSTOM_VENVS, cluster=True, venv_group='local')
@pytest.mark.usefixtures('skip_if_pre_ansible29', 'skip_if_openshift', 'authtoken', 'skip_if_cluster', 'skip_if_wrong_python')
@pytest.mark.parametrize('python_venv', CUSTOM_VENVS, ids=CUSTOM_VENVS_NAMES)
class Test_Ansible_Tower_Collection_Config(APITest):
    def run_module(self, venv_path, ansible_adhoc, is_docker, request, module_name, module_args=None):
        if module_args is None:
            module_args = {}

        ansible_adhoc = ansible_adhoc()
        # If we're not in the docker deployment, we must change the hosts in
        # the venv_group to use the right virtualenv that has the dependencies
        # for awx collection
        fixture_args = request.node.get_closest_marker('fixture_args')
        venv_group = fixture_args.kwargs.get('venv_group')
        if not is_docker:
            for host in ansible_adhoc.options['inventory_manager'].groups[venv_group].hosts:
                host.vars['ansible_python_interpreter'] = venv_path + 'bin/python'

        module_output = getattr(ansible_adhoc[venv_group], module_name)(
                **module_args,
            )

        for hostname in ansible_adhoc.options['inventory_manager'].groups[venv_group].host_names:
            assert hasattr(module_output, 'contacted'), f'module execution failed: {module_output.__dict__}'
            assert hostname in module_output.contacted, f'module could not contact localhost: {module_output.__dict__}'
            if 'exception' in module_output.contacted[hostname]:
                pytest.fail(f'module threw an exception: {module_output.__dict__}')
            assert 'invocation' in module_output.contacted[hostname], f'module could not be invoked: {module_output.__dict__}'

        return module_output

    def check_module_output(self, request, ansible_adhoc, module_output, module_args=None, changed=None):
        if not module_args:
            module_args = {}

        ansible_adhoc = ansible_adhoc()
        fixture_args = request.node.get_closest_marker('fixture_args')
        venv_group = fixture_args.kwargs.get('venv_group')

        # Make sure there is at least 1 host we are checking
        assert ansible_adhoc.options['inventory_manager'].groups[venv_group].host_names

        for hostname in ansible_adhoc.options['inventory_manager'].groups[venv_group].host_names:
            assert 'module_args' in module_output.contacted[hostname]['invocation'], f'module arguments missing: {module_output.__dict__}'
            for (k, v) in module_args.items():
                assert k in module_output.contacted[hostname]['invocation']['module_args'], f'module argument missing: {k}, full module_output: {module_output.__dict__}'
                actual_value = module_output.contacted[hostname]['invocation']['module_args'][k]
                assert v == actual_value, f'module argument has wrong value on output, key: {k}, value: {v}, expected value: {actual_value}, full module_output: {module_output.__dict__}'
            if changed is not None:
                assert 'changed' in module_output.contacted[hostname], f'module_output has no changed attribute: {module_output.__dict__}'
                actual_changed = module_output.contacted[hostname]['changed']
                assert changed == actual_changed, f'module_output incorrect changed value, expected changed: {changed} actual state: {actual_changed}'

    def create_and_verify_organization(self, venv_path, request, v2, is_docker, ansible_adhoc, python_venv, collection_fqcn, module_args=None):
        if not module_args:
            org_name = utils.random_title()
            module_args = {
                'name': org_name,
                'description': 'hello world',
            }

        request.addfinalizer(lambda *args: v2.organizations.get(name=module_args['name']).results[0].delete())
        self.run_module(venv_path(python_venv['name']),
                ansible_adhoc, is_docker, request, collection_fqcn + '.tower_organization', module_args)

        org = v2.organizations.get(name=module_args['name']).results.pop()
        assert module_args['name'] == org['name']
        assert org['description'] == 'hello world'

    def test_ansible_tower_module_user_yaml_config(self, venv_path, request, v2, is_docker, ansible_adhoc, python_venv, collection_fqcn, user_config_yaml):
        self.create_and_verify_organization(venv_path, request, v2, is_docker, ansible_adhoc, python_venv, collection_fqcn)

    def test_ansible_tower_module_user_ini_config(self, venv_path, request, update_setting_pg, v2, is_docker, ansible_adhoc, python_venv, collection_fqcn, user_config_ini):
        self.create_and_verify_organization(venv_path, request, v2, is_docker, ansible_adhoc, python_venv, collection_fqcn)

    def test_ansible_tower_module_user_yaml_oauth_config(self, venv_path, request, v2, is_docker, ansible_adhoc, python_venv, collection_fqcn, user_config_yaml_oauth):
        self.create_and_verify_organization(venv_path, request, v2, is_docker, ansible_adhoc, python_venv, collection_fqcn)

    def test_ansible_tower_module_user_ini_oauth_config(self, venv_path, request, update_setting_pg, v2, is_docker, ansible_adhoc, python_venv, collection_fqcn, user_config_ini_oauth):
        self.create_and_verify_organization(venv_path, request, v2, is_docker, ansible_adhoc, python_venv, collection_fqcn)

    def test_ansible_tower_module_global_ini_config(self, venv_path, request, update_setting_pg, v2, is_docker, ansible_adhoc, python_venv, collection_fqcn, global_config_ini):
        self.create_and_verify_organization(venv_path, request, v2, is_docker, ansible_adhoc, python_venv, collection_fqcn)

    def test_ansible_tower_module_global_yaml_config(self, venv_path, request, update_setting_pg, v2, is_docker, ansible_adhoc, python_venv, collection_fqcn, global_config_yaml):
        self.create_and_verify_organization(venv_path, request, v2, is_docker, ansible_adhoc, python_venv, collection_fqcn)

    def test_ansible_tower_module_global_ini_oauth_config(self, venv_path, request, update_setting_pg, v2, is_docker, ansible_adhoc, python_venv, collection_fqcn, global_config_ini_oauth):
        self.create_and_verify_organization(venv_path, request, v2, is_docker, ansible_adhoc, python_venv, collection_fqcn)

    def test_ansible_tower_module_global_yaml_oauth_config(self, venv_path, request, update_setting_pg, v2, is_docker, ansible_adhoc, python_venv, collection_fqcn, global_config_yaml_oauth):
        self.create_and_verify_organization(venv_path, request, v2, is_docker, ansible_adhoc, python_venv, collection_fqcn)

    def test_ansible_tower_module_local_yaml_config(self, venv_path, request, update_setting_pg, v2, is_docker, ansible_adhoc, python_venv, collection_fqcn, local_config_yaml):
        org_name = utils.random_title()
        module_args = {
            'name': org_name,
            'description': 'hello world',
            'tower_config_file': local_config,
        }
        self.create_and_verify_organization(venv_path, request, v2, is_docker, ansible_adhoc, python_venv, collection_fqcn, module_args)

    def test_ansible_tower_module_local_k_v_config(self, venv_path, request, update_setting_pg, v2, is_docker, ansible_adhoc, python_venv, collection_fqcn, local_config_k_v):
        org_name = utils.random_title()
        module_args = {
            'name': org_name,
            'description': 'hello world',
            'tower_config_file': local_config,
        }
        self.create_and_verify_organization(venv_path, request, v2, is_docker, ansible_adhoc, python_venv, collection_fqcn, module_args)

    def test_ansible_tower_module_local_yaml_oauth_config(self, venv_path, request, update_setting_pg, v2, is_docker, ansible_adhoc, python_venv, collection_fqcn, local_config_yaml_oauth):
        org_name = utils.random_title()
        module_args = {
            'name': org_name,
            'description': 'hello world',
            'tower_config_file': local_config,
        }
        self.create_and_verify_organization(venv_path, request, v2, is_docker, ansible_adhoc, python_venv, collection_fqcn, module_args)

    def test_ansible_tower_module_local_k_v_oauth_config(self, venv_path, request, update_setting_pg, v2, is_docker, ansible_adhoc, python_venv, collection_fqcn, local_config_k_v_oauth):
        org_name = utils.random_title()
        module_args = {
            'name': org_name,
            'description': 'hello world',
            'tower_config_file': local_config,
        }
        self.create_and_verify_organization(venv_path, request, v2, is_docker, ansible_adhoc, python_venv, collection_fqcn, module_args)

    def test_ansible_tower_module_parameter_config(self, venv_path, request, update_setting_pg, v2, is_docker, ansible_adhoc, python_venv, collection_fqcn, clear_config):
        org_name = utils.random_title()
        module_args = {
            'name': org_name,
            'description': 'hello world',
            'tower_username': config.credentials.default.username,
            'tower_password': config.credentials.default.password,
            'tower_host': config.base_url,
            'validate_certs': False,
        }
        self.create_and_verify_organization(venv_path, request, v2, is_docker, ansible_adhoc, python_venv, collection_fqcn, module_args)

    def test_ansible_tower_module_config_heirarchy_params(self, venv_path, request, update_setting_pg, v2, is_docker, ansible_adhoc, python_venv, collection_fqcn, clear_config):
        org_name = utils.random_title()
        write_config(ansible_adhoc, user_config, bad_config)
        request.addfinalizer(lambda *args: delete_file(ansible_adhoc, user_config))

        old_tower_host = os.environ.get('TOWER_HOST', None)
        old_tower_username = os.environ.get('TOWER_USERNAME', None)
        old_tower_password = os.environ.get('TOWER_PASSWORD', None)
        old_tower_verify_ssl = os.environ.get('TOWER_VERIFY_SSL', None)

        os.environ['TOWER_HOST'] = 'badhost'
        os.environ['TOWER_USERNAME'] = 'badusername'
        os.environ['TOWER_PASSWORD'] = 'badpassword'

        module_args = {
            'name': org_name,
            'description': 'hello world',
            'tower_username': config.credentials.default.username,
            'tower_password': config.credentials.default.password,
            'tower_host': config.base_url,
            'validate_certs': False,
        }
        self.create_and_verify_organization(venv_path, request, v2, is_docker, ansible_adhoc, python_venv, collection_fqcn, module_args)

        # Reset our environment variable so we dont potentially step on other tests
        reset_environment_vars(old_tower_host, old_tower_username, old_tower_password, old_tower_verify_ssl)

    def test_ansible_tower_module_config_heirarchy_tower_config_file(self, venv_path, request, update_setting_pg, v2, is_docker, ansible_adhoc, python_venv, collection_fqcn, local_config_yaml):
        org_name = utils.random_title()
        write_config(ansible_adhoc, user_config, bad_config)
        request.addfinalizer(lambda *args: delete_file(ansible_adhoc, user_config))

        old_tower_host = os.environ.get('TOWER_HOST', None)
        old_tower_username = os.environ.get('TOWER_USERNAME', None)
        old_tower_password = os.environ.get('TOWER_PASSWORD', None)
        old_tower_verify_ssl = os.environ.get('TOWER_VERIFY_SSL', None)

        os.environ['TOWER_HOST'] = 'badhost'
        os.environ['TOWER_USERNAME'] = 'badusername'
        os.environ['TOWER_PASSWORD'] = 'badpassword'

        module_args = {
            'name': org_name,
            'description': 'hello world',
            'tower_config_file': local_config,
        }
        self.create_and_verify_organization(venv_path, request, v2, is_docker, ansible_adhoc, python_venv, collection_fqcn, module_args)

        # Reset our environment variable so we dont potentially step on other tests
        reset_environment_vars(old_tower_host, old_tower_username, old_tower_password, old_tower_verify_ssl)

    def test_ansible_tower_module_config_heirarchy_user(self, venv_path, request, update_setting_pg, v2, is_docker, ansible_adhoc, python_venv, collection_fqcn, skip_docker, user_config_yaml):
        org_name = utils.random_title()
        write_config(ansible_adhoc, global_config, bad_config)
        request.addfinalizer(lambda *args: delete_file(ansible_adhoc, global_config))

        module_args = {
            'name': org_name,
            'description': 'hello world',
        }
        self.create_and_verify_organization(venv_path, request, v2, is_docker, ansible_adhoc, python_venv, collection_fqcn, module_args)
