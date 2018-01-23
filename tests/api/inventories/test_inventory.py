from towerkit import exceptions as exc
import fauxfactory
import pytest

from tests.api import Base_Api_Test


@pytest.mark.api
@pytest.mark.destructive
@pytest.mark.usefixtures('authtoken', 'install_enterprise_license_unlimited')
class TestInventory(Base_Api_Test):

    def test_inventory_names(self, factories):
        """Test that we can have inventories with the same name in different organizations."""
        name = fauxfactory.gen_alphanumeric()
        factories.inventory(name=name)
        factories.inventory(name=name)

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
        script_hosts_count = len(script.all.hosts)
        assert hosts.count == script_hosts_count

    def test_host_related_groups(self, factories):
        """Verifies the hosts/N/groups related field."""
        inventory = factories.v2_inventory()
        parent_group, child_group = [factories.v2_group(inventory=inventory) for _ in range(2)]
        parent_group.add_group(child_group)

        isolated_host, parent_host, duplicate_host = [factories.v2_host(inventory=inventory) for _ in range(3)]
        parent_group.add_host(parent_host)
        for group in [parent_group, child_group]:
            group.add_host(duplicate_host)

        assert set([parent_group.id]) == set([group.id for group in parent_host.related.groups.get().results])
        assert set([parent_group.id, child_group.id]) == set([group.id for group in duplicate_host.related.groups.get().results])
        assert isolated_host.related.groups.get().count == 0

    def test_host_summary_field_groups(self, factories):
        """Verifies the host details groups summary field.
        * Should only show five results.
        * Results should be from parent groups only.
        """
        inventory = factories.v2_inventory()
        host = factories.v2_host(inventory=inventory)

        groups = [factories.v2_group(inventory=inventory) for i in range(6)]
        for group in groups:
            group.add_host(host)
        parent_group = factories.v2_group(inventory=inventory)
        parent_group.add_group(groups[0])

        sf_groups = host.get().summary_fields.groups
        assert sf_groups.count == 6
        assert len(sf_groups.results) == 5

        all_results = []
        for group in groups:
            result = {'id': group.id, 'name': group.name}
            assert result not in all_results
            all_results.append(result)

    def test_jobs_run_on_enabled_hosts_only(self, factories):
        inventory = factories.v2_inventory()
        enabled_host, disabled_host = [factories.v2_host(inventory=inventory, enabled=enabled) for enabled in (True, False)]
        jt = factories.v2_job_template(inventory=inventory)

        job = jt.launch().wait_until_completed()
        assert job.is_successful

        jhs = job.related.job_host_summaries.get()
        assert jhs.count == 1
        assert jhs.results.pop().host == enabled_host.id

    def test_jobs_not_run_on_disabled_hosts(self, factories):
        inventory = factories.v2_inventory()
        for _ in range(3):
            factories.v2_host(inventory=inventory, enabled=False)
        jt = factories.v2_job_template(inventory=inventory)

        job = jt.launch().wait_until_completed()
        assert job.is_successful

        assert job.related.job_host_summaries.get().count == 0

    def test_inventory_reflects_dependent_resources_and_active_failures(self, factories):
        inv = factories.v2_inventory()
        group = factories.v2_group(inventory=inv)
        group.add_host(factories.v2_host(inventory=inv))
        inv_source = factories.v2_inventory_source(inventory=inv, source='ec2')

        inv_source.update().wait_until_completed()
        jt = factories.v2_job_template(inventory=inv, playbook='fail_unless.yml')
        assert jt.launch().wait_until_completed().status == 'failed'

        assert inv.get().total_hosts == 1
        assert inv.total_groups == 1
        assert inv.total_inventory_sources == 1
        assert inv.has_inventory_sources

        assert inv.hosts_with_active_failures == 1
        assert inv.groups_with_active_failures == 1
        assert inv.inventory_sources_with_failures == 1
        assert inv.has_active_failures

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

    def test_resource_cascade_delete(self, factories):
        """Verify that inventory resources get cascade deleted with their inventory."""
        inventory = factories.v2_inventory()
        parent_group, child_group = [factories.v2_group(inventory=inventory) for _ in range(2)]
        parent_group.add_group(child_group)
        isolated_host, group_host = [factories.v2_host(inventory=inventory) for _ in range(2)]
        parent_group.add_host(group_host)
        inv_source = factories.v2_inventory_source(inventory=inventory)

        inventory.delete().wait_until_deleted()
        for resource in [inventory, parent_group, child_group, group_host, isolated_host, inv_source]:
            with pytest.raises(exc.NotFound):
                resource.get()

    def test_duplicate_inventories_disallowed_by_organization(self, factories):
        inv = factories.v2_inventory()

        with pytest.raises(exc.BadRequest) as e:
            factories.v2_inventory(name=inv.name, organization=inv.ds.organization)
        assert e.value[1]['__all__'] == ['Inventory with this Name and Organization already exists.']

    def test_confirm_inventory_not_in_host_put_options(self, v2, factories):
        assert 'inventory' not in factories.v2_host().options().actions.PUT
