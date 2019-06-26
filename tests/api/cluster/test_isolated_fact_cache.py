import pytest

from tests.api import APITest


@pytest.mark.usefixtures('authtoken', 'skip_if_not_traditional_cluster')
class TestIsolatedFactCache(APITest):

    @pytest.fixture
    def isolated_instance_group(self, v2):
        return v2.instance_groups.get(name='protected').results.pop()

    def assert_updated_facts(self, ansible_facts):
        assert ansible_facts.module_setup
        assert ansible_facts.ansible_distribution == 'RedHat'
        assert ansible_facts.ansible_machine == 'x86_64'
        assert ansible_facts.ansible_system == 'Linux'

    def test_ingest_facts_with_gather_facts_on_isolated_node(self, factories, isolated_instance_group):
        host = factories.host()
        ansible_facts = host.related.ansible_facts.get()
        assert ansible_facts.json == {}

        jt = factories.job_template(inventory=host.ds.inventory, playbook='gather_facts.yml', use_fact_cache=True)
        jt.add_instance_group(isolated_instance_group)
        job = jt.launch()
        job.wait_until_completed().assert_successful()

        ansible_facts = host.related.ansible_facts.get()
        self.assert_updated_facts(ansible_facts)
        assert job.execution_node in [
            instance.hostname for instance in isolated_instance_group.related.instances.get().results
        ]

    def test_consume_facts_with_multiple_hosts_on_isolated_node(self, factories, isolated_instance_group):
        inventory = factories.inventory()
        hosts = [factories.host(inventory=inventory) for _ in range(3)]
        ansible_facts = hosts.pop().related.ansible_facts.get()  # facts should be the same between hosts

        jt = factories.job_template(inventory=hosts[0].ds.inventory, playbook='gather_facts.yml', use_fact_cache=True)
        jt.add_instance_group(isolated_instance_group)
        job = jt.launch()
        job.wait_until_completed().assert_successful()
        self.assert_updated_facts(ansible_facts.get())
        assert job.execution_node in [
            instance.hostname for instance in isolated_instance_group.related.instances.get().results
        ]

        jt.patch(playbook='use_facts.yml', job_tags='ansible_facts')
        job = jt.launch().wait_until_completed()
        job.assert_successful()

        assert job.result_stdout.count(ansible_facts.ansible_distribution) == 3
        assert job.result_stdout.count(ansible_facts.ansible_machine) == 3
        assert job.result_stdout.count(ansible_facts.ansible_system) == 3

    def test_clear_facts_on_isolated_node(self, factories, isolated_instance_group):
        host = factories.host()

        jt = factories.job_template(inventory=host.ds.inventory, playbook='gather_facts.yml', use_fact_cache=True)
        jt.add_instance_group(isolated_instance_group)
        job = jt.launch()
        job.wait_until_completed().assert_successful()
        ansible_facts = host.related.ansible_facts.get()
        self.assert_updated_facts(ansible_facts)
        assert job.execution_node in [
            instance.hostname for instance in isolated_instance_group.related.instances.get().results
        ]

        jt.playbook = 'clear_facts.yml'
        jt.launch().wait_until_completed().assert_successful()
        assert ansible_facts.get().json == {}
