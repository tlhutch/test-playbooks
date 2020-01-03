from awxkit import exceptions as exc, utils
import fauxfactory
import pytest
import six
import time
import logging

from tests.api import APITest


log = logging.getLogger(__name__)


@pytest.mark.usefixtures('authtoken')
class TestInventory(APITest):

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
        inventory = factories.inventory()
        parent_group, child_group = [factories.group(inventory=inventory) for _ in range(2)]
        parent_group.add_group(child_group)

        isolated_host, parent_host, duplicate_host = [factories.host(inventory=inventory) for _ in range(3)]
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
        inventory = factories.inventory()
        host = factories.host(inventory=inventory)

        groups = [factories.group(inventory=inventory) for i in range(6)]
        for group in groups:
            group.add_host(host)
        parent_group = factories.group(inventory=inventory)
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
        inventory = factories.inventory()
        enabled_host, disabled_host = [factories.host(inventory=inventory, enabled=enabled) for enabled in (True, False)]
        jt = factories.job_template(inventory=inventory)

        job = jt.launch().wait_until_completed()
        job.assert_successful()

        jhs = job.related.job_host_summaries.get()
        assert jhs.count == 1
        assert jhs.results.pop().host == enabled_host.id

    def test_jobs_not_run_on_disabled_hosts(self, factories):
        inventory = factories.inventory()
        for _ in range(3):
            factories.host(inventory=inventory, enabled=False)
        jt = factories.job_template(inventory=inventory)

        job = jt.launch().wait_until_completed()
        job.assert_successful()

        assert job.related.job_host_summaries.get().count == 0

    def test_inventory_reflects_dependent_resources_and_active_failures(self, factories):
        inv = factories.inventory()
        group = factories.group(inventory=inv)
        group.add_host(factories.host(inventory=inv))
        inv_source = factories.inventory_source(inventory=inv, source='ec2')

        inv_source.update().wait_until_completed()
        jt = factories.job_template(inventory=inv, playbook='fail_unless.yml')
        assert jt.launch().wait_until_completed().status == 'failed'

        assert inv.get().total_hosts == 1
        assert inv.total_groups == 1
        assert inv.total_inventory_sources == 1
        assert inv.has_inventory_sources

        assert inv.hosts_with_active_failures == 1
        assert inv.inventory_sources_with_failures == 1
        assert inv.has_active_failures

    def test_update_cascade_delete(self, factories):
        """Verify that v2 inventory updates get cascade deleted with their inventory source."""
        inv_source = factories.inventory_source()
        inv_update1, inv_update2 = [inv_source.update().wait_until_completed() for _ in range(2)]

        inv_source.delete()
        with pytest.raises(exc.NotFound):
            inv_update1.get()
        with pytest.raises(exc.NotFound):
            inv_update2.get()

    def test_resource_cascade_delete(self, factories):
        """Verify that inventory resources get cascade deleted with their inventory."""
        inventory = factories.inventory()
        parent_group, child_group = [factories.group(inventory=inventory) for _ in range(2)]
        parent_group.add_group(child_group)
        isolated_host, group_host = [factories.host(inventory=inventory) for _ in range(2)]
        parent_group.add_host(group_host)
        inv_source = factories.inventory_source(inventory=inventory)

        inventory.delete().wait_until_deleted()
        for resource in [inventory, parent_group, child_group, group_host, isolated_host, inv_source]:
            with pytest.raises(exc.NotFound):
                resource.get()

    def test_duplicate_inventories_disallowed_by_organization(self, factories):
        inv = factories.inventory()

        with pytest.raises(exc.Duplicate) as e:
            factories.inventory(name=inv.name, organization=inv.ds.organization)
        assert e.value[1]['__all__'] == ['Inventory with this Name and Organization already exists.']

    def test_confirm_inventory_not_in_host_put_options(self, v2, factories):
        assert 'inventory' not in factories.host().options().actions.PUT

    def test_confirm_computed_fields_tasks_dont_overwhelm_system(self, factories):
        """Verify that numerous individual inventory modifications don't affect system's ability to run jobs"""
        jt = factories.job_template()
        invs = [factories.inventory() for _ in range(10)]
        hosts = {inv: [inv.add_host() for _ in range(20)] for inv in invs}
        groups = [factories.group(inventory=inv) for inv in invs]
        for group in groups:
            for host in hosts[group.ds.inventory]:
                group.add_host(host)
        for inv in invs:
            for host in hosts[inv]:
                host.delete()

        def noop(*a, **kw):
            pass

        for group in groups:
            group.silent_delete = noop  # prevent redundant deletion requests.
            group.delete()
        for inv in invs:
            inv.silent_delete = noop
            inv.delete()
        jt.launch().wait_until_completed().assert_successful()

    @pytest.fixture
    def host_script(self):
        """Given N, this produces text which can be used in an inventory script
        that prints JSON output that defines an inventory with N hosts
        """
        def give_me_text(hosts=0, groups=0):
            return '\n'.join([
                "#!/usr/bin/env python",
                "import json",
                "data = {'_meta': {'hostvars': {}}}",
                "for i in range({}):".format(hosts),
                "   data.setdefault('ungrouped', []).append('Host-{}'.format(i))",
                "for i in range({}):".format(groups),
                "   data['Group-{}'.format(i)] = {'vars': {'foo': 'bar'}}",
                "print(json.dumps(data, indent=2))"
            ])
        return give_me_text

    def test_confirm_large_inventory_copies_dont_overwhelm_system(self, factories, host_script):
        """Verify that copying an inventory with many hosts doesn't affect system's ability to run jobs"""
        total = 5000
        jt = factories.job_template()
        inv_script = factories.inventory_script(script=host_script(total))
        inv_source = factories.inventory_source(source_script=inv_script)
        assert inv_source.source_script == inv_script.id
        inv = inv_source.ds.inventory
        inv.update_inventory_sources(wait=True)

        copied = inv.get_related('copy').post({'name': six.text_type('{} (Copied)').format(inv.name)})
        jt.launch().wait_until_completed().assert_successful()

        utils.poll_until(lambda: copied.get_related('hosts').count == total, interval=10, timeout=60 * 5)

    def test_large_import_activity_stream(self, v2, factories, host_script):
        total = 25
        inv_script = factories.inventory_script(script=host_script(hosts=total, groups=total))
        inv_source = factories.inventory_source(source_script=inv_script)
        assert inv_source.source_script == inv_script.id
        inv = inv_source.ds.inventory
        search_kernel = inv.name[:-3]  # work around https://github.com/ansible/awx/issues/2570
        start = time.time()
        inv.update_inventory_sources(wait=True)
        creation_entry_ct = v2.activity_stream.get(changes__icontains=search_kernel).count
        log.warning('Inventory import of {} hosts took {}, producing {} entries.'.format(
            total, time.time() - start, creation_entry_ct
        ))

        start = time.time()
        inv.delete()
        utils.poll_until(lambda: v2.inventory.get(name__icontains=search_kernel).count == 0, interval=1, timeout=60 * 5)
        deletion_entries = v2.activity_stream.get(changes__icontains=search_kernel, operation='delete')
        log.warning('Deletion of inventory took roughly {}, producing {} entries.'.format(
            time.time() - start, deletion_entries.count
        ))
        for entry in deletion_entries.results:
            if entry.object1 == 'inventory':
                inventory_entry = entry
                break
        else:
            raise Exception('Could not find inventory entry out of:\n{}'.format(deletion_entries.results[:2]))
        assert inventory_entry.changes['coalesced_data']['hosts_deleted'] == total
        assert inventory_entry.changes['coalesced_data']['groups_deleted'] == total
        assert deletion_entries.count == 2  # one for inventory delete, one for inventory source
