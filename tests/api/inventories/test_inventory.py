import towerkit.tower.inventory
import towerkit.exceptions
import towerkit.utils
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
        org1 = factories.organization()
        org2 = factories.organization()

        factories.inventory(name="test-org", organization=org1)
        factories.inventory(name="test-org", organization=org2)

    def test_host_update(self, factories):
        """Smart inventory hosts should reflect host changes."""
        host = factories.host()
        inventory = factories.v2_inventory(kind='smart', host_filter="name={0}".format(host.name))
        hosts = inventory.related.hosts.get()

        host.description = fauxfactory.gen_utf8()
        assert hosts.get().results.pop().description == host.description

        host.delete()
        assert hosts.get().count == 0

    def test_host_without_group(self, host_without_group, tower_version_cmp):
        """Verify that /inventory/N/script includes hosts that are not a member of
        any group.
            1) Create inventory with hosts, but no groups
            2) Verify the hosts appear in related->hosts
            2) Verify the hosts appear in related->script
        """
        if tower_version_cmp('2.0.0') < 0:
            pytest.xfail("Only supported on tower-2.0.0 (or newer)")

        inventory_pg = host_without_group.get_related('inventory')

        # Verify /groups is empty
        assert inventory_pg.get_related('groups').count == 0, \
            "Inventory unexpectedly has groups (%s)" % inventory_pg.get_related('groups').count
        # Verify /root_groups is empty
        assert inventory_pg.get_related('root_groups').count == 0, \
            "Inventory unexpectedly has root_groups (%s)" % inventory_pg.get_related('root_groups').count

        all_hosts = inventory_pg.get_related('hosts')
        assert all_hosts.count == 1

        script = inventory_pg.get_related('script').json
        script_all_hosts = len(script['all']['hosts'])

        assert all_hosts.count == script_all_hosts, \
            "The number of inventory hosts differs between endpoints " \
            "/hosts (%s) and /script (%s)" % (all_hosts.count, script_all_hosts)

    def test_conflict_exception_with_running_update(self, custom_inventory_source):
        """Verify that deleting an inventory with a running update will
        raise a 409 exception
        """
        inventory_pg = custom_inventory_source.get_related("inventory")
        custom_inventory_source.get_related("update").post()
        update_pg = custom_inventory_source.get().get_related("current_update")

        # delete the job_template
        exc_info = pytest.raises(towerkit.exceptions.Conflict, inventory_pg.delete)
        result = exc_info.value[1]
        assert result == {'conflict': 'Resource is being used by running jobs', 'active_jobs': [{'type': '%s' % update_pg.type, 'id': update_pg.id}]}

    def test_update_cascade_delete(self, custom_inventory_source, api_inventory_updates_pg):
        """Verify that associated inventory updates get cascade deleted with custom group
        deletion.
        """
        inv_source_id = custom_inventory_source.id
        custom_inventory_source.update().wait_until_completed()

        # assert that we have an inventory update
        assert api_inventory_updates_pg.get(inventory_source=inv_source_id).count == 1, \
            "Unexpected number of inventory updates. Expected one update."

        # delete custom group and assert that inventory updates deleted
        custom_inventory_source.get_related('group').delete()
        assert api_inventory_updates_pg.get(inventory_source=inv_source_id).count == 0, \
            "Unexpected number of inventory updates after deleting custom group. Expected zero updates."

    def test_child_cascade_delete(self, inventory, host_local, host_without_group, group, api_groups_pg, api_hosts_pg):
        """Verify DELETE removes associated groups and hosts"""
        # Verify inventory group/host counts
        assert inventory.get_related('groups').count == 1
        assert inventory.get_related('hosts').count == 2

        # Delete the inventory
        inventory.delete()

        # Related resources should be forbidden
        with pytest.raises(towerkit.exceptions.NotFound):
            inventory.get_related('groups')

        # Using main endpoint, find any matching groups
        groups_pg = api_groups_pg.get(inventory=inventory.id)

        # Assert no matching groups found
        assert groups_pg.count == 0, "ERROR: not All inventory groups were deleted"

        # Related resources should be forbidden
        with pytest.raises(towerkit.exceptions.NotFound):
            inventory.get_related('hosts')

        # Using main endpoint, find any matching hosts
        hosts_pg = api_hosts_pg.get(inventory=inventory.id)

        # Assert no matching hosts found
        assert hosts_pg.count == 0, "ERROR: not all inventory hosts were deleted"
