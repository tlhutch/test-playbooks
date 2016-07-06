import fauxfactory
import pytest

from common.ui.pages import (ActivityStream, Credentials, Dashboard, Hosts, Inventories, InventoryScripts,
                             JobTemplateSchedules, JobTemplates, Jobs, License, Login, ManageInventory, ManagementJobs,
                             Organizations, ProjectSchedules, Projects, SetupMenu, Teams, Users)

#
# TODO: Decompose this beast into separate modules
#


@pytest.fixture
def total_rows():
    """Return a total number of rows sufficient for all pagination links to be
    displayed on any crud page
    """
    return 120


@pytest.fixture
def ui_login(selenium, base_url):
    return Login(base_url, selenium).open()


@pytest.fixture
def ui_dashboard(
    selenium,
    base_url,
    default_credentials
):
    return Dashboard(base_url, selenium, **default_credentials).open()


@pytest.fixture
def ui_inventories(
    selenium,
    base_url,
    default_credentials
):
    return Inventories(base_url, selenium, **default_credentials).open()


@pytest.fixture
def ui_inventories_add(
    selenium,
    base_url,
    default_credentials
):
    return Inventories(base_url,
                       selenium,
                       index='add',
                       **default_credentials).open()


@pytest.fixture
def ui_inventories_edit(
    inventory,
    selenium,
    base_url,
    default_credentials
):
    return Inventories(base_url,
                       selenium,
                       index=inventory.id,
                       **default_credentials).open()


@pytest.fixture
def ui_inventory_scripts(
    selenium,
    base_url,
    default_credentials
):
    return InventoryScripts(base_url,
                            selenium,
                            **default_credentials).open()


@pytest.fixture
def ui_inventory_scripts_add(
    selenium,
    base_url,
    default_credentials
):
    return InventoryScripts(base_url,
                            selenium,
                            index='add',
                            **default_credentials).open()


@pytest.fixture
def ui_inventory_scripts_edit(
    inventory_script,
    selenium,
    base_url,
    default_credentials
):
    return InventoryScripts(base_url,
                            selenium,
                            index=inventory_script.id,
                            **default_credentials).open()


@pytest.fixture
def ui_job_templates(
    selenium,
    base_url,
    default_credentials
):
    return JobTemplates(base_url,
                        selenium,
                        **default_credentials).open()


@pytest.fixture
def ui_job_templates_add(
    selenium,
    base_url,
    default_credentials
):
    return JobTemplates(base_url,
                        selenium,
                        index='add',
                        **default_credentials).open()


@pytest.fixture
def ui_job_templates_edit(
    authtoken,
    job_template_with_schedule,
    selenium,
    base_url,
    default_credentials
):
    return JobTemplates(base_url,
                        selenium,
                        index=job_template_with_schedule.id,
                        **default_credentials).open()


@pytest.fixture
def ui_job_templates_schedule(
    authtoken,
    job_template_with_schedule,
    selenium,
    base_url,
    default_credentials
):
    return JobTemplateSchedules(base_url,
                                selenium,
                                index=job_template_with_schedule.id,
                                **default_credentials).open()


@pytest.fixture
def ui_projects(
    selenium,
    base_url,
    default_credentials
):
    return Projects(base_url,
                    selenium,
                    **default_credentials).open()


@pytest.fixture
def ui_projects_add(
    selenium,
    base_url,
    default_credentials
):
    return Projects(base_url,
                    selenium,
                    index='add',
                    **default_credentials).open()


@pytest.fixture
def ui_projects_edit(
    project_with_schedule,
    selenium,
    base_url,
    default_credentials
):
    return Projects(base_url,
                    selenium,
                    index=project_with_schedule.id,
                    **default_credentials).open()


@pytest.fixture
def ui_projects_schedule(
    project_with_schedule,
    selenium,
    base_url,
    default_credentials
):
    return ProjectSchedules(base_url,
                            selenium,
                            index=project_with_schedule.id,
                            **default_credentials).open()


@pytest.fixture
def ui_jobs(
    selenium,
    base_url,
    default_credentials
):
    return Jobs(base_url,
                selenium,
                **default_credentials).open()


@pytest.fixture
def ui_users(
    selenium,
    base_url,
    default_credentials
):
    return Users(base_url,
                 selenium,
                 **default_credentials).open()


@pytest.fixture
def ui_users_add(
    selenium,
    base_url,
    default_credentials
):
    return Users(base_url,
                 selenium,
                 index='add',
                 **default_credentials).open()


@pytest.fixture
def ui_users_edit(
    anonymous_user,
    selenium,
    base_url,
    default_credentials
):
    return Users(base_url,
                 selenium,
                 index=anonymous_user.id,
                 **default_credentials).open()


@pytest.fixture
def ui_teams(
    selenium,
    base_url,
    default_credentials
):
    return Teams(base_url,
                 selenium,
                 **default_credentials).open()


@pytest.fixture
def ui_teams_add(
    selenium,
    base_url,
    default_credentials
):
    return Teams(base_url,
                 selenium,
                 index='add',
                 **default_credentials).open()


@pytest.fixture
def ui_teams_edit(
    team,
    selenium,
    base_url,
    default_credentials
):
    return Teams(base_url,
                 selenium,
                 index=team.id,
                 **default_credentials).open()


@pytest.fixture
def ui_organizations(
    authtoken,
    selenium,
    base_url,
    default_credentials
):
    return Organizations(base_url,
                         selenium,
                         **default_credentials).open()


@pytest.fixture
def ui_organizations_add(
    authtoken,
    selenium,
    base_url,
    default_credentials
):
    return Organizations(base_url,
                         selenium,
                         index='add',
                         **default_credentials).open()


@pytest.fixture
def ui_organizations_edit(
    authtoken,
    another_organization,
    selenium,
    base_url,
    default_credentials
):
    return Organizations(base_url,
                         selenium,
                         index=another_organization.id,
                         **default_credentials).open()


@pytest.fixture
def ui_credentials(
    selenium,
    base_url,
    default_credentials
):
    return Credentials(base_url,
                       selenium,
                       **default_credentials).open()


@pytest.fixture
def ui_credentials_edit(
    ssh_credential,
    selenium,
    base_url,
    default_credentials
):
    return Credentials(base_url,
                       selenium,
                       index=ssh_credential.id,
                       **default_credentials).open()


@pytest.fixture
def ui_credentials_add(
    selenium,
    base_url,
    default_credentials
):
    return Credentials(base_url,
                       selenium,
                       index='add',
                       **default_credentials).open()


@pytest.fixture
def ui_hosts(
    selenium,
    base_url,
    default_credentials
):
    return Hosts(base_url,
                 selenium,
                 **default_credentials).open()


@pytest.fixture
def ui_setup(
    selenium,
    base_url,
    default_credentials
):
    return SetupMenu(base_url,
                     selenium,
                     **default_credentials).open()


@pytest.fixture
def ui_manage_inventory(
    request,
    host_local,
    selenium,
    base_url,
    default_credentials
):
    inventory = host_local.get_related('inventory')

    inventory.get_related('groups').post({
        'name': 'ui-group-%s' % fauxfactory.gen_alphanumeric(),
        'description': fauxfactory.gen_utf8(),
        'inventory': inventory.id
    })

    return ManageInventory(base_url,
                           selenium,
                           inventory.id,
                           **default_credentials).open()


@pytest.fixture
def ui_activity_stream(
    selenium,
    base_url,
    default_credentials
):
    return ActivityStream(base_url,
                          selenium,
                          **default_credentials).open()


@pytest.fixture
def ui_management_jobs(request, ansible_runner, selenium, base_url, default_credentials):

    script_setup = '''
from django.utils.timezone import now
from awx.main.models import *

SystemJobTemplate(name='Cleanup Job Details',
    description="Remove job history older than X days",
    job_type="cleanup_jobs",
    created=now(),
    modified=now()).save()
SystemJobTemplate(name='Cleanup Deleted Data',
    description="Remove deleted object history older than X days",
    job_type="cleanup_deleted",
    created=now(),
    modified=now()).save()
SystemJobTemplate(name='Cleanup Activity Stream',
    description="Remove activity stream history older than X days",
    job_type="cleanup_activitystream",
    created=now(),
    modified=now()).save()

    '''

    script_teardown = '''
from awx.main.models import *

for jobTemplate in SystemJobTemplate.objects.all():
    jobTemplate.delete()

    '''

    # push scripts to host
    ansible_runner.copy(content=script_setup,
                        dest='~/setup_system_job_templates.py')
    ansible_runner.copy(content=script_teardown,
                        dest='~/teardown_system_job_templates.py')

    # run setup scripts
    ansible_runner.shell(
        'cat teardown_system_job_templates.py | tower-manage shell', chdir='~')
    ansible_runner.shell(
        'cat setup_system_job_templates.py | tower-manage shell', chdir='~')

    # run teardown script and delete files after test run
    def fin():
        ansible_runner.shell(
            'cat teardown_system_job_templates.py | tower-manage shell', chdir='~')
        ansible_runner.file(state='absent',
                            path='~/setup_system_job_templates.py')
        ansible_runner.file(state='absent',
                            path='~/teardown_system_job_templates.py')

    request.addfinalizer(fin)

    return ManagementJobs(base_url,
                          selenium,
                          **default_credentials).open()


@pytest.fixture
def ui_license(selenium, base_url, default_credentials, ui_login):
    ui_login.login(wait=False, **default_credentials)
    license_page = License(base_url, selenium, **default_credentials)
    license_page.driver.get(license_page.url)
    license_page.wait_for_spinny()
    license_page.wait_until_loaded()
    return license_page
