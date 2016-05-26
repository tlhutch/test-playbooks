import pytest
from tests.api import Base_Api_Test


@pytest.mark.api
@pytest.mark.skip_selenium
@pytest.mark.destructive
class Test_Tower_Prepopulation(Base_Api_Test):

    pytestmark = pytest.mark.usefixtures('authtoken', 'install_license_unlimited')

    def test_success(self, default_organization):
        '''
        Tests Tower demo objects.
        '''
        # check for demo credential
        admin_user_pg = default_organization.get_related('created_by', username='admin')
        assert admin_user_pg.get_related('credentials', name='Demo Credential').count == 1, \
            "'Demo Credential' not found."

        # check for demo inventory and host
        inventories_pg = default_organization.get_related('inventories', name='Demo Inventory')
        assert inventories_pg.count == 1, "'Demo Inventory' not found."
        inventory_pg = inventories_pg.results[0]
        hosts_pg = inventory_pg.get_related('hosts', name='localhost')
        assert hosts_pg.count == 1, "Demo host 'localhost' not found."

        # check demo project
        projects_pg = default_organization.get_related('projects', name='Demo Project')
        assert projects_pg.count == 1, "'Demo Project' not found."
        project_pg = projects_pg.results[0]
        assert project_pg.is_successful, "'Demo Project' unsuccessful - %s." % projects_pg.results[0]

        # check demo job template
        job_templates_pg = inventory_pg.get_related('job_templates', name='Demo Job Template')
        assert job_templates_pg.count == 1, "'Demo Job Template' not found."
        job_template_pg = job_templates_pg.results[0]
        assert job_template_pg.playbook == 'hello_world.yml', \
            "JT created with incorrect playbook. Expected 'hello_world.yml', got %s." % job_templates_pg.playbook

        job_pg = job_template_pg.launch().wait_until_completed()
        assert job_pg.is_successful, 'Job unsuccessful - %s.' % job_pg
