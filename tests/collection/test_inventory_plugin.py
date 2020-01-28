from awxkit.config import config

import pytest
import json
import os

from tests.api import APITest
from tests.collection import CUSTOM_VENVS, CUSTOM_VENVS_NAMES


@pytest.mark.fixture_args(venvs=CUSTOM_VENVS, cluster=True, venv_group='local')
@pytest.mark.usefixtures('skip_if_pre_ansible29', 'skip_if_openshift', 'authtoken', 'skip_if_cluster', 'skip_if_wrong_python')
@pytest.mark.parametrize('python_venv', CUSTOM_VENVS, ids=CUSTOM_VENVS_NAMES)
class Test_Ansible_Tower_Inventory_Plugin(APITest):
    def replace_password(self, module_output):
        assert hasattr(module_output, 'contacted'), f'module execution failed: {module_output.__dict__}'
        for hostname in module_output.contacted.keys():
            assert 'cmd' in module_output.contacted[hostname], f'shell module did not return command run: {module_output.__dict__}'
            module_output.contacted[hostname]['cmd'] = module_output.contacted[hostname]['cmd'].replace(config.credentials.users.admin.password, "FILTERED")
            module_output.contacted[hostname]['stderr'] = module_output.contacted[hostname]['stderr'].replace(config.credentials.users.admin.password, "FILTERED")
            assert 'invocation' in module_output.contacted[hostname], f'shell module did not return command run: {module_output.__dict__}'
            assert 'module_args' in module_output.contacted[hostname]['invocation'], f'shell module did not return command run: {module_output.__dict__}'
            assert '_raw_params' in module_output.contacted[hostname]['invocation']['module_args'], f'shell module did not return command run: {module_output.__dict__}'
            module_output.contacted[hostname]['invocation']['module_args']['_raw_params'] = module_output.contacted[hostname]['invocation']['module_args']['_raw_params'].replace(config.credentials.users.admin.password, "FILTERED")

    def test_inventory_plugin(self, factories, venv_path, ansible_collections_path, request, v2, is_docker, ansible_adhoc, python_venv, collection_fqcn):
        fixture_args = request.node.get_closest_marker('fixture_args')
        venv_group = fixture_args.kwargs.get('venv_group')
        # if we're not in the docker deployment we need to specify using the
        # virtualenv ansible-inventory
        ansible_inv_path = "ansible-inventory"
        if not is_docker:
            virtual_env_path = venv_path(python_venv['name'])
            ansible_inv_path = os.path.join(virtual_env_path, "bin", "ansible-inventory")

        inv = factories.inventory()
        hosts = []
        hosts.append(factories.host(inventory=inv))
        hosts.append(factories.host(inventory=inv))
        hosts.append(factories.host(inventory=inv))
        ansible_adhoc = ansible_adhoc()[venv_group]
        # Change this awx.awx.tower to use ansible.tower.tower when we're
        # deploying the tower build of the collection in the future
        module_output = ansible_adhoc.shell(
            'ANSIBLE_INVENTORY_UNPARSED_FAILED=true '
            f'ANSIBLE_INVENTORY_ENABLED="{collection_fqcn}.tower" '
            f'TOWER_HOST={config.base_url} '
            f'TOWER_USERNAME={config.credentials.users.admin.username} '
            f'TOWER_PASSWORD=\'{config.credentials.users.admin.password}\' '
            'TOWER_VERIFY_SSL=0 '
            f'TOWER_INVENTORY={inv.id} '
            f'{ansible_inv_path} -i @tower_inventory --list'
        )

        self.replace_password(module_output)

        for hostname in ansible_adhoc.options['inventory_manager'].groups[venv_group].host_names:
            assert 'rc' in module_output.contacted[hostname], f'module is missing an "rc" value: {module_output.__dict__}'
            rc = module_output.contacted[hostname]['rc']
            assert rc == 0, f'ansible-inventory command failed with rc: {rc} module output: {module_output.contacted[hostname]["stderr"]}'
            assert 'invocation' in module_output.contacted[hostname], f'module could not be invoked: {module_output.__dict__}'
            assert 'stdout' in module_output.contacted[hostname], f'module stdout was not captured: {module_output.__dict__}'

            inventory_list = json.loads(module_output.contacted[hostname]['stdout'])
            for host in hosts:
                assert host.name in inventory_list['_meta']['hostvars']
                host_vars = inventory_list['_meta']['hostvars'][host.name]
                assert 'ansible_connection' in host_vars
                assert 'local' == host_vars['ansible_connection']
                assert 'ansible_host' in host_vars
                assert '127.0.0.1' == host_vars['ansible_host']
                assert 'remote_tower_enabled' in host_vars
                assert 'true' == host_vars['remote_tower_enabled']
                assert 'remote_tower_id' in host_vars
                assert host.id == host_vars['remote_tower_id']
