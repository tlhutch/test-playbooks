import towerkit.exceptions as exc
import pytest

from tests.api import Base_Api_Test


@pytest.mark.api
@pytest.mark.destructive
@pytest.mark.ha_tower
@pytest.mark.skip_selenium
class TestInsights(Base_Api_Test):

    pytestmark = pytest.mark.usefixtures('authtoken', 'insights_inventory')
    matched_machine_id = "84baf1a3-eee5-4f92-b5ee-42609e89a2cd"
    unmatched_machine_id = "aaaabbbb-cccc-dddd-eeee-ffffgggghhhh"

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

        # update registered host with matched machine ID
        ansible_runner.shell('echo -n {0} > /etc/redhat-access-insights/machine-id'.format(self.matched_machine_id))
        assert jt.launch().wait_until_completed().is_successful

        # update unregistered host with unmatched machine ID
        jt.limit = "unregistered_host"
        ansible_runner.shell('echo -n {0} > /etc/redhat-access-insights/machine-id'.format(self.unmatched_machine_id))
        assert jt.launch().wait_until_completed().is_successful

        return inventory

    def test_default_host_machine_id(self, factories):
        """Verify that a normal host has no machine ID."""
        host = factories.v2_host()
        assert not host.insights_system_id

    def test_insights_host_machine_id(self, insights_inventory):
        """Verify that Insights hosts have machine IDs."""
        matched_host = insights_inventory.related.hosts.get(name='registered_host').results.pop()
        unmatched_host = insights_inventory.related.hosts.get(name='unregistered_host').results.pop()
        assert matched_host.insights_system_id == self.matched_machine_id
        assert unmatched_host.insights_system_id == self.unmatched_machine_id

    def test_access_insights_with_no_credential(self, insights_inventory):
        """Verify that attempts to access Insights without a credential raises a 404."""
        hosts = insights_inventory.related.hosts.get().results
        for host in hosts:
            with pytest.raises(exc.NotFound) as e:
                host.related.insights.get()
        assert e.value[1] == {'error': 'The Insights Credential for "{0}" was not found.'.format(insights_inventory.name)}

    def test_access_insights_with_credential_and_matched_host(self, factories, insights_inventory):
        """Verify that attempts to access Insights from a matching host with an Insights credential succeed."""
        credential = factories.v2_credential(kind='insights')
        insights_inventory.insights_credential = credential.id
        host = insights_inventory.related.hosts.get(name="registered_host").results.pop()

        content = host.related.insights.get().insights_content
        assert content.reports
        assert content.product == 'rhel'
        assert content.hostname == 'ip-10-156-20-161.ec2.internal'
        assert content.system_id == '84baf1a3-eee5-4f92-b5ee-42609e89a2cd'
        assert content.type == 'machine'

    # FIXME: fix line length
    def test_access_insights_with_credential_and_unmatched_host(self, factories, insights_inventory):
        """Verify that attempts to access Insights from an unmatched host with an Insights credential
        raises a 500.
        """
        credential = factories.v2_credential(kind='insights')
        insights_inventory.insights_credential = credential.id
        host = insights_inventory.related.hosts.get(name="unregistered_host").results.pop()

        with pytest.raises(exc.InternalServerError) as e:
            host.related.insights.get().insights_content
        assert e.value[1] == {'error': 'Failed to gather reports and maintenance plans from Insights API at URL https://access.redhat.com/r/insights/v3/systems/aaaabbbb-cccc-dddd-eeee-ffffgggghhhh/reports/. Server responded with 404 status code and message {}'}

    def test_insights_project_no_credential(self, factories):
        """Verify that attempts to create an Insights project without an Insights credential raise a 400."""
        with pytest.raises(exc.BadRequest) as e:
            factories.v2_project(scm_type='insights', credential=None)
        assert e.value[1] == {'credential': ['Insights Credential is required for an Insights Project.']}

    # FIXME: audit assertions here
    def test_insights_project_with_credential(self, factories):
        """Verify the creation of an Insights project with an Insights credential and its
        auto-spawned project update.
        """
        insights_cred = factories.v2_credential(kind='insights')
        project = factories.v2_project(scm_type='insights', credential=insights_cred, wait=True)
        update = project.related.last_update.get()

        assert project.is_successful
        assert not project.scm_branch
        assert project.credential == insights_cred.id
        assert project.scm_type == 'insights'
        assert project.scm_url == 'https://access.redhat.com'
        assert project.scm_revision

        assert update.is_successful
        assert not update.scm_branch
        assert not update.job_explanation
        assert update.credential == insights_cred.id
        assert update.job_type == 'check'
        assert update.scm_type == 'insights'
        assert update.scm_url == 'https://access.redhat.com'
        assert update.project == project.id
