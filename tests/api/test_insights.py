import os
import base64
import json

from towerkit import config
import towerkit.exceptions as exc
import pytest

from tests.api import APITest


@pytest.fixture(scope="class")
def register_rhn_and_insights(ansible_runner_class):
    rhn_username = config.credentials.insights.username
    rhn_password = config.credentials.insights.password
    ansible_runner_class.redhat_subscription(state='present',
                                             username=rhn_username,
                                             password=rhn_password,
                                             auto_attach=True)

    ansible_runner_class.yum(state='installed', name='insights-client')
    ansible_runner_class.shell('insights-client --register')
    yield
    ansible_runner_class.shell('insights-client --unregister')
    ansible_runner_class.redhat_subscription(state='absent',
                                             username=rhn_username,
                                             password=rhn_password)
    ansible_runner_class.yum(state='absent', name='insights-client')


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
@pytest.mark.usefixtures('authtoken', 'install_enterprise_license_unlimited', 'skip_if_not_rhel', 'register_rhn_and_insights')
class TestInsightsAnalytics(APITest):

    def gather_analytics(self, ansible_runner):
        result = ansible_runner.shell('awx-manage gather_analytics').values()[0]
        analytics_payload = [l for l in result['stderr_lines'] if "tar.gz" in l][0]
        tempdir = ansible_runner.tempfile(state='directory', suffix='insights_test').values()[0]['path']
        ansible_runner.unarchive(src=analytics_payload, dest=tempdir, remote_src=True).values()[0]
        files = [f['path'] for f in ansible_runner.find(paths=tempdir).values()[0]['files']]
        return tempdir, files

    def test_awxmanage_gather_analytics_generates_valid_tar(self, ansible_runner):
        tempdir, files = self.gather_analytics(ansible_runner)
        expected_files = ['config.json', 'counts.json', 'projects_by_scm_type.json']
        for f in expected_files:
            filepath = '{}/{}'.format(tempdir, f)
            assert filepath in files
            content = ansible_runner.slurp(path=filepath).values()[0]['content']
            try:
                json_dict = json.loads(base64.b64decode(content))
                assert type(json_dict) == dict
            except:
                raise Exception('{} is not valid json'.format(filepath))
