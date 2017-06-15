from towerkit import exceptions as exc
import fauxfactory
import pytest

from tests.api import Base_Api_Test


@pytest.mark.api
@pytest.mark.ha_tower
@pytest.mark.skip_selenium
@pytest.mark.destructive
class Test_Inventory(Base_Api_Test):

    pytestmark = pytest.mark.usefixtures('authtoken', 'install_enterprise_license_unlimited')

    def test_inventory_names(self, factories):
        """Test that we can have inventories with the same name in different organizations."""
        name = fauxfactory.gen_alphanumeric()
        factories.inventory(name=name)
        factories.inventory(name=name)

    def test_host_update(self, factories):
        """Smart inventory hosts should reflect host changes."""
        host = factories.host()
        inventory = factories.v2_inventory(kind='smart', host_filter="name={0}".format(host.name))
        hosts = inventory.related.hosts.get()

        host.description = fauxfactory.gen_utf8()
        assert hosts.get().results.pop().description == host.description

        host.delete()
        assert hosts.get().count == 0

    def test_host_without_group(self, host_without_group):
        """Verify that inventories/N/script includes hosts that are not a member of any group.
        * Create inventory with host and no groups
        * Verify host appears in related->hosts
        * Verify host appears in related->script
        """
        inventory = host_without_group.get_related('inventory')
        assert inventory.get_related('groups').count == 0
        assert inventory.get_related('root_groups').count == 0

        hosts = inventory.get_related('hosts')
        assert hosts.count == 1

        script = inventory.get_related('script')
        script_hosts_count = len(script.json['all']['hosts'])
        assert hosts.count == script_hosts_count

    def test_conflict_exception_with_running_update(self, factories):
        """Verify that deleting an inventory with a running update will raise a 409
        exception.
        """
        inv_source = factories.v2_inventory_source()
        inv_update = inv_source.update()

        with pytest.raises(exc.Conflict) as e:
            inv_source.ds.inventory.delete()
        assert e.value.message['conflict'] == 'Resource is being used by running jobs'
        assert e.value.message['active_jobs'] == [{'type': 'inventory_update', 'id': inv_update.id}]

        # ensure clean test teardown
        inv_update.wait_until_completed()

    def test_v1_update_cascade_delete(self, custom_inventory_source):
        """Verify that v1 inventory updates get cascade deleted with their custom group."""
        inv_update1, inv_update2 = [custom_inventory_source.update().wait_until_completed() for _ in range(2)]

        custom_inventory_source.get_related('group').delete()
        with pytest.raises(exc.NotFound):
            inv_update1.get()
        with pytest.raises(exc.NotFound):
            inv_update2.get()

    def test_v2_update_cascade_delete(self, factories):
        """Verify that v2 inventory updates get cascade deleted with their inventory source."""
        inv_source = factories.v2_inventory_source()
        inv_update1, inv_update2 = [inv_source.update().wait_until_completed() for _ in range(2)]

        inv_source.delete()
        with pytest.raises(exc.NotFound):
            inv_update1.get()
        with pytest.raises(exc.NotFound):
            inv_update2.get()

    def test_resource_cascade_delete(self, factories, v2):
        """Verify that inventory resources get cascade deleted with their inventory."""
        inventory = factories.v2_inventory()
        parent_group, child_group = [factories.v2_group(inventory=inventory) for i in range(2)]
        parent_group.add_group(child_group)
        isolated_host, group_host = [factories.v2_host(inventory=inventory) for i in range(2)]
        parent_group.add_host(group_host)
        inv_source = factories.v2_inventory_source(inventory=inventory)

        inventory.delete()
        for resource in [inventory, parent_group, child_group, group_host, isolated_host, inv_source]:
            with pytest.raises(exc.NotFound):
                resource.get()
