import os
import base64
import json
import boto3
import csv

from towerkit import config
import towerkit.exceptions as exc
import pytest

from tests.api import APITest


@pytest.fixture(scope="function")
def register_rhn_and_insights(ansible_runner):
    rhn_username = config.credentials.insights.username
    rhn_password = config.credentials.insights.password
    ansible_runner.redhat_subscription(state='present',
                                             username=rhn_username,
                                             password=rhn_password,
                                             auto_attach=True)

    ansible_runner.yum(state='installed', name='insights-client')
    ansible_runner.shell('insights-client --register')
    yield
    ansible_runner.shell('insights-client --unregister')
    ansible_runner.redhat_subscription(state='absent',
                                             username=rhn_username,
                                             password=rhn_password)
    ansible_runner.yum(state='absent', name='insights-client')


@pytest.mark.api
@pytest.mark.destructive
@pytest.mark.mp_group('Insights', 'serial')
@pytest.mark.usefixtures('authtoken', 'install_enterprise_license_unlimited')
class TestInsights(APITest):

    registered_machine_id = "84baf1a3-eee5-4f92-b5ee-42609e89a2cd"
    unregistered_machine_id = "aaaabbbb-cccc-dddd-eeee-ffffgggghhhh"

    @pytest.fixture(scope="class")
    def insights_inventory(self, request, class_factories, modified_ansible_adhoc, is_docker):
        inventory = class_factories.v2_inventory()
        for name in ('registered_host', 'unregistered_host'):
            class_factories.v2_host(name=name, inventory=inventory)

        modified_ansible_adhoc().tower.file(path='/etc/redhat-access-insights', state="directory")
        request.addfinalizer(lambda: modified_ansible_adhoc().tower.file(path='/etc/redhat-access-insights', state="absent"))

        project = class_factories.v2_project(scm_url="https://github.com/ansible/awx-facts-playbooks", wait=True)
        jt = class_factories.v2_job_template(project=project, inventory=inventory, playbook='scan_facts.yml',
                                             use_fact_cache=True, limit="registered_host")

        # update registered host with registered machine ID
        modified_ansible_adhoc().tower.shell('echo -n {0} > /etc/redhat-access-insights/machine-id'.format(self.registered_machine_id))
        jt.launch().wait_until_completed().assert_successful()

        # update unregistered host with unregistered machine ID
        jt.limit = "unregistered_host"
        modified_ansible_adhoc().tower.shell('echo -n {0} > /etc/redhat-access-insights/machine-id'.format(self.unregistered_machine_id))
        jt.launch().wait_until_completed().assert_successful()

        return inventory

    def test_default_host_machine_id(self, factories):
        """Verify that a normal host has no machine ID."""
        host = factories.v2_host()
        assert not host.insights_system_id

    def test_insights_host_machine_id(self, skip_if_cluster, insights_inventory):
        """Verify that Insights hosts have machine IDs."""
        registered_host = insights_inventory.related.hosts.get(name='registered_host').results.pop()
        unregistered_host = insights_inventory.related.hosts.get(name='unregistered_host').results.pop()
        assert registered_host.insights_system_id == self.registered_machine_id
        assert unregistered_host.insights_system_id == self.unregistered_machine_id

    def test_insights_system_id_is_read_only(self, skip_if_cluster, insights_inventory):
        """Host details insights_system_id should be read-only."""
        unregistered_host = insights_inventory.related.hosts.get(name='unregistered_host').results.pop()
        unregistered_host.insights_system_id = "zzzzyyyy-xxxx-wwww-vvvv-uuuuttttssss"
        assert unregistered_host.get().insights_system_id == self.unregistered_machine_id

    def test_inventory_with_insights_credential(self, skip_if_cluster, factories, insights_inventory):
        """Verify that various inventory fields update for our Insights credential."""
        assert not insights_inventory.insights_credential
        assert not insights_inventory.summary_fields.get('insights_credential')

        credential = factories.v2_credential(kind='insights')
        insights_inventory.insights_credential = credential.id

        assert insights_inventory.insights_credential == credential.id
        assert insights_inventory.summary_fields.insights_credential == dict(id=credential.id,
                                                                             name=credential.name,
                                                                             description=credential.description)

    def test_access_insights_with_no_credential(self, skip_if_cluster, insights_inventory):
        """Verify that attempts to access Insights without a credential raises a 404."""
        hosts = insights_inventory.related.hosts.get().results
        for host in hosts:
            with pytest.raises(exc.NotFound) as e:
                host.related.insights.get()
        assert e.value[1] == {'error': 'The Insights Credential for "{0}" was not found.'.format(insights_inventory.name)}

    def test_access_insights_with_valid_credential_and_registered_host(self, skip_if_cluster, factories, insights_inventory):
        """Verify that attempts to access Insights from a registered host with a valid Insights credential succeed."""
        credential = factories.v2_credential(kind='insights')
        insights_inventory.insights_credential = credential.id
        host = insights_inventory.related.hosts.get(name="registered_host").results.pop()

        assert host.related.insights.get().insights_content == {'last_check_in': '2017-07-20T12:47:59.000Z', 'reports': []}

    def test_access_insights_with_valid_credential_and_unregistered_host(self, skip_if_cluster, factories, insights_inventory):
        """Verify that attempts to access Insights from an unregistered host with a valid Insights credential
        raises a 502.
        """
        credential = factories.v2_credential(kind='insights')
        insights_inventory.insights_credential = credential.id
        host = insights_inventory.related.hosts.get(name="unregistered_host").results.pop()

        with pytest.raises(exc.BadGateway) as e:
            host.related.insights.get()
        assert "Failed to gather reports and maintenance plans from Insights API" in e.value[1]['error']

    def test_access_insights_with_invalid_credential(self, skip_if_cluster, factories, insights_inventory):
        """Verify that attempts to access Insights with a bad Insights credential raise a 502."""
        credential = factories.v2_credential(kind='insights', inputs=dict(username="fake", password="fake"))
        insights_inventory.insights_credential = credential.id
        hosts = insights_inventory.related.hosts.get().results

        for host in hosts:
            with pytest.raises(exc.BadGateway) as e:
                host.related.insights.get()
            assert e.value[1]['error'] == 'Unauthorized access. Please check your Insights Credential username and password.'

    def test_insights_project_no_credential(self, factories):
        """Verify that attempts to create an Insights project without an Insights credential raise a 400."""
        with pytest.raises(exc.BadRequest) as e:
            factories.v2_project(scm_type='insights', credential=None)
        assert e.value[1] == {'credential': ['Insights Credential is required for an Insights Project.']}

    def test_insights_project_with_valid_credential(self, factories):
        """Verify the creation of an Insights project with a valid Insights credential and its
        auto-spawned project update.
        """
        insights_cred = factories.v2_credential(kind='insights')
        project = factories.v2_project(scm_type='insights', credential=insights_cred, wait=True)
        update = project.related.last_update.get()

        project.assert_successful()
        assert project.credential == insights_cred.id
        assert not project.scm_branch
        assert project.scm_type == 'insights'
        assert project.scm_url == 'https://access.redhat.com'
        assert project.scm_revision

        update.assert_successful()
        assert not update.job_explanation
        assert update.project == project.id
        assert update.credential == insights_cred.id
        assert update.job_type == 'check'
        assert update.launch_type == 'manual'
        assert update.scm_type == 'insights'
        assert update.scm_url == 'https://access.redhat.com'
        assert not update.scm_branch

    def test_insights_project_with_invalid_credential(self, factories):
        """Verify the creation of an Insights project with an invalid Insights credential and its
        auto-spawned project update.
        """
        insights_cred = factories.v2_credential(kind='insights', inputs=dict(username="fake", password="fake"))
        project = factories.v2_project(scm_type='insights', credential=insights_cred, wait=True)
        update = project.related.last_update.get()

        assert project.status == "failed"
        assert project.last_job_failed
        assert project.last_update_failed
        assert update.status == "failed"
        assert update.failed is True

    def test_insights_project_directory(self, skip_if_cluster, factories, v2, ansible_runner):
        """Verify created project directory."""
        insights_cred = factories.v2_credential(kind='insights')
        project = factories.v2_project(scm_type='insights', credential=insights_cred, wait=True)
        directory_path = os.path.join(v2.config.get().project_base_dir, project.local_path)

        # assert project directory created
        contacted = ansible_runner.stat(path=directory_path)
        for result in contacted.values():
            assert result['stat']['exists'], "Directory not found under {0}.".format(directory_path)

    def test_matching_insights_revision(self, skip_if_cluster, factories, v2, ansible_runner):
        """Verify that our revision tag matches between the following:
        * Project details.
        * Project update standard output.
        * .verison under our project directory.
        """
        insights_cred = factories.v2_credential(kind='insights')
        project = factories.v2_project(scm_type='insights', credential=insights_cred, wait=True)
        update = project.related.last_update.get()

        scm_revision = project.scm_revision
        assert scm_revision in update.result_stdout

        # verify contents of .version file
        version_path = os.path.join(v2.config.get().project_base_dir, project.local_path, ".version")
        contacted = ansible_runner.shell('cat {0}'.format(version_path))
        assert list(contacted.values())[0]['stdout'] == project.scm_revision


@pytest.mark.mp_group('Insights', 'serial')
@pytest.mark.usefixtures('authtoken', 'install_enterprise_license_unlimited')
class TestInsightsAnalytics(APITest):

    def toggle_analytics(self, update_setting_pg, v2, state=False):
        system_settings = v2.settings.get().get_endpoint('system')
        payload = {'INSIGHTS_DATA_ENABLED': state}
        update_setting_pg(system_settings, payload)

    @pytest.fixture
    def analytics_enabled(self, update_setting_pg, v2, request):
        self.toggle_analytics(update_setting_pg, v2, state=True)
        request.addfinalizer(lambda: self.toggle_analytics(update_setting_pg, v2, state=False))

    def gather_analytics(self, ansible_runner):
        result = ansible_runner.shell('awx-manage gather_analytics').values()[0]
        analytics_payload = [l for l in result['stderr_lines'] if "tar.gz" in l][0]
        tempdir = ansible_runner.tempfile(state='directory', suffix='insights_test').values()[0]['path']
        ansible_runner.unarchive(src=analytics_payload, dest=tempdir, remote_src=True).values()[0]
        files = [f['path'] for f in ansible_runner.find(paths=tempdir).values()[0]['files']]
        return tempdir, files

    def read_json_file(self, file, ansible_runner):
        content = ansible_runner.slurp(path=file).values()[0]['content']
        return json.loads(base64.b64decode(content))

    def read_csv(self, ansible_runner, tempdir, filename):
        csv_file = ansible_runner.fetch(src=filename, dest='/tmp/fetched').values()[0]['dest']
        rows = []
        for row in csv.reader(open(csv_file, 'r', encoding='utf8'), delimiter='\t'):
            rows.append(row)
        return rows

    def collect_stats(self, keys, ansible_runner):
        tempdir, files = self.gather_analytics(ansible_runner)
        stats = {}
        for k in keys:
            filename_split = k.split('.')
            if filename_split[1] == 'json':
                stats[filename_split[0]] = self.read_json_file('{}/{}'.format(tempdir, k), ansible_runner)
            elif filename_split[1] == 'csv':
                stats[filename_split[0]] = self.read_csv(ansible_runner, tempdir, '{}/{}'.format(tempdir, k))
        return stats

    @pytest.mark.ansible(host_pattern='tower[0]')
    def test_awxmanage_gather_analytics_generates_valid_tar(self, ansible_runner, skip_if_not_rhel, analytics_enabled):
        tempdir, files = self.gather_analytics(ansible_runner)
        expected_files = ['config.json', 'counts.json', 'projects_by_scm_type.json']
        for f in expected_files:
            filepath = '{}/{}'.format(tempdir, f)
            assert filepath in files
            content = self.read_json_file(filepath, ansible_runner)
            assert type(content) == dict

    @pytest.mark.ansible(host_pattern='tower[0]')
    def test_awxmanage_gather_analytics_project_count_incremented(self, ansible_runner, factories, skip_if_not_rhel, analytics_enabled):
        counts = self.collect_stats(['counts.json'], ansible_runner)
        projects_before = counts['counts']['project']
        factories.v2_project()
        counts = self.collect_stats(['counts.json'], ansible_runner)
        projects_after = counts['counts']['project']

        assert projects_after == projects_before + 1

    @pytest.mark.ansible(host_pattern='tower[0]')
    def test_awxmanage_gather_analytics_job_status_manual_launch_count_incremented(self, ansible_runner, factories, skip_if_not_rhel, analytics_enabled):
        jt = factories.v2_job_template()
        counts = self.collect_stats(['job_counts.json'], ansible_runner)
        manual_launch_before = counts['job_counts']['launch_type']['manual']

        jt.launch()
        counts = self.collect_stats(['job_counts.json'], ansible_runner)
        manual_launch_after = counts['job_counts']['launch_type']['manual']

        assert manual_launch_after == manual_launch_before + 1

    @pytest.mark.ansible(host_pattern='tower[0]')
    def test_awxmanage_gather_analytics_inventory_counts_incremented(self, ansible_runner, factories, skip_if_not_rhel, analytics_enabled):
        counts = self.collect_stats(['counts.json'], ansible_runner)
        inventory_types_before = counts['counts']['inventories']
        [factories.v2_inventory() for _ in range(2)]
        factories.v2_inventory(kind='smart', host_filter='search=foo')
        counts = self.collect_stats(['counts.json'], ansible_runner)
        inventory_types_after = counts['counts']['inventories']

        assert inventory_types_after['normal'] == inventory_types_before['normal'] + 2
        assert inventory_types_after['smart'] == inventory_types_before['smart'] + 1

    @pytest.mark.ansible(host_pattern='tower[0]')
    def test_awxmanage_gather_analytics_inventory_host_counts_incremented(self, ansible_runner, factories, skip_if_not_rhel, analytics_enabled):
        org = factories.v2_organization()
        empty_inventory = factories.v2_inventory(organization=org)
        two_host_inventory = factories.v2_inventory(organization=org)
        smart_inventory = factories.v2_inventory(kind='smart', host_filter='search=smart-test', organization=org)
        inventory_counts_before = self.collect_stats(['inventory_counts.json'], ansible_runner)
        [factories.v2_host(name="smart-test_{0}".format(i), inventory=two_host_inventory) for i in range(2)]
        factories.v2_host(organization=org)

        inventory_counts_after = self.collect_stats(['inventory_counts.json'], ansible_runner)

        assert inventory_counts_after['inventory_counts'][str(empty_inventory.id)]['hosts'] == inventory_counts_before['inventory_counts'][str(empty_inventory.id)]['hosts'] == 0
        assert inventory_counts_after['inventory_counts'][str(two_host_inventory.id)]['hosts'] == inventory_counts_before['inventory_counts'][str(two_host_inventory.id)]['hosts'] + 2 == 2
        assert inventory_counts_after['inventory_counts'][str(smart_inventory.id)]['num_hosts'] == inventory_counts_before['inventory_counts'][str(smart_inventory.id)]['num_hosts'] + 2 == 2

    @pytest.mark.ansible(host_pattern='tower[0]')
    def test_awxmanage_gather_analytics_job_status_counts_incremented(self, ansible_runner, factories, skip_if_not_rhel, analytics_enabled):
        jt = factories.v2_job_template()
        jt.ds.project.patch(scm_update_on_launch=False)
        jt.ds.project.update().wait_until_completed()
        counts = self.collect_stats(['job_instance_counts.json'], ansible_runner)
        sync_before = 0
        success_before = 0
        for h in counts['job_instance_counts'].keys():
            sync_before += counts['job_instance_counts'][h]['status'].get('sync', 0)
            success_before += counts['job_instance_counts'][h]['launch_type'].get('successful', 0)
        jt.launch().wait_until_completed()
        counts = self.collect_stats(['job_instance_counts.json'], ansible_runner)
        sync_after = 0
        success_after = 0
        for h in counts['job_instance_counts'].keys():
            sync_after += counts['job_instance_counts'][h]['status'].get('sync', 0)
            success_after += counts['job_instance_counts'][h]['launch_type'].get('successful', 0)
        assert success_after == success_before + 1
        assert sync_after == sync_before

    @pytest.mark.ansible(host_pattern='tower[0]')
    def test_awxmanage_gather_analytics_events_table_accurate(self, ansible_runner, factories, skip_if_not_rhel, analytics_enabled):
        # Gather analytics to set last_run
        self.gather_analytics(ansible_runner)
        jt = factories.v2_job_template()
        job = jt.launch().wait_until_completed()

        events = []
        job_events = job.related.job_events.get()
        while True:
            events.extend(job_events.results)
            if not job_events.next:
                break
            job_events = job_events.next.get()

        stats = self.collect_stats(['events_table.csv'], ansible_runner)
        csv_uuids = set()
        event_uuids = set()
        for row in stats['events_table']:
            csv_uuids.add(row[2])
        for e in events:
            event_uuids.add(e['uuid'])
        assert csv_uuids == event_uuids

    @pytest.mark.ansible(host_pattern='tower[0]')
    def test_awxmanage_gather_analytics_unicode(self, ansible_runner, factories, skip_if_not_rhel, analytics_enabled):
        project = factories.v2_project(name='🖖')
        project.update().wait_until_completed()
        inventory = factories.v2_inventory(name='🤔')
        org = factories.v2_organization(name='🤬🥔')
        jt = factories.v2_job_template(playbook='utf-8-䉪ቒ칸ⱷꯔ噂폄蔆㪗輥.yml')
        jt.launch().wait_until_completed()
        counts = self.collect_stats(['inventory_counts.json',
                                     'org_counts.json',
                                     'events_table.csv',
                                     'unified_jobs_table.csv'], ansible_runner)

        assert counts['inventory_counts'][str(inventory.id)]['name'] == '🤔'
        assert counts['org_counts'][str(org.id)]['name'] == '🤬🥔'
        assert len([x for x in counts['events_table'] if x[8] == 'utf-8-䉪ቒ칸ⱷꯔ噂폄蔆㪗輥.yml']) > 0
        assert len([x for x in counts['unified_jobs_table'] if x[4] == '🖖']) > 0

    # Commented out due to logistical concerns with contacting insights dev API from AWS
    # def test_ship_insights_succeeds(self, ansible_runner, skip_if_not_rhel, register_rhn_and_insights):
    #     logfile = '/var/log/insights-client/insights-client.log'
    #     ansible_runner.file(path=logfile, state='absent')
    #     result = ansible_runner.shell('awx-manage gather_analytics --ship').values()[0]['stderr_lines']
    #     assert [l for l in result if "Successfully uploaded report" in l]
    #     log_content = base64.b64decode(ansible_runner.slurp(path=logfile).values()[0]['content']).splitlines()
    #     assert [l for l in log_content if "insights.client.connection Upload status: 202 Accepted" in l]

    # This "test" is temporary, it is being used by @bender to generate data for a summit demo
    # Please contact @bender if you want to remove it
    @pytest.mark.ansible(host_pattern='tower[0]')
    def test_awxmanage_gather_analytics_ship_insights_tar_to_s3(self, ansible_runner, skip_if_not_rhel, analytics_enabled):
        s3_bucket_name = 'tower-analytics-data'
        s3 = boto3.client('s3',
                          aws_access_key_id=config.credentials.cloud.aws.username,
                          aws_secret_access_key=config.credentials.cloud.aws.password,
                          region_name='us-east-1')
        gather_result = ansible_runner.shell('awx-manage gather_analytics').values()[0]
        analytics_file = [l for l in gather_result['stderr_lines'] if "tar.gz" in l][0]
        local_file = ansible_runner.fetch(src=analytics_file, dest='/tmp/', flat=True).values()[0]['dest']
        s3_path = 'integration_data/{}'.format(local_file.split('/')[-1])
        s3.upload_file(local_file, s3_bucket_name, s3_path)

        assert s3.get_object(Bucket=s3_bucket_name, Key=s3_path)['ResponseMetadata']['HTTPStatusCode'] == 200

    def test_awxmanage_gather_analytics_system_uuid_same_across_cluster(self, ansible_runner, skip_if_not_cluster, skip_if_not_rhel, analytics_enabled):
        uuid_result = ansible_runner.shell('echo "from django.conf import settings; print(settings.INSTALL_UUID)" | awx-manage shell')
        node_uuids = set()
        for u in uuid_result.values():
            node_uuids.add(u)
        assert len(node_uuids) == 1
        assert "00000000-0000-0000-0000-000000000000" not in node_uuids
