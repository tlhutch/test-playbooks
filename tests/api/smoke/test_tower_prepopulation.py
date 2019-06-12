import pytest
from tests.api import APITest


class Test_Tower_Prepopulation(APITest):

    pytestmark = pytest.mark.usefixtures('authtoken', 'install_enterprise_license_unlimited')

    @pytest.mark.yolo
    def test_success(self, default_organization):
        """Tests Tower demo objects."""
        # check demo organization
        assert default_organization.custom_virtualenv is None

        # check for demo credential
        admin_user = default_organization.get_related('created_by', username='admin')
        credentials = admin_user.get_related('credentials', name='Demo Credential')
        assert credentials.count == 1, "'Demo Credential' not found."
        credential = credentials.results.pop()

        # check for demo inventory and host
        inventories = default_organization.get_related('inventories', name='Demo Inventory')
        assert inventories.count == 1, "'Demo Inventory' not found."
        inventory = inventories.results[0]
        hosts = inventory.get_related('hosts', name='localhost')
        assert hosts.count == 1, "Demo host 'localhost' not found."

        # check demo project
        projects = default_organization.get_related('projects', name='Demo Project')
        assert projects.count == 1, "'Demo Project' not found."
        project = projects.results[0]
        assert project.scm_update_on_launch
        assert project.custom_virtualenv is None
        assert project.organization == default_organization.id

        job_templates = inventory.get_related('job_templates', name='Demo Job Template')
        assert job_templates.count == 1, "'Demo Job Template' not found."
        job_template = job_templates.results[0]
        if job_template.last_job_run:
            project.assert_successful()
        else:
            assert project.status == "never updated", "Unexpected project.status - %s." % projects
        assert job_template.custom_virtualenv is None

        # check demo job template
        assert job_template.playbook == 'hello_world.yml', \
            "JT created with incorrect playbook. Expected 'hello_world.yml', got %s." % job_templates.playbook
        assert job_template.project == project.id
        assert job_template.inventory == inventory.id
        assert [c.id for c in job_template.related.credentials.get().results] == [credential.id]
        job = job_template.launch().wait_until_completed()
        job.assert_successful()
