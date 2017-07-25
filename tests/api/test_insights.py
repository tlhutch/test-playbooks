import os

import towerkit.exceptions as exc
import pytest

from tests.api import Base_Api_Test


@pytest.mark.api
@pytest.mark.destructive
@pytest.mark.skip_selenium
class TestInsights(Base_Api_Test):

    pytestmark = pytest.mark.usefixtures('authtoken', 'install_enterprise_license_unlimited')
    registered_machine_id = "84baf1a3-eee5-4f92-b5ee-42609e89a2cd"
    unregistered_machine_id = "aaaabbbb-cccc-dddd-eeee-ffffgggghhhh"

    @pytest.fixture(scope="class")
    def insights_inventory(self, request, class_factories, ansible_runner):
        inventory = class_factories.v2_inventory()
        for name in ('registered_host', 'unregistered_host'):
            class_factories.v2_host(name=name, inventory=inventory)

        ansible_runner.file(path='/etc/redhat-access-insights', state="directory")
        request.addfinalizer(lambda: ansible_runner.file(path='/etc/redhat-access-insights', state="absent"))

        scm_cred, ssh_cred = [class_factories.v2_credential(kind=kind) for kind in ('scm', 'ssh')]
        project = class_factories.v2_project(scm_url="git@github.com:ansible/tower-fact-modules.git",
                                             credential=scm_cred, wait=True)
        jt = class_factories.v2_job_template(project=project, inventory=inventory, playbook='scan_facts.yml',
                                             credential=ssh_cred, use_fact_cache=True, limit="registered_host")

        # update registered host with registered machine ID
        ansible_runner.shell('echo -n {0} > /etc/redhat-access-insights/machine-id'.format(self.registered_machine_id))
        assert jt.launch().wait_until_completed().is_successful

        # update unregistered host with unregistered machine ID
        jt.limit = "unregistered_host"
        ansible_runner.shell('echo -n {0} > /etc/redhat-access-insights/machine-id'.format(self.unregistered_machine_id))
        assert jt.launch().wait_until_completed().is_successful

        return inventory

    def test_default_host_machine_id(self, factories):
        """Verify that a normal host has no machine ID."""
        host = factories.v2_host()
        assert not host.insights_system_id

    def test_insights_host_machine_id(self, insights_inventory):
        """Verify that Insights hosts have machine IDs."""
        registered_host = insights_inventory.related.hosts.get(name='registered_host').results.pop()
        unregistered_host = insights_inventory.related.hosts.get(name='unregistered_host').results.pop()
        assert registered_host.insights_system_id == self.registered_machine_id
        assert unregistered_host.insights_system_id == self.unregistered_machine_id

    def test_inventory_with_insights_credential(self, factories, insights_inventory):
        """Verify that various inventory fields update for our Insights credential."""
        assert not insights_inventory.insights_credential
        assert not insights_inventory.summary_fields.get('insights_credential')

        credential = factories.v2_credential(kind='insights')
        insights_inventory.insights_credential = credential.id

        assert insights_inventory.insights_credential == credential.id
        assert insights_inventory.summary_fields.insights_credential == dict(id=credential.id,
                                                                             name=credential.name,
                                                                             description=credential.description)

    def test_access_insights_with_no_credential(self, insights_inventory):
        """Verify that attempts to access Insights without a credential raises a 404."""
        hosts = insights_inventory.related.hosts.get().results
        for host in hosts:
            with pytest.raises(exc.NotFound) as e:
                host.related.insights.get()
        assert e.value[1] == {'error': 'The Insights Credential for "{0}" was not found.'.format(insights_inventory.name)}

    def test_access_insights_with_credential_and_registered_host(self, factories, insights_inventory):
        """Verify that attempts to access Insights from a registered host with an Insights credential succeed."""
        credential = factories.v2_credential(kind='insights')
        insights_inventory.insights_credential = credential.id
        host = insights_inventory.related.hosts.get(name="registered_host").results.pop()

        content = host.related.insights.get().insights_content
        assert content.reports
        assert content.product == 'rhel'
        assert content.hostname == 'ip-10-180-34-241.ec2.internal' # non-existent instance
        assert content.system_id == self.registered_machine_id
        assert content.type == 'machine'

    @pytest.mark.skip(reason="Behavior TBD: https://github.com/ansible/ansible-tower/issues/6916.")
    def test_access_insights_with_credential_and_unregistered_host(self, factories, insights_inventory):
        """Verify that attempts to access Insights from an unregistered host with an Insights credential
        raises a 500.
        """
        credential = factories.v2_credential(kind='insights')
        insights_inventory.insights_credential = credential.id
        host = insights_inventory.related.hosts.get(name="unregistered_host").results.pop()

        with pytest.raises(exc.InternalServerError) as e:
            host.related.insights.get().insights_content
        assert "Failed to gather reports and maintenance plans from Insights API" in e.value[1]['error']

    def test_insights_project_no_credential(self, factories):
        """Verify that attempts to create an Insights project without an Insights credential raise a 400."""
        with pytest.raises(exc.BadRequest) as e:
            factories.v2_project(scm_type='insights', credential=None)
        assert e.value[1] == {'credential': ['Insights Credential is required for an Insights Project.']}

    def test_insights_project_with_credential(self, factories):
        """Verify the creation of an Insights project with an Insights credential and its
        auto-spawned project update.
        """
        insights_cred = factories.v2_credential(kind='insights')
        project = factories.v2_project(scm_type='insights', credential=insights_cred, wait=True)
        update = project.related.last_update.get()

        assert project.is_successful
        assert project.credential == insights_cred.id
        assert not project.scm_branch
        assert project.scm_type == 'insights'
        assert project.scm_url == 'https://access.redhat.com'
        assert project.scm_revision

        assert update.is_successful
        assert not update.job_explanation
        assert update.project == project.id
        assert update.credential == insights_cred.id
        assert update.job_type == 'check'
        assert update.launch_type == 'manual'
        assert update.scm_type == 'insights'
        assert update.scm_url == 'https://access.redhat.com'
        assert not update.scm_branch

    def test_insights_project_contents(self, factories, v2, ansible_runner):
        """Verify created project directory and playbook. Note: chrwang-test-28315.yml is an Insights
        maintenance plan (playbook) stored under our test Insights account.
        """
        insights_cred = factories.v2_credential(kind='insights')
        project = factories.v2_project(scm_type='insights', credential=insights_cred, wait=True)
        playbook_path = os.path.join(v2.config.get().project_base_dir, project.local_path, "chrwang-test-28315.yml")

        # assert playbook created
        contacted = ansible_runner.stat(path=playbook_path)
        for result in contacted.values():
            assert result['stat']['exists'], "Playbook not found under {0}.".format(playbook_path)

    def test_matching_insights_revision(self, factories, v2, ansible_runner):
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
        assert contacted.values()[0]['stdout'] == project.scm_revision
