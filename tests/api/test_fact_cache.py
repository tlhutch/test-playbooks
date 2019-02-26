# -*- coding: utf-8 -*-
import json

from towerkit.utils import random_title
import fauxfactory
import pytest

from tests.api import APITest


@pytest.mark.api
@pytest.mark.usefixtures('authtoken', 'install_enterprise_license_unlimited')
class TestFactCache(APITest):

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
        jt.launch().wait_until_completed().assert_successful()

        self.assert_updated_facts(ansible_facts.get())
        assert "foo" not in ansible_facts
        assert "bar" not in ansible_facts

    @pytest.fixture
    def scan_facts_job_template(self, factories):
        host = factories.v2_host()
        project = factories.v2_project(scm_url='https://github.com/ansible/awx-facts-playbooks', wait=True)
        return factories.v2_job_template(description="3.2 scan_facts JT %s" % fauxfactory.gen_utf8(), project=project,
                                         inventory=host.ds.inventory, playbook='scan_facts.yml', use_fact_cache=True)

    @pytest.mark.mp_group('AWX_PROOT_ENABLED', 'isolated_serial')
    def test_ingest_facts_with_tower_scan_playbook(self, skip_if_cluster, request, factories, ansible_runner, ansible_os_family,
                                                   is_docker, scan_facts_job_template, v2, update_setting_pg):
        machine_id = "4da7d1f8-14f3-4cdc-acd5-a3465a41f25d"
        ansible_runner.file(path='/etc/redhat-access-insights', state="directory")
        ansible_runner.shell('echo -n {0} > /etc/redhat-access-insights/machine-id'.format(machine_id))
        request.addfinalizer(lambda: ansible_runner.file(path='/etc/redhat-access-insights', state="absent"))

        # https://github.com/ansible/tower/issues/2743
        update_setting_pg(
            v2.settings.get().get_endpoint('jobs'),
            {'AWX_PROOT_ENABLED': False})
        scan_facts_job_template.launch().wait_until_completed().assert_successful()

        ansible_facts = scan_facts_job_template.ds.inventory.related.hosts.get().results[0].related.ansible_facts.get()
        self.assert_updated_facts(ansible_facts)

        if is_docker:
            assert ansible_facts.services['network']
        elif ansible_os_family == 'RedHat':
            assert ansible_facts.services['sshd.service']
        # for ubuntu systems
        else:
            assert ansible_facts.services['ssh']

        assert ansible_facts.packages['which'] if is_docker else ansible_facts.packages['ansible-tower']
        assert ansible_facts.insights['system_id'] == machine_id

    def test_ingest_facts_with_host_with_unicode_hostname(self, factories):
        host = factories.v2_host(name=fauxfactory.gen_utf8())
        jt = factories.v2_job_template(inventory=host.ds.inventory, playbook='gather_facts.yml', use_fact_cache=True)
        jt.launch().wait_until_completed().assert_successful()

        ansible_facts = host.related.ansible_facts.get()
        self.assert_updated_facts(ansible_facts)

    def test_ingest_facts_with_host_with_hostname_with_spaces(self, factories):
        host = factories.v2_host(name="hostname with spaces")
        jt = factories.v2_job_template(inventory=host.ds.inventory, playbook='gather_facts.yml', use_fact_cache=True)
        jt.launch().wait_until_completed().assert_successful()

        ansible_facts = host.related.ansible_facts.get()
        self.assert_updated_facts(ansible_facts)

    def test_consume_facts_with_single_host(self, factories):
        host = factories.v2_host()
        jt = factories.v2_job_template(inventory=host.ds.inventory, playbook='gather_facts.yml', use_fact_cache=True)
        jt.launch().wait_until_completed().assert_successful()

        jt.patch(playbook='use_facts.yml', job_tags='ansible_facts')
        job = jt.launch().wait_until_completed()
        job.assert_successful()

        ansible_facts = host.related.ansible_facts.get()
        assert ansible_facts.ansible_distribution in job.result_stdout
        assert ansible_facts.ansible_machine in job.result_stdout
        assert ansible_facts.ansible_system in job.result_stdout

    def test_consume_facts_with_multiple_hosts(self, factories):
        inventory = factories.v2_inventory()
        hosts = [factories.v2_host(inventory=inventory) for _ in range(3)]

        jt = factories.v2_job_template(inventory=hosts[0].ds.inventory, playbook='gather_facts.yml', use_fact_cache=True)
        jt.launch().wait_until_completed().assert_successful()

        jt.patch(playbook='use_facts.yml', job_tags='ansible_facts')
        job = jt.launch().wait_until_completed()
        job.assert_successful()

        ansible_facts = hosts.pop().related.ansible_facts.get()  # facts should be the same between hosts
        assert job.result_stdout.count(ansible_facts.ansible_distribution) == 3
        assert job.result_stdout.count(ansible_facts.ansible_machine) == 3
        assert job.result_stdout.count(ansible_facts.ansible_system) == 3

        for host in hosts:
            assert host.get().summary_fields.last_job.id == job.id

    def test_consume_facts_with_multiple_hosts_and_limit(self, factories):
        inventory = factories.v2_inventory()
        hosts = [factories.v2_host(inventory=inventory) for _ in range(3)]
        target_host = hosts.pop()

        jt = factories.v2_job_template(inventory=target_host.ds.inventory, playbook='gather_facts.yml', use_fact_cache=True)
        scan_job = jt.launch().wait_until_completed()
        scan_job.assert_successful()

        jt.patch(playbook='use_facts.yml', job_tags='ansible_facts')
        jt.limit = target_host.name
        fact_job = jt.launch().wait_until_completed()
        fact_job.assert_successful()

        ansible_facts = target_host.related.ansible_facts.get()
        assert fact_job.result_stdout.count(ansible_facts.ansible_distribution) == 1
        assert fact_job.result_stdout.count(ansible_facts.ansible_machine) == 1
        assert fact_job.result_stdout.count(ansible_facts.ansible_system) == 1

        assert target_host.get().summary_fields.last_job.id == fact_job.id
        for host in hosts:
            assert host.get().summary_fields.last_job.id == scan_job.id

    def test_consume_updated_facts(self, factories):
        host = factories.v2_host()

        jt = factories.v2_job_template(inventory=host.ds.inventory, playbook='gather_facts.yml', use_fact_cache=True)
        jt.launch().wait_until_completed().assert_successful()
        ansible_facts = host.related.ansible_facts.get()
        first_time = ansible_facts.ansible_date_time.time

        jt.launch().wait_until_completed().assert_successful()
        second_time = ansible_facts.get().ansible_date_time.time
        assert second_time > first_time

        jt.patch(playbook='use_facts.yml', job_tags='ansible_facts')
        job = jt.launch().wait_until_completed()
        job.assert_successful()

        self.assert_updated_facts(ansible_facts)
        assert second_time in job.result_stdout

    def test_consume_facts_with_custom_ansible_module(self, factories):
        host = factories.v2_host()
        jt = factories.v2_job_template(inventory=host.ds.inventory, playbook='scan_custom.yml', use_fact_cache=True)
        job = jt.launch().wait_until_completed()
        job.assert_successful()

        target_job_events = job.related.job_events.get(event="runner_on_ok", task="test_scan_facts")
        assert target_job_events.count == 1
        target_job_event = target_job_events.results.pop()
        ansible_facts = target_job_event.event_data.res.ansible_facts

        # verify ingested facts
        assert ansible_facts.string == "abc"
        assert str(ansible_facts.unicode_string) == "鵟犭酜귃ꔀꈛ竳䙭韽ࠔ"
        assert ansible_facts.int == 1
        assert ansible_facts.float == 1.0
        assert ansible_facts.bool is True
        assert ansible_facts.null is None
        assert ansible_facts.list == ["abc", 1, 1.0, True, None, [], {}]
        assert ansible_facts.obj == dict(string="abc", int=1, float=1.0, bool=True, null=None, list=[], obj={})
        assert ansible_facts.empty_list == []
        assert ansible_facts.empty_obj == {}

        jt.patch(playbook='use_facts.yml', job_tags='custom_facts')
        job = jt.launch().wait_until_completed()
        job.assert_successful()

        # verify facts consumption
        result_stdout = job.result_stdout
        assert '"msg": "abc"' in result_stdout
        assert '"msg": "鵟犭酜귃ꔀꈛ竳䙭韽ࠔ"' in result_stdout
        assert '"msg": 1' in result_stdout
        assert '"msg": 1.0' in result_stdout
        assert '"msg": true' in result_stdout
        assert '"msg": null' in result_stdout
        assert any(('"msg": [\r\n' in result_stdout, '"msg": [\n' in result_stdout))
        assert any(('"msg": {\r\n' in result_stdout, '"msg": {\n' in result_stdout))
        assert '"msg": []' in result_stdout
        assert '"msg": {}' in result_stdout

    def test_deleted_hosts_not_reused_by_cache(self, factories):
        jt = factories.v2_job_template(playbook='gather_facts.yml', use_fact_cache=True)
        inv = jt.ds.inventory
        deleted_host = factories.v2_host(inventory=inv)

        job = jt.launch().wait_until_completed()
        job.assert_successful()

        deleted_host.delete()
        job = job.relaunch().wait_until_completed()
        job.assert_successful()

        assert job.related.job_host_summaries.get().count == 0

    def test_clear_facts(self, factories, ansible_version_cmp):
        if ansible_version_cmp("2.3.2") < 0:
            pytest.skip("Not support on Ansible versions predating 2.3.2.")
        host = factories.v2_host()

        jt = factories.v2_job_template(inventory=host.ds.inventory, playbook='gather_facts.yml', use_fact_cache=True)
        jt.launch().wait_until_completed().assert_successful()
        ansible_facts = host.related.ansible_facts.get()
        self.assert_updated_facts(ansible_facts)

        jt.playbook = 'clear_facts.yml'
        jt.launch().wait_until_completed().assert_successful()

        assert not host.related.ansible_facts.get().json

    @pytest.mark.ansible_integration
    def test_scan_file_paths_are_sourced(self, scan_facts_job_template):
        scan_file_paths = ('/tmp', '/bin')
        scan_facts_job_template.extra_vars = json.dumps(dict(scan_file_paths=','.join(scan_file_paths)))

        job = scan_facts_job_template.launch().wait_until_completed()
        job.assert_successful()

        host = scan_facts_job_template.related.inventory.get().related.hosts.get().results[0]
        files = host.related.ansible_facts.get().files

        for file_path in [f.path for f in files]:
            assert any([file_path.startswith(path) for path in scan_file_paths])

    @pytest.mark.ansible_integration
    @pytest.mark.mp_group(group="pytest_mark_requires_isolation", strategy="isolated_serial")
    def test_scan_file_paths_are_traversed(self, skip_if_cluster, v2, request, ansible_runner, scan_facts_job_template):
        test_dir = '/tmp/test{}'.format(fauxfactory.gen_alphanumeric())
        request.addfinalizer(lambda: ansible_runner.file(path=test_dir, state='absent'))

        jobs_settings = v2.settings.get().get_endpoint('jobs')
        prev_proot_show_paths = jobs_settings.AWX_PROOT_SHOW_PATHS
        jobs_settings.AWX_PROOT_SHOW_PATHS = prev_proot_show_paths + [test_dir]
        request.addfinalizer(lambda: jobs_settings.patch(AWX_PROOT_SHOW_PATHS=prev_proot_show_paths))

        dir_path = '{}/directory/traversal/is/working'.format(test_dir)
        res = list(ansible_runner.file(path=dir_path, state='directory').values())[0]
        assert not res.get('failed') and res.get('changed')

        file_path = dir_path + '/some_file'
        res = list(ansible_runner.file(path=file_path, state='touch').values())[0]
        assert not res.get('failed') and res.get('changed')

        extra_vars = dict(scan_file_paths=test_dir, scan_use_recursive=True)
        scan_facts_job_template.patch(extra_vars=json.dumps(extra_vars))

        job = scan_facts_job_template.launch().wait_until_completed()
        job.assert_successful()

        host = scan_facts_job_template.related.inventory.get().related.hosts.get().results[0]
        files = host.related.ansible_facts.get().files
        assert len(files) == 1
        assert files[0].path == file_path

    @pytest.mark.ansible_integration
    def test_file_scan_job_provides_checksums(self, scan_facts_job_template):
        scan_facts_job_template.extra_vars = json.dumps(dict(scan_file_paths='/tmp,/bin', scan_use_checksum=True))

        job = scan_facts_job_template.launch().wait_until_completed()
        job.assert_successful()

        host = scan_facts_job_template.related.inventory.get().related.hosts.get().results[0]
        files = host.related.ansible_facts.get().files

        for file in files:
            # Ensure the selected files aren't things like socket, directory, etc. and that
            # we have permission to read them
            if not file.isdir and file.roth and file.isreg:
                assert file.checksum

    @pytest.mark.ansible_integration
    def test_use_fact_cache_for_host_with_large_hostvars(self, factories):
        script = """#!/usr/bin/env python
import json
inv = dict(somegroup{0}=dict(hosts=['somehost{0}'],
                             vars=dict(ansible_host='127.0.0.1',
                                       ansible_connection='local',
                                       cruft='x' * 1024 ** 2)))

print(json.dumps(inv))""".format(random_title(non_ascii=False))
        inv_src = factories.v2_inventory_source(inventory_script=(True, dict(script=script)))
        inv_src.update().wait_until_completed().assert_successful()
        jt = factories.v2_job_template(inventory=inv_src.ds.inventory,
                                       use_fact_cache=True,
                                       playbook='scan_custom.yml')
        jt.launch().wait_until_completed().assert_successful()
        host = inv_src.ds.inventory.related.hosts.get().results.pop()
        facts = host.related.ansible_facts.get()
        assert facts.string == "abc"

    def test_cachable_custom_fact(self, factories):
        host = factories.v2_host()
        jt = factories.v2_job_template(inventory=host.ds.inventory, playbook='gather_facts.yml',
                                       use_fact_cache=True, extra_vars=dict(set_fact_cacheable=True))
        job = jt.launch().wait_until_completed()
        job.assert_successful()

        facts = host.related.ansible_facts.get()
        self.assert_updated_facts(facts)
        assert facts.foo == "bar"
        assert facts.bar.a.b == ["c", "d"]
