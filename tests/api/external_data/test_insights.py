import os
import base64
import json
import boto3
import csv
from datetime import datetime
from pathlib import Path

from awxkit import config
import awxkit.exceptions as exc
import pytest

from tests.api import APITest


@pytest.mark.usefixtures('authtoken')
class TestInsights(APITest):

    registered_machine_id = '654918b5-269d-4097-993e-dc384d831db8'
    unregistered_machine_id = 'aaaabbbb-cccc-dddd-eeee-ffffaaaabbbb'

    @pytest.fixture(scope="class")
    def insights_inventory(self, request, class_factories, modified_ansible_adhoc, is_docker):
        inventory = class_factories.inventory()
        for name in (
                'registered_host', 'unregistered_host', 'no_system_id_host'):
            class_factories.host(name=name, inventory=inventory)

        modified_ansible_adhoc().tower.file(path='/etc/redhat-access-insights', state="directory")
        request.addfinalizer(lambda: modified_ansible_adhoc().tower.file(path='/etc/redhat-access-insights', state="absent"))

        project = class_factories.project(scm_url="https://github.com/ansible/awx-facts-playbooks", wait=True)
        jt = class_factories.job_template(project=project, inventory=inventory, playbook='scan_facts.yml',
                                             use_fact_cache=True, limit="registered_host")

        # update registered host with registered machine ID
        result = modified_ansible_adhoc().tower.shell('echo -n {0} > /etc/redhat-access-insights/machine-id'.format(self.registered_machine_id))
        result = result.values()[0]
        assert result['rc'] == 0, result['stderr']
        jt.launch().wait_until_completed().assert_successful()

        # update unregistered host with unregistered machine ID
        jt.limit = "unregistered_host"
        result = modified_ansible_adhoc().tower.shell('echo -n {0} > /etc/redhat-access-insights/machine-id'.format(self.unregistered_machine_id))
        result = result.values()[0]
        assert result['rc'] == 0, result['stderr']
        jt.launch().wait_until_completed().assert_successful()

        return inventory

    def test_default_host_machine_id(self, factories):
        """Verify that a normal host has no machine ID."""
        host = factories.host()
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

    def test_insights_no_system_id(self, skip_if_cluster, insights_inventory):
        """insights_system_id should be None if the host does not have it."""
        no_system_id_host = insights_inventory.related.hosts.get(name='no_system_id_host').results.pop()
        assert no_system_id_host.get().insights_system_id is None

    def test_inventory_with_insights_credential(self, skip_if_cluster, factories, insights_inventory):
        """Verify that various inventory fields update for our Insights credential."""
        assert not insights_inventory.insights_credential
        assert not insights_inventory.summary_fields.get('insights_credential')

        credential = factories.credential(kind='insights')
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


    @pytest.mark.github('https://github.com/ansible/tower-qa/issues/4487', skip=True)
    def test_access_insights_with_valid_credential_and_registered_host(self, skip_if_cluster, factories, insights_inventory):
        """Verify that attempts to access Insights from a registered host with a valid Insights credential succeed."""
        credential = factories.credential(kind='insights')
        insights_inventory.insights_credential = credential.id
        host = insights_inventory.related.hosts.get(name="registered_host").results.pop()

        insights_content = host.related.insights.get().insights_content
        assert 'last_check_in' in insights_content
        assert 'platform_id' in insights_content
        assert insights_content['platform_id'] == '4182feb1-3711-473b-8d53-e5387d0d20d4'
        assert 'reports' in insights_content
        for report in insights_content['reports']:
            assert 'maintenance_actions' in report
            assert 'rule' in report
            assert set(report['rule'].keys()) == {
                'category',
                'description',
                'severity',
                'summary',
            }

    def test_access_insights_with_valid_credential_and_unregistered_host(self, skip_if_cluster, factories, insights_inventory):
        """Verify that attempts to access Insights from an unregistered host with a valid Insights credential
        raises a 404.
        """
        credential = factories.credential(kind='insights')
        insights_inventory.insights_credential = credential.id
        host = insights_inventory.related.hosts.get(name="unregistered_host").results.pop()

        with pytest.raises(exc.NotFound) as e:
            host.related.insights.get()
        assert e.value[1]['error'] == f'Could not translate Insights system ID {self.unregistered_machine_id} into an Insights platform ID.'

    def test_access_insights_with_valid_credential_and_no_system_id_host(self, skip_if_cluster, factories, insights_inventory):
        """Verify that attempts to access Insights from a host with no system
        id with a valid Insights credential raises a 502.
        """
        credential = factories.credential(kind='insights')
        insights_inventory.insights_credential = credential.id
        host = insights_inventory.related.hosts.get(name="no_system_id_host").results.pop()

        with pytest.raises(exc.NotFound) as e:
            host.related.insights.get()
        assert e.value[1]['error'] == 'This host is not recognized as an Insights host.'

    def test_access_insights_with_invalid_credential(self, skip_if_cluster, factories, insights_inventory):
        """Verify that attempts to access Insights with a bad Insights credential raise a 502."""
        credential = factories.credential(kind='insights', inputs=dict(username="fake", password="fake"))
        insights_inventory.insights_credential = credential.id
        hosts = insights_inventory.related.hosts.get().results

        for host in hosts:
            if host.insights_system_id is None:
                # If the insights_system_id fact is not present, then the host
                # is not an Insights hosts and therefore the /insights URL will
                # state that with a 404 response.
                with pytest.raises(exc.NotFound) as e:
                    host.related.insights.get()
                assert e.value[1]['error'] == 'This host is not recognized as an Insights host.'
            else:
                # If the insights_system_id fact is present, then Tower will
                # try to make a request to Insights and since the credentials
                # are invalid it will fail with a proper error message.
                with pytest.raises(exc.BadGateway) as e:
                    host.related.insights.get()
                assert e.value[1]['error'] == 'Unauthorized access. Please check your Insights Credential username and password.'

    def test_insights_project_no_credential(self, factories):
        """Verify that attempts to create an Insights project without an Insights credential raise a 400."""
        with pytest.raises(exc.BadRequest) as e:
            factories.project(scm_type='insights', credential=None)
        assert e.value[1] == {'credential': ['Insights Credential is required for an Insights Project.']}

    def test_insights_project_with_valid_credential(self, factories):
        """Verify the creation of an Insights project with a valid Insights credential and its
        auto-spawned project update.
        """
        insights_cred = factories.credential(kind='insights')
        project = factories.project(scm_type='insights', credential=insights_cred, wait=True)
        update = project.related.last_update.get()

        project.assert_successful()
        assert project.credential == insights_cred.id
        assert not project.scm_branch
        assert project.scm_type == 'insights'
        assert project.scm_url == 'https://cloud.redhat.com'
        assert project.scm_revision

        update.assert_successful()
        assert not update.job_explanation
        assert update.project == project.id

        assert update.credential == insights_cred.id
        assert update.job_type == 'check'
        assert update.launch_type == 'manual'
        assert update.scm_type == 'insights'
        assert update.scm_url == 'https://cloud.redhat.com'
        assert not update.scm_branch

    def test_insights_project_with_invalid_credential(self, factories):
        """Verify the creation of an Insights project with an invalid Insights credential and its
        auto-spawned project update.
        """
        insights_cred = factories.credential(kind='insights', inputs=dict(username="fake", password="fake"))
        project = factories.project(scm_type='insights', credential=insights_cred, wait=True)
        update = project.related.last_update.get()

        assert project.status == "failed"
        assert project.last_job_failed
        assert project.last_update_failed
        assert update.status == "failed"
        assert update.failed is True

    def test_insights_project_directory(self, skip_if_cluster, factories, v2, ansible_runner):
        """Verify created project directory."""
        insights_cred = factories.credential(kind='insights')
        project = factories.project(scm_type='insights', credential=insights_cred, wait=True)
        directory_path = os.path.join(v2.config.get().project_base_dir, project.local_path)

        # assert project directory created
        contacted = ansible_runner.stat(path=directory_path)
        stat = [
            result['stat'] for result in contacted.values()
            if 'stat' in result
        ]
        assert len(stat) == 1, contacted.values()
        assert stat[0]['exists'], f'Directory not found under {directory_path}.'

    def test_matching_insights_revision(self, skip_if_cluster, factories, v2, ansible_runner):
        """Verify that our revision tag matches between the following:
        * Project details.
        * Project update standard output.
        * .verison under our project directory.
        """
        insights_cred = factories.credential(kind='insights')
        project = factories.project(scm_type='insights', credential=insights_cred, wait=True)
        update = project.related.last_update.get()

        # Ansible stdout output will escape some characters on the revision and
        # therefore we should do the same in order to assert with the stdout.
        scm_revision = project.scm_revision.translate(str.maketrans({
            '"': '\\\\"',
        }))
        assert scm_revision in update.result_stdout

        # verify contents of .version file
        version_path = os.path.join(v2.config.get().project_base_dir, project.local_path, ".version")
        contacted = ansible_runner.shell('cat {0}'.format(version_path))
        result = [
            value for value in contacted.values()
            if 'stdout' in value
        ]
        assert len(result) == 1, contacted.values()
        assert result[0]['stdout'] == project.scm_revision


@pytest.mark.usefixtures('authtoken')
class TestInsightsAnalytics(APITest):

    EXPECTED_FILES = {
        'config.json',
        'counts.json',
        'cred_type_counts.json',
        'events_table.csv',
        'instance_info.json',
        'inventory_counts.json',
        'job_counts.json',
        'job_instance_counts.json',
        'manifest.json',
        'org_counts.json',
        'projects_by_scm_type.json',
        'query_info.json',
        'unified_job_template_table.csv',
        'unified_jobs_table.csv',
    }

    def toggle_analytics(self, update_setting_pg, v2, state=False):
        system_settings = v2.settings.get().get_endpoint('system')
        payload = {'INSIGHTS_TRACKING_STATE': state}
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

    def read_json_file(self, path, ansible_runner):
        content = ansible_runner.slurp(path=path).values()[0]['content']
        return json.loads(base64.b64decode(content))

    def read_csv_file(self, path, ansible_runner):
        csv_file = ansible_runner.fetch(src=path, dest='/tmp/fetched').values()[0]['dest']
        rows = []
        for row in csv.reader(open(csv_file, 'r', encoding='utf8'), delimiter=','):
            rows.append(row)
        return rows

    def collect_stats(self, keys, ansible_runner):
        tempdir, files = self.gather_analytics(ansible_runner)
        stats = {}
        for k in keys:
            filename_split = k.split('.')
            path = '{}/{}'.format(tempdir, k)
            if filename_split[1] == 'json':
                stats[filename_split[0]] = self.read_json_file(path, ansible_runner)
            elif filename_split[1] == 'csv':
                stats[filename_split[0]] = self.read_csv_file(path, ansible_runner)
        return stats

    @pytest.mark.ansible(host_pattern='tower[0]')
    def test_awxmanage_gather_analytics_generates_valid_tar(self, ansible_runner, skip_if_openshift, analytics_enabled):
        tempdir, files = self.gather_analytics(ansible_runner)
        generated_files = {Path(f).name for f in files}
        assert self.EXPECTED_FILES == generated_files, (
            'gather_analytics did not generate the expected files.\n\n'
            'Extra files: {}\n\n'
            'Missing files: {}\n\n'
            .format(
                ', '.join(generated_files - self.EXPECTED_FILES) or 'none',
                ', '.join(self.EXPECTED_FILES - generated_files) or 'none',
            )
        )

        for f in files:
            filepath = Path(f)
            if filepath.suffix == '.json':
                content = self.read_json_file(filepath.as_posix(), ansible_runner)
                assert isinstance(content, dict)
            elif filepath.suffix == '.csv':
                content = self.read_csv_file(filepath.as_posix(), ansible_runner)
                assert isinstance(content, list)

    @pytest.mark.ansible(host_pattern='tower[0]')
    def test_awxmanage_gather_analytics_manifest(self, ansible_runner, skip_if_openshift, analytics_enabled):
        """Check if the manifest is providing the expected reports versions."""
        manifest = self.collect_stats(['manifest.json'], ansible_runner).get('manifest', {})
        expected_files = self.EXPECTED_FILES.copy()
        # manifest.json don't have a version, it only provide the version
        # information for the other report files
        expected_files.remove('manifest.json')
        generated_files = set(manifest.keys())
        assert expected_files == generated_files, (
            'manifest.json did not provide the version info for expected files.\n\n'
            'Extra files: {}\n\n'
            'Missing files: {}\n\n'
            .format(
                ', '.join(generated_files - expected_files) or 'none',
                ', '.join(expected_files - generated_files) or 'none',
            )
        )

        assert manifest == {
            'config.json': '1.0',
            'counts.json': '1.0',
            'cred_type_counts.json': '1.0',
            'events_table.csv': '1.0',
            'instance_info.json': '1.0',
            'inventory_counts.json': '1.0',
            'job_counts.json': '1.0',
            'job_instance_counts.json': '1.0',
            'org_counts.json': '1.0',
            'projects_by_scm_type.json': '1.0',
            'query_info.json': '1.0',
            'unified_job_template_table.csv': '1.0',
            'unified_jobs_table.csv': '1.0',
        }

    @pytest.mark.ansible(host_pattern='tower[0]')
    def test_awxmanage_gather_analytics_query_info(self, ansible_runner, skip_if_openshift, analytics_enabled):
        previous = self.collect_stats(['query_info.json'], ansible_runner).get('query_info', {})
        current = self.collect_stats(['query_info.json'], ansible_runner).get('query_info', {})

        # Gather analytics was called manually and not by a recurring task
        assert previous['collection_type'] == 'manual'
        assert current['collection_type'] == 'manual'

        expected_date_format = '%Y-%m-%d %H:%M:%S.%f%z'
        for key in ('current_time', 'last_run'):
            previous[key] = previous[key].replace('+00:00', '+0000')
            previous[key] = datetime.strptime(previous[key], expected_date_format)

            current[key] = current[key].replace('+00:00', '+0000')
            current[key] = datetime.strptime(current[key], expected_date_format)

        assert previous['current_time'] > previous['last_run']
        assert current['current_time'] > current['last_run']

        assert current['current_time'] > previous['current_time'], (
            "The current run's current_time value must be greater than the current_time value of the previous run"
        )

        # last_run is updated only when we push the data to insights. On this
        # test we are just running locally without pushing any data, so the
        # last_run information must be the same.
        assert current['last_run'] == previous['last_run'], (
            'The last_run  should be the same since no data is being pushed '
            'to insights. If this assertion fail, make sure that an async '
            'task have not pushed data to insights in between the '
            'gather_analytics calls.'
        )

    @pytest.mark.ansible(host_pattern='tower[0]')
    def test_awxmanage_gather_analytics_project_count_incremented(self, ansible_runner, factories, skip_if_openshift, analytics_enabled):
        counts = self.collect_stats(['counts.json'], ansible_runner)
        projects_before = counts['counts']['project']
        factories.project()
        counts = self.collect_stats(['counts.json'], ansible_runner)
        projects_after = counts['counts']['project']

        assert projects_after == projects_before + 1

    @pytest.mark.ansible(host_pattern='tower[0]')
    def test_awxmanage_gather_analytics_job_status_manual_launch_count_incremented(self, ansible_runner, factories, skip_if_openshift, analytics_enabled):
        jt = factories.job_template()
        counts = self.collect_stats(['job_counts.json'], ansible_runner)
        manual_launch_before = counts['job_counts']['launch_type']['manual']

        jt.launch()
        counts = self.collect_stats(['job_counts.json'], ansible_runner)
        manual_launch_after = counts['job_counts']['launch_type']['manual']

        assert manual_launch_after == manual_launch_before + 1

    @pytest.mark.ansible(host_pattern='tower[0]')
    def test_awxmanage_gather_analytics_inventory_counts_incremented(self, ansible_runner, factories, skip_if_openshift, analytics_enabled):
        counts = self.collect_stats(['counts.json'], ansible_runner)
        inventory_types_before = counts['counts']['inventories']
        [factories.inventory() for _ in range(2)]
        factories.inventory(kind='smart', host_filter='search=foo')
        counts = self.collect_stats(['counts.json'], ansible_runner)
        inventory_types_after = counts['counts']['inventories']

        assert inventory_types_after['normal'] == inventory_types_before['normal'] + 2
        assert inventory_types_after['smart'] == inventory_types_before['smart'] + 1

    @pytest.mark.ansible(host_pattern='tower[0]')
    def test_awxmanage_gather_analytics_inventory_host_counts_incremented(self, ansible_runner, factories, skip_if_openshift, analytics_enabled):
        org = factories.organization()
        empty_inventory = factories.inventory(organization=org)
        two_host_inventory = factories.inventory(organization=org)
        smart_inventory = factories.inventory(kind='smart', host_filter='search=smart-test', organization=org)
        inventory_counts_before = self.collect_stats(['inventory_counts.json'], ansible_runner)
        [factories.host(name="smart-test_{0}".format(i), inventory=two_host_inventory) for i in range(2)]
        factories.host(organization=org)
        inventory_counts_after = self.collect_stats(['inventory_counts.json'], ansible_runner)

        assert inventory_counts_after['inventory_counts'][str(empty_inventory.id)]['hosts'] == inventory_counts_before['inventory_counts'][str(empty_inventory.id)]['hosts'] == 0
        assert inventory_counts_after['inventory_counts'][str(two_host_inventory.id)]['hosts'] == inventory_counts_before['inventory_counts'][str(two_host_inventory.id)]['hosts'] + 2 == 2
        assert inventory_counts_after['inventory_counts'][str(smart_inventory.id)]['num_hosts'] == inventory_counts_before['inventory_counts'][str(smart_inventory.id)]['num_hosts'] + 2 == 2

    @pytest.mark.ansible(host_pattern='tower[0]')
    def test_awxmanage_gather_analytics_job_status_counts_incremented(self, ansible_runner, factories, skip_if_openshift, analytics_enabled):
        jt = factories.job_template()
        jt.ds.project.patch(scm_update_on_launch=False)
        jt.ds.project.update().wait_until_completed()
        counts = self.collect_stats(['job_instance_counts.json'], ansible_runner)
        sync_before = 0
        success_before = 0
        for h in counts['job_instance_counts'].keys():
            sync_before += counts['job_instance_counts'][h]['status'].get('sync', 0)
            success_before += counts['job_instance_counts'][h]['status'].get('successful', 0)
        jt.launch().wait_until_completed()
        counts = self.collect_stats(['job_instance_counts.json'], ansible_runner)
        sync_after = 0
        success_after = 0
        for h in counts['job_instance_counts'].keys():
            sync_after += counts['job_instance_counts'][h]['status'].get('sync', 0)
            success_after += counts['job_instance_counts'][h]['status'].get('successful', 0)
        assert success_after == success_before + 1
        assert sync_after == sync_before

    @pytest.mark.ansible(host_pattern='tower[0]')
    def test_awxmanage_gather_analytics_events_table_accurate(self, ansible_runner, factories, skip_if_openshift, analytics_enabled):
        # Gather analytics to set last_run
        self.gather_analytics(ansible_runner)
        jt = factories.job_template()
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
        if 'uuid' in csv_uuids:
            csv_uuids.remove('uuid')
        for e in events:
            event_uuids.add(e['uuid'])
        assert event_uuids.issubset(csv_uuids)

    @pytest.mark.ansible(host_pattern='tower[0]')
    def test_awxmanage_gather_analytics_unified_jobs_table_accurate(self, ansible_runner, factories, skip_if_openshift, analytics_enabled):
        jt = factories.job_template()
        job = jt.launch().wait_until_completed()
        stats = self.collect_stats(['unified_jobs_table.csv'], ansible_runner)

        assert sorted(stats['unified_jobs_table'][0]) == sorted([
            'cancel_flag',
            'controller_node',
            'created',
            'elapsed',
            'execution_node',
            'failed',
            'finished',
            'id',
            'instance_group_id',
            'job_explanation',
            'launch_type',
            'model',
            'name',
            'organization_id',
            'organization_name',
            'polymorphic_ctype_id',
            'schedule_id',
            'started',
            'status',
            'unified_job_template_id',
        ])

        org = jt.related.project.get().related.organization.get()
        entries = [
            row for row in stats['unified_jobs_table']
            if row[0] == f'{job.id}'
        ]
        assert len(entries) == 1, entries

        report_entry = {
            k: v for k, v in zip(stats['unified_jobs_table'][0], entries[0])
            if k != 'polymorphic_ctype_id'
        }
        expected = {
            'cancel_flag': 't' if job.status == 'canceled' else 'f',
            'controller_node': job.controller_node,
            'created': job.created,
            'elapsed': f'{job.elapsed:.3f}',
            'execution_node': job.execution_node,
            'failed': 't' if job.failed else 'f',
            'finished': job.finished,
            'id': f'{job.id}',
            'instance_group_id': f'{job.instance_group}',
            'job_explanation': '',
            'launch_type': job.launch_type,
            'model': job.type,
            'name': job.name,
            'organization_id': f'{org.id}',
            'organization_name': f'{org.name}',
            'schedule_id': '',
            'started': job.started,
            'status': f'{job.status}',
            'unified_job_template_id': f'{jt.id}',
        }
        for k in ('created', 'finished', 'started'):
            report_entry[k] = datetime.strptime(report_entry[k], '%Y-%m-%d %H:%M:%S.%f+00'),
            expected[k] = datetime.strptime(expected[k], '%Y-%m-%dt%H:%M:%S.%fZ'),

        assert report_entry == expected, (
            'The report, generated by Tower, does not match the expected data '
            'type or format.'
        )

    @pytest.mark.ansible(host_pattern='tower[0]')
    def test_awxmanage_gather_analytics_unicode(self, ansible_runner, factories, skip_if_openshift, analytics_enabled):
        org = factories.organization(name='🤬🥔')
        project = factories.project(name='🖖', organization=org)
        project.update().wait_until_completed()
        inventory = factories.inventory(name='🤔')
        jt = factories.job_template(
            name='😜',
            playbook='utf-8-䉪ቒ칸ⱷꯔ噂폄蔆㪗輥.yml',
            project=project,  # this will provide the org name on the report entry
        )
        jt.launch().wait_until_completed()
        counts = self.collect_stats(['inventory_counts.json',
                                     'org_counts.json',
                                     'events_table.csv',
                                     'unified_jobs_table.csv'], ansible_runner)

        assert counts['inventory_counts'][str(inventory.id)]['name'] == '🤔'
        assert counts['org_counts'][str(org.id)]['name'] == '🤬🥔'

        assert 'playbook' in counts['events_table'][0], counts['events_table'][0]
        playbook_col = counts['events_table'][0].index('playbook')
        events_table_entries = [
            row for row in counts['events_table']
            if row[playbook_col] == 'utf-8-䉪ቒ칸ⱷꯔ噂폄蔆㪗輥.yml'
        ]
        assert len(events_table_entries) > 0, (
            'At least one event for the playbook must exist on the events_table'
        )

        organization_name = counts['unified_jobs_table'][0].index('organization_name')
        name = counts['unified_jobs_table'][0].index('name')
        unified_jobs_table_entries = [
            row for row in counts['unified_jobs_table']
            if row[organization_name] == '🤬🥔' and row[name] == '😜'
        ]
        assert len(unified_jobs_table_entries) > 0, (
            'At least one entry for the job template run must exist on the unified_jobs_table'
        )

    @pytest.mark.ansible(become=True, become_user='awx')
    def test_ship_insights_succeeds(self, v2, update_setting_pg, ansible_runner, analytics_enabled):
        error_strings = ['Upload failed',
                        'Automation Analytics TAR not found',
                        'A valid license was not found:',
                        'Invalid License provided, or No License Provided',
                        'Could not generate metric',
                        'Could not generate manifest.json',
                        'Could not copy tables',
                        'is not set',
                        'Automation Analytics not enabled'
                        ]
        system_settings = v2.settings.get().get_endpoint('system')
        payload = {'REDHAT_USERNAME': config.credentials.insights.username,
                   'REDHAT_PASSWORD': config.credentials.insights.password,
                   'AUTOMATION_ANALYTICS_URL': 'https://cloud.redhat.com/api/ingress/v1/upload'
                  }
        update_setting_pg(system_settings, payload)
        result = ansible_runner.shell('awx-manage gather_analytics --ship', chdir='/').values()[0]['stderr_lines']
        for e in error_strings:
            assert not any(e.lower() in r.lower() for r in result), result

    # This "test" is temporary, it is being used by @bender to generate data for a summit demo
    # Please contact @bender if you want to remove it
    @pytest.mark.ansible(host_pattern='tower[0]')
    def test_awxmanage_gather_analytics_ship_insights_tar_to_s3(self, ansible_runner, skip_if_openshift, analytics_enabled):
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

    def test_awxmanage_gather_analytics_system_uuid_same_across_cluster(self, ansible_runner, skip_if_not_cluster, skip_if_openshift, analytics_enabled):
        uuid_result = ansible_runner.shell('echo "from django.conf import settings; print(settings.INSTALL_UUID)" | awx-manage shell')
        node_uuids = set()
        for u in uuid_result.values():
            node_uuids.add(u['stdout'])
        assert len(node_uuids) == 1
        assert "00000000-0000-0000-0000-000000000000" not in node_uuids
