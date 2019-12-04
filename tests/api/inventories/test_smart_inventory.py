from awxkit import exceptions as exc
from awxkit.utils import poll_until, logged_sleep
import fauxfactory
import pytest

from tests.api import APITest


@pytest.mark.usefixtures('authtoken')
class TestSmartInventory(APITest):

    def test_host_sourced_by_ansible_facts(self, factories):
        host = factories.host()
        jt = factories.job_template(inventory=host.ds.inventory, playbook='gather_facts.yml', use_fact_cache=True)
        assert jt.launch().wait_until_completed()

        facts = host.related.ansible_facts.get()
        inv = factories.inventory(organization=host.ds.inventory.ds.organization, kind='smart',
                                  host_filter=('ansible_facts__ansible_distribution={0} and'
                                               'ansible_facts__ansible_distribution_version="{1}"')
                                  .format(facts.ansible_distribution, facts.ansible_distribution_version))

        hosts = inv.related.hosts.get()
        assert hosts.count == 1
        assert hosts.results.pop().id == host.id

    def test_host_updates_for_edit_and_deletion(self, factories):
        host = factories.host()
        inventory = factories.inventory(organization=host.ds.inventory.ds.organization, kind='smart',
                                        host_filter="name={0}".format(host.name))
        hosts = inventory.related.hosts.get()
        assert hosts.count == 1

        host.description = fauxfactory.gen_utf8()
        assert hosts.get().results.pop().description == host.description

        host.delete()
        assert hosts.get().count == 0

    def test_host_filter_is_organization_scoped(self, factories):
        host1, host2 = [factories.host(name="test_host_{0}".format(i)) for i in range(2)]
        inventory = factories.inventory(organization=host1.ds.inventory.ds.organization, kind='smart',
                                        host_filter='search=test_host')

        hosts = inventory.related.hosts.get()
        assert hosts.count == 1
        assert hosts.results.pop().id == host1.id

    def test_smart_inventory_reflects_dependent_resources(self, factories):
        host = factories.host()
        inv = factories.inventory(organization=host.ds.inventory.ds.organization, kind='smart',
                                  host_filter='name={0}'.format(host.name))

        assert inv.total_hosts == 1
        assert inv.total_groups == 0
        assert inv.total_inventory_sources == 0
        assert not inv.has_inventory_sources

        jt = factories.job_template(inventory=inv, playbook='fail_unless.yml')
        assert jt.launch().wait_until_completed().status == 'failed'

        assert inv.get().hosts_with_active_failures == 1
        assert inv.groups_with_active_failures == 0
        assert inv.inventory_sources_with_failures == 0
        assert inv.has_active_failures

    @pytest.mark.serial
    def test_consumed_capacity_for_hosts_with_smart_inventory(self, v2, factories, organization):
        """
        Test that the consumed capacity for the instance group is calculated accurately for
        a JT that has forks and uses smart inventory
        issue: https://github.com/ansible/tower/issues/3734
        """
        # Create a smart inventory that uses an instance group
        ig = factories.instance_group()
        instance = v2.instances.get().results.pop()
        ig.add_instance(instance)
        iv = factories.inventory(organization=organization)
        iv.add_instance_group(ig)
        capacity = instance.capacity
        forks = min(50, capacity // 2)
        # create hosts that will be added in the smart inventory
        for n in range(capacity):
            factories.host(name='test_host_' + str(n), inventory=iv)
        smart_iv = factories.inventory(organization=organization, kind='smart', host_filter="search=test_host_")
        smart_iv.add_instance_group(ig)
        # create a job template with the smart inventory and instance group
        jt = factories.job_template(inventory=smart_iv, forks=forks, playbook='sleep.yml')
        jt.add_instance_group(ig)
        expected_percent_capacity_remaining = ((capacity - forks) / capacity) * 100
        expected_percent_capacity_remaining_range = range(int(expected_percent_capacity_remaining - 10),
                                                          int(expected_percent_capacity_remaining + 10))
        jt.launch().wait_until_status('running')
        # Launching the job shows the correct consumed capacity percent in the instance group/instance
        assert int(ig.get().percent_capacity_remaining) in expected_percent_capacity_remaining_range

    def test_unable_to_create_host(self, factories):
        inventory = factories.inventory(host_filter='name=localhost', kind='smart')
        with pytest.raises(exc.BadRequest) as e:
            factories.host(inventory=inventory)
        assert e.value[1]['inventory'] == {'detail': 'Cannot create Host for Smart Inventory'}

    def test_unable_to_create_group(self, factories):
        inventory = factories.inventory(host_filter='name=localhost', kind='smart')
        with pytest.raises(exc.BadRequest) as e:
            factories.group(inventory=inventory)
        assert e.value[1]['inventory'] == {'detail': 'Cannot create Group for Smart Inventory'}

    def test_unable_to_create_root_group(self, factories):
        inventory = factories.inventory(host_filter='name=localhost', kind='smart')

        with pytest.raises(exc.BadRequest) as e:
            inventory.related.root_groups.post()
        assert e.value[1]['inventory'] == {'detail': 'Cannot create Group for Smart Inventory'}

    def test_unable_to_create_inventory_source(self, factories):
        inventory = factories.inventory(host_filter='name=localhost', kind='smart')
        with pytest.raises(exc.BadRequest) as e:
            factories.inventory_source(inventory=inventory)
        assert e.value[1]['inventory'] == {'detail': 'Cannot create Inventory Source for Smart Inventory'}

    def test_unable_to_have_insights_credential(self, factories):
        credential = factories.credential(kind='insights')
        expected_error = ['Assignment not allowed for Smart Inventory']

        with pytest.raises(exc.BadRequest) as e:
            factories.inventory(host_filter='name=localhost', kind='smart', insights_credential=credential.id)
        assert e.value.msg['insights_credential'] == expected_error

        inventory = factories.inventory(host_filter='name=localhost', kind='smart')
        with pytest.raises(exc.BadRequest) as e:
            inventory.insights_credential = credential.id
        assert e.value.msg['insights_credential'] == expected_error

    def test_unable_to_update_regular_inventory_into_smart_inventory(self, factories):
        inventory = factories.inventory()
        with pytest.raises(exc.MethodNotAllowed):
            inventory.patch(host_filter="name=localhost", kind="smart")

    def test_able_to_update_smart_inventory_into_regular_inventory(self, factories):
        host = factories.host()
        inventory = factories.inventory(organization=host.ds.inventory.ds.organization,
                                        host_filter="name={0}".format(host.name), kind="smart")
        assert inventory.related.hosts.get().count == 1

        inventory.patch(host_filter="", kind="")
        assert inventory.related.hosts.get().count == 0

    @pytest.mark.yolo
    def test_launch_ahc_with_smart_inventory(self, factories):
        inventory = factories.inventory()
        parent_group, child_group = [factories.group(inventory=inventory) for _ in range(2)]
        parent_group.add_group(child_group)
        for group in (parent_group, child_group):
            host = factories.host(name="test_host_{0}".format(group.name), inventory=inventory)
            group.add_host(host)
        factories.host(name="test_host_root", inventory=inventory)

        smart_inventory = factories.inventory(organization=inventory.ds.organization, host_filter="search=test_host",
                                              kind="smart")
        hosts = smart_inventory.related.hosts.get()
        assert hosts.count == 3

        ahc = factories.ad_hoc_command(inventory=smart_inventory).wait_until_completed()
        ahc.assert_successful()
        assert ahc.summary_fields.inventory.id == smart_inventory.id
        assert ahc.inventory == smart_inventory.id

        assert ahc.related.inventory.get().id == smart_inventory.id
        assert ahc.related.events.get().count > 0
        activity_stream = ahc.related.activity_stream.get()
        assert activity_stream.count == 1
        assert activity_stream.results.pop().operation == 'create'

    @pytest.mark.yolo
    def test_launch_job_template_with_smart_inventory(self, factories):
        inventory = factories.inventory()
        parent_group, child_group = [factories.group(inventory=inventory) for _ in range(2)]
        parent_group.add_group(child_group)
        for group in (parent_group, child_group):
            host = factories.host(name="test_host_{0}".format(group.name), inventory=inventory)
            group.add_host(host)
        factories.host(name="test_host_root", inventory=inventory)

        smart_inventory = factories.inventory(organization=inventory.ds.organization, host_filter="search=test_host",
                                              kind="smart")
        hosts = smart_inventory.related.hosts.get()
        assert hosts.count == 3

        jt = factories.job_template(inventory=smart_inventory)
        job = jt.launch().wait_until_completed()
        job.assert_successful()
        assert job.summary_fields.inventory.id == smart_inventory.id
        assert job.inventory == smart_inventory.id

        assert job.related.inventory.get().id == smart_inventory.id
        assert job.related.job_host_summaries.get().count == 3
        assert job.related.job_events.get().count > 0
        activity_stream = job.related.activity_stream.get()
        assert activity_stream.count == 1
        assert activity_stream.results.pop().operation == 'create'

    def test_launch_ahc_with_limit(self, factories):
        inventory = factories.inventory()
        parent_group, child_group = [factories.group(inventory=inventory) for _ in range(2)]
        parent_group.add_group(child_group)
        for group in (parent_group, child_group):
            group.add_host(factories.host(name="test_host_{0}".format(group.name), inventory=inventory))
        factories.host(name="test_host_root", inventory=inventory)

        smart_inventory = factories.inventory(organization=inventory.ds.organization, host_filter="search=test_host",
                                              kind="smart")
        host_names = [host.name for host in smart_inventory.related.hosts.get().results]
        assert len(host_names) == 3

        for name in host_names:
            ahc = factories.ad_hoc_command(inventory=smart_inventory, limit=name).wait_until_completed()
            ahc.assert_successful()

            runner_events = ahc.related.events.get(event__startswith='runner_on_ok')
            assert runner_events.count == 1
            assert runner_events.results[0].host_name == name

    def test_launch_job_with_limit(self, factories):
        inventory = factories.inventory()
        parent_group, child_group = [factories.group(inventory=inventory) for _ in range(2)]
        parent_group.add_group(child_group)
        for group in (parent_group, child_group):
            group.add_host(factories.host(name="test_host_{0}".format(group.name), inventory=inventory))
        factories.host(name="test_host_root", inventory=inventory)

        smart_inventory = factories.inventory(organization=inventory.ds.organization, host_filter="search=test_host",
                                              kind="smart")
        host_names = [host.name for host in smart_inventory.related.hosts.get().results]
        assert len(host_names) == 3
        jt = factories.job_template(inventory=smart_inventory)

        for name in host_names:
            jt.limit = name
            job = jt.launch().wait_until_completed()
            job.assert_successful()

            runner_events = job.related.job_events.get(event__startswith='runner_on_ok')
            assert runner_events.count == 1
            assert runner_events.results[0].host_name == name

    def test_ahcs_should_not_run_on_disabled_smart_inventory_hosts(self, factories):
        host = factories.host(enabled=False)
        smart_inventory = factories.inventory(organization=host.ds.inventory.ds.organization, kind="smart",
                                              host_filter="name={0}".format(host.name))
        ahc = factories.ad_hoc_command(inventory=smart_inventory, module_name='ping').wait_until_completed()
        ahc.assert_successful()
        assert 'provided hosts list is empty' in ahc.result_stdout

    def test_jobs_should_not_run_on_disabled_smart_inventory_hosts(self, factories):
        host = factories.host(enabled=False)
        smart_inventory = factories.inventory(organization=host.ds.inventory.ds.organization, kind="smart",
                                              host_filter="name={0}".format(host.name))
        job = factories.job_template(inventory=smart_inventory).launch().wait_until_completed()
        job.assert_successful()
        assert 'skipping: no hosts matched' in job.result_stdout

    def test_host_update_after_ahc(self, factories):
        host = factories.host()
        smart_inventory = factories.inventory(organization=host.ds.inventory.ds.organization, kind="smart",
                                              host_filter="name={0}".format(host.name))
        ahc = factories.ad_hoc_command(inventory=smart_inventory).wait_until_completed()

        ahcs = host.related.ad_hoc_commands.get()
        assert ahcs.count == 1
        assert ahcs.results.pop().id == ahc.id
        assert host.related.ad_hoc_command_events.get().count > 0

    def test_ad_hoc_host_event_links(self, factories):
        org = factories.organization()
        normal_inventory = factories.inventory(organization=org)
        host = factories.host(name='test_host', inventory=normal_inventory)
        smart_inventory = factories.inventory(organization=org, host_filter="name=test_host", kind="smart")

        ahc = factories.ad_hoc_command(inventory=smart_inventory).wait_until_completed()
        assert set(event.host for event in ahc.get_related('events').results) == set([None, host.id])

    def test_host_update_after_job(self, factories):
        host = factories.host()
        smart_inventory = factories.inventory(organization=host.ds.inventory.ds.organization, kind="smart",
                                              host_filter="name={0}".format(host.name))
        job = factories.job_template(inventory=smart_inventory).launch().wait_until_completed()

        job.assert_successful()
        jhs = job.related.job_host_summaries.get().results.pop()

        assert host.get().summary_fields.last_job.id == job.id
        assert host.summary_fields.last_job_host_summary.id == jhs.id
        recent_jobs = host.summary_fields.recent_jobs
        assert len(recent_jobs) == 1
        assert recent_jobs.pop().id == job.id

        assert host.last_job == job.id
        assert host.last_job_host_summary == jhs.id

        assert host.related.job_host_summaries.get().results.pop().id == jhs.id
        assert host.related.job_events.get().count > 0
        assert host.related.last_job.get().id == job.id
        assert host.related.last_job_host_summary.get().id == jhs.id

    def test_host_sources_original_inventory(self, factories):
        host = factories.host()
        inventory = host.ds.inventory
        factories.inventory(organization=host.ds.inventory.ds.organization, kind="smart",
                            host_filter="name={0}".format(host.name))

        assert host.get().related.inventory.get().id == inventory.id
        assert host.summary_fields.inventory.id == inventory.id
        assert host.inventory == inventory.id

    def test_duplicate_hosts(self, factories):
        org = factories.organization()
        inv1, inv2 = [factories.inventory(organization=org) for _ in range(2)]
        inventory = factories.inventory(organization=org, host_filter="name=test_host", kind="smart")
        hosts = [factories.host(name='test_host', inventory=inv) for inv in (inv1, inv2)]

        inv_hosts = inventory.related.hosts.get()
        smart_host_id = min([host.id for host in hosts])
        assert inv_hosts.count == 1
        assert inv_hosts.results.pop().id == smart_host_id

        # verify that the events link back to the hosts, and to the correct hosts
        job = factories.job_template(inventory=inventory).launch().wait_until_completed()
        assert set(event.host for event in job.get_related('job_events').results) == set([None, smart_host_id])

    def test_deleted_host_does_not_error_event(self, factories):
        """Smart inventories cannot reasonably have deletion protection like
        what normal inventories do, because there is no universally reliable
        link from the host to the inventory.
        As such, hosts in smart inventories can be deleted while jobs are running.
        Those jobs should not error when this happens.
        """
        org = factories.organization()
        normal_inventory = factories.inventory(organization=org)
        host = factories.host(name='test_host', inventory=normal_inventory)
        smart_inventory = factories.inventory(organization=org, host_filter="name=test_host", kind="smart")

        jt_sleep = factories.job_template(
            inventory=smart_inventory,
            playbook='sleep.yml',
            extra_vars='{"sleep_interval": 1}'
        )
        job = jt_sleep.launch().wait_until_completed()
        expected_event_ct = job.get_related('job_events').count

        jt_sleep.extra_vars = '{"sleep_interval": 20}'
        job2 = jt_sleep.launch()
        poll_until(lambda: job2.get_related('job_events').count, timeout=30)
        host.delete()
        # we cannot use wait_until_completed because the error case is where
        # not all events have come in, which would block this
        poll_until(lambda: job2.get_related('job_events', event='playbook_on_stats').count, timeout=30)
        logged_sleep(2)
        assert job2.get_related('job_events').count == expected_event_ct

    def test_source_inventory_variables_ignored(self, factories):
        inventory = factories.inventory(variables="ansible_connection: local")
        group = factories.group(inventory=inventory, variables="ansible_connection: local")
        host = factories.host(inventory=inventory, variables="")
        group.add_host(host)

        jt = factories.job_template(inventory=inventory)
        jt.launch().wait_until_completed().assert_successful()

        smart_inventory = factories.inventory(organization=inventory.ds.organization, kind="smart",
                                              host_filter="name={0}".format(host.name), variables="")
        assert smart_inventory.related.hosts.get().count == 1

        jt.inventory = smart_inventory.id
        job = jt.launch().wait_until_completed()
        assert job.status == 'failed'
        assert 'Failed to connect to the host via ssh' in job.result_stdout

    def test_overriden_smart_inventory_variables(self, factories):
        host = factories.host(variables="ansible_connection: local")
        smart_inventory = factories.inventory(organization=host.ds.inventory.ds.organization, kind="smart",
                                              host_filter="name={0}".format(host.name),
                                              variables="ansible_connection: ssh")
        assert smart_inventory.related.hosts.get().count == 1

        jt = factories.job_template(inventory=smart_inventory)
        jt.launch().wait_until_completed().assert_successful()

    def test_smart_inventory_deletion_should_not_cascade_delete_hosts(self, factories):
        host = factories.host()
        inventory = factories.inventory(organization=host.ds.inventory.ds.organization, kind='smart',
                                        host_filter='name={0}'.format(host.name))
        assert inventory.related.hosts.get().count == 1

        inventory.delete().wait_until_deleted()
        host.get()
