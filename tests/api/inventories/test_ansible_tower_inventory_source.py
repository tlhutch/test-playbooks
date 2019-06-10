import pytest

from towerkit.config import config

from tests.api import APITest


@pytest.mark.api
@pytest.mark.usefixtures('authtoken', 'install_enterprise_license_unlimited')
class TestAnsibleTowerInventorySource(APITest):

    @pytest.fixture
    def remote_tower_hostname(self, is_docker):
        # Will use the tower under test to simulate a remote tower instance.
        # This assumes is that the hostname reachable by tests is reachable
        # by the task-system service running the inventory update, which is
        # always subject to revision
        return config.base_url

    @pytest.fixture
    def tower_cred(self, factories, admin_user, remote_tower_hostname):
        return factories.credential(kind='tower', username=admin_user.username,
                                       password=admin_user.password, host=remote_tower_hostname)

    def test_tower_inv_src_mirrors_target_inventory(self, factories, tower_cred):
        """Confirms that Tower inventory sources have same hosts, groups, and vars as mirrored remote inventory"""
        custom_inv_src = factories.inventory_source()
        custom_inv_src.update().wait_until_completed().assert_successful()

        custom_hosts = custom_inv_src.related.hosts.get().results

        custom_host_vars = {host.name: host.variables for host in custom_hosts}
        custom_host_to_id = {host.name: host.id for host in custom_hosts}

        for host in custom_hosts:  # Tower inventory source host variables have metadata
            custom_host_vars[host.name]['remote_tower_enabled'] = 'true'
            custom_host_vars[host.name]['remote_tower_id'] = custom_host_to_id[host.name]

        custom_group_vars = {group.name: group.variables for group in custom_inv_src.related.groups.get().results}

        tower_inv_src = factories.inventory_source(source='tower', credential=tower_cred,
                                                      instance_filters=custom_inv_src.ds.inventory.id)

        update = tower_inv_src.update().wait_until_completed()
        update.assert_successful()
        # Verify that default behavior is False when not giving verify_ssl input
        # https://github.com/ansible/tower/issues/2038
        assert update.job_env['TOWER_VERIFY_SSL'] == 'False'

        tower_hosts = tower_inv_src.related.hosts.get().results
        assert len(tower_hosts) == len(custom_hosts)

        tower_host_vars = {host.name: host.variables for host in tower_hosts}
        tower_group_vars = {group.name: group.variables for group in tower_inv_src.related.groups.get().results}

        assert tower_host_vars == custom_host_vars
        assert tower_group_vars == custom_group_vars

    @pytest.mark.mp_group('AnsibleTowerInventorySource', 'isolated_serial')
    def test_tower_inv_src_update_doesnt_affect_instance_count(self, v2, factories, tower_cred):
        custom_inv_src = factories.inventory_source()
        custom_inv_src.update().wait_until_completed().assert_successful()

        license_info = v2.config.get().license_info
        instance_count = license_info.instance_count
        free_instances = license_info.free_instances

        tower_inv_src = factories.inventory_source(source='tower', credential=tower_cred,
                                                      instance_filters=custom_inv_src.ds.inventory.id)

        update = tower_inv_src.update().wait_until_completed()
        update.assert_successful()

        updated_license_info = v2.config.get().license_info
        assert updated_license_info.instance_count == instance_count
        assert updated_license_info.free_instances == free_instances

    @pytest.mark.flaky(reruns=5, reruns_delay=1)
    def test_tower_inv_src_filter_by_inventory_name(self, factories, tower_cred):
        custom_inv_src = factories.inventory_source()
        custom_inv_src.update().wait_until_completed().assert_successful()

        inv_name = custom_inv_src.ds.inventory.get().related.named_url.split('/')[-2]
        tower_inv_src = factories.inventory_source(source='tower', credential=tower_cred,
                                                      instance_filters=inv_name)
        update = tower_inv_src.update().wait_until_completed()
        update.assert_successful()
        assert custom_inv_src.related.hosts.get().count == tower_inv_src.related.hosts.get().count

    def test_invalid_instance_filter_causes_failed_update(self, factories, tower_cred):
        tower_inv_source = factories.inventory_source(source='tower', credential=tower_cred,
                                                         instance_filters='NotATowerInventory')
        update = tower_inv_source.update().wait_until_completed()
        update.assert_status('failed')
        assert update.failed

    def test_user_credentials_without_inventory_access_cause_failed_update(self, factories, remote_tower_hostname):
        custom_inv_src = factories.inventory_source()
        custom_inv_src.update().wait_until_completed().assert_successful()

        unprivileged_user = factories.user()
        tower_cred = factories.credential(kind='tower', username=unprivileged_user.username,
                                             password=unprivileged_user.password, host=remote_tower_hostname)

        tower_inv_src = factories.inventory_source(source='tower', credential=tower_cred,
                                                      instance_filters=custom_inv_src.ds.inventory.id)
        update = tower_inv_src.update().wait_until_completed()
        update.assert_status('failed')
        assert update.failed
        assert "You do not have permission to perform this action." in update.result_stdout.replace('\n', ' ')
