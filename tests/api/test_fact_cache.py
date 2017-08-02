# -*- coding: utf-8 -*-

from towerkit.utils import to_str
import fauxfactory
import pytest

from tests.api import Base_Api_Test


@pytest.mark.api
@pytest.mark.skip_selenium
class TestFactCache(Base_Api_Test):

    pytestmark = pytest.mark.usefixtures('authtoken', 'install_enterprise_license_unlimited')

    def assert_updated_facts(self, ansible_facts):
        """Perform basic validation on host details ansible_facts."""
        assert ansible_facts.module_setup
        assert 'ansible_distribution' in ansible_facts
        assert 'ansible_machine' in ansible_facts
        assert 'ansible_system' in ansible_facts

    def test_ingest_facts_with_gather_facts_playbook(self, factories):
        host = factories.v2_host()
        ansible_facts = host.related.ansible_facts.get()
        assert not ansible_facts.json

        jt = factories.v2_job_template(inventory=host.ds.inventory, playbook='gather_facts.yml', use_fact_cache=True)
        assert jt.launch().wait_until_completed().is_successful

        self.assert_updated_facts(ansible_facts.get())

    @pytest.mark.requires_single_instance
    def test_ingest_facts_with_tower_scan_playbook(self, request, factories, ansible_runner, encrypted_scm_credential):
        host = factories.v2_host()

        machine_id = "4da7d1f8-14f3-4cdc-acd5-a3465a41f25d"
        ansible_runner.file(path='/etc/redhat-access-insights', state="directory")
        ansible_runner.shell('echo -n {0} > /etc/redhat-access-insights/machine-id'.format(machine_id))
        request.addfinalizer(lambda: ansible_runner.file(path='/etc/redhat-access-insights', state="absent"))

        project = factories.v2_project(scm_url="git@github.com:ansible/tower-fact-modules.git",
                                       credential=encrypted_scm_credential, wait=True)
        jt = factories.v2_job_template(inventory=host.ds.inventory, project=project, playbook='scan_facts.yml',
                                       use_fact_cache=True)
        assert jt.launch().wait_until_completed().is_successful

        ansible_facts = host.related.ansible_facts.get()
        self.assert_updated_facts(ansible_facts)
        assert ansible_facts.services['sshd.service']
        assert ansible_facts.packages['ansible-tower']
        assert ansible_facts.insights['system_id'] == machine_id

    def test_ingest_facts_with_host_with_unicode_hostname(self, factories):
        host = factories.v2_host(name=fauxfactory.gen_utf8())
        jt = factories.v2_job_template(inventory=host.ds.inventory, playbook='gather_facts.yml', use_fact_cache=True)
        assert jt.launch().wait_until_completed().is_successful

        ansible_facts = host.related.ansible_facts.get()
        self.assert_updated_facts(ansible_facts)

    def test_ingest_facts_with_host_with_hostname_with_spaces(self, factories):
        host = factories.v2_host(name="hostname with spaces")
        jt = factories.v2_job_template(inventory=host.ds.inventory, playbook='gather_facts.yml', use_fact_cache=True)
        assert jt.launch().wait_until_completed().is_successful

        ansible_facts = host.related.ansible_facts.get()
        self.assert_updated_facts(ansible_facts)

    def test_consume_facts_with_single_host(self, factories):
        host = factories.v2_host()
        jt = factories.v2_job_template(inventory=host.ds.inventory, playbook='gather_facts.yml', use_fact_cache=True)
        assert jt.launch().wait_until_completed().is_successful

        jt.playbook = 'use_facts.yml'
        job = jt.launch().wait_until_completed()
        assert job.is_successful

        ansible_facts = host.related.ansible_facts.get()
        assert ansible_facts.ansible_distribution in job.result_stdout
        assert ansible_facts.ansible_machine in job.result_stdout
        assert ansible_facts.ansible_system in job.result_stdout

    def test_consume_facts_with_multiple_hosts(self, factories):
        inventory = factories.v2_inventory()
        hosts = []
        for _ in range(3):
            host = factories.v2_host(inventory=inventory)
            hosts.append(host)

        jt = factories.v2_job_template(inventory=host.ds.inventory, playbook='gather_facts.yml', use_fact_cache=True)
        assert jt.launch().wait_until_completed().is_successful

        jt.playbook = 'use_facts.yml'
        job = jt.launch().wait_until_completed()
        assert job.is_successful

        ansible_facts = hosts.pop().related.ansible_facts.get()  # facts should be the same between hosts
        assert job.result_stdout.count(ansible_facts.ansible_distribution) == 3
        assert job.result_stdout.count(ansible_facts.ansible_machine) == 3
        assert job.result_stdout.count(ansible_facts.ansible_system) == 3

        for host in hosts:
            assert host.get().summary_fields.last_job.id == job.id

    def test_consume_facts_with_multiple_hosts_and_limit(self, factories):
        inventory = factories.v2_inventory()
        hosts = []
        for _ in range(3):
            host = factories.v2_host(inventory=inventory)
            hosts.append(host)
        target_host = hosts.pop()

        jt = factories.v2_job_template(inventory=host.ds.inventory, playbook='gather_facts.yml', use_fact_cache=True)
        scan_job = jt.launch().wait_until_completed()
        assert scan_job.is_successful

        jt.playbook = 'use_facts.yml'
        jt.limit = target_host.name
        fact_job = jt.launch().wait_until_completed()
        assert fact_job.is_successful

        ansible_facts = target_host.related.ansible_facts.get()
        assert fact_job.result_stdout.count(ansible_facts.ansible_distribution) == 1
        assert fact_job.result_stdout.count(ansible_facts.ansible_machine) == 1
        assert fact_job.result_stdout.count(ansible_facts.ansible_system) == 1

        assert target_host.get().summary_fields.last_job.id == fact_job.id
        for host in hosts:
            assert host.get().summary_fields.last_job.id == scan_job.id

    def test_consume_facts_with_custom_ansible_module(self, factories):
        host = factories.v2_host()
        jt = factories.v2_job_template(inventory=host.ds.inventory, playbook='scan_custom.yml', use_fact_cache=True)
        job = jt.launch().wait_until_completed()
        assert job.is_successful

        target_job_events = job.related.job_events.get(event="runner_on_ok", task="test_scan_facts")
        assert target_job_events.count == 1
        target_job_event = target_job_events.results.pop()
        ansible_facts = target_job_event.event_data.res.ansible_facts

        assert ansible_facts.string == "abc"
        assert to_str(ansible_facts.unicode_string) == "鵟犭酜귃ꔀꈛ竳䙭韽ࠔ"
        assert ansible_facts.int == 1
        assert ansible_facts.float == 1.0
        assert ansible_facts.bool is True
        assert ansible_facts.null is None
        assert ansible_facts.list == ["abc", 1, 1.0, True, None, [], {}]
        assert ansible_facts.obj == dict(string="abc", int=1, float=1.0, bool=True, null=None, list=[], obj={})
        assert ansible_facts.empty_list == []
        assert ansible_facts.empty_obj == {}

    def test_clear_facts(self, factories, ansible_version_cmp):
        if ansible_version_cmp("2.3") < 0:
            pytest.skip("Not supported on Ansible-2.2.")
        host = factories.v2_host()
        jt = factories.v2_job_template(inventory=host.ds.inventory, playbook='gather_facts.yml', use_fact_cache=True)
        assert jt.launch().wait_until_completed().is_successful

        jt.playbook = 'clear_facts.yml'
        assert jt.launch().wait_until_completed().is_successful

        jt.playbook = 'use_facts.yml'
        job = jt.launch().wait_until_completed()
        assert job.status == 'failed'
        assert "The error was: 'ansible_distribution' is undefined" in job.result_stdout
