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
def ui_login(mozwebqa):
    return Login(mozwebqa.base_url, mozwebqa.selenium).open()


@pytest.fixture
def ui_dashboard(
    mozwebqa,
    default_credentials
):
    return Dashboard(mozwebqa.base_url,
                     mozwebqa.selenium,
                     **default_credentials).open()


@pytest.fixture
def ui_inventories(
    mozwebqa,
    default_credentials
):
    return Inventories(mozwebqa.base_url,
                       mozwebqa.selenium,
                       **default_credentials).open()


@pytest.fixture
def ui_inventories_add(
    mozwebqa,
    default_credentials
):
    return Inventories(mozwebqa.base_url,
                       mozwebqa.selenium,
                       index='add',
                       **default_credentials).open()


@pytest.fixture
def ui_inventories_edit(
    inventory,
    mozwebqa,
    default_credentials
):
    return Inventories(mozwebqa.base_url,
                       mozwebqa.selenium,
                       index=inventory.id,
                       **default_credentials).open()


@pytest.fixture
def ui_inventory_scripts(
    mozwebqa,
    default_credentials
):
    return InventoryScripts(mozwebqa.base_url,
                            mozwebqa.selenium,
                            **default_credentials).open()


@pytest.fixture
def ui_inventory_scripts_add(
    mozwebqa,
    default_credentials
):
    return InventoryScripts(mozwebqa.base_url,
                            mozwebqa.selenium,
                            index='add',
                            **default_credentials).open()


@pytest.fixture
def ui_inventory_scripts_edit(
    inventory_script,
    mozwebqa,
    default_credentials
):
    return InventoryScripts(mozwebqa.base_url,
                            mozwebqa.selenium,
                            index=inventory_script.id,
                            **default_credentials).open()


@pytest.fixture
def ui_job_templates(
    mozwebqa,
    default_credentials
):
    return JobTemplates(mozwebqa.base_url,
                        mozwebqa.selenium,
                        **default_credentials).open()


@pytest.fixture
def ui_job_templates_add(
    mozwebqa,
    default_credentials
):
    return JobTemplates(mozwebqa.base_url,
                        mozwebqa.selenium,
                        index='add',
                        **default_credentials).open()


@pytest.fixture
def ui_job_templates_edit(
    authtoken,
    install_basic_license,
    job_template_with_schedule,
    mozwebqa,
    default_credentials
):
    return JobTemplates(mozwebqa.base_url,
                        mozwebqa.selenium,
                        index=job_template_with_schedule.id,
                        **default_credentials).open()


@pytest.fixture
def ui_job_templates_schedule(
    authtoken,
    install_basic_license,
    job_template_with_schedule,
    mozwebqa,
    default_credentials
):
    return JobTemplateSchedules(mozwebqa.base_url,
                                mozwebqa.selenium,
                                index=job_template_with_schedule.id,
                                **default_credentials).open()


@pytest.fixture
def ui_projects(
    mozwebqa,
    default_credentials
):
    return Projects(mozwebqa.base_url,
                    mozwebqa.selenium,
                    **default_credentials).open()


@pytest.fixture
def ui_projects_add(
    mozwebqa,
    default_credentials
):
    return Projects(mozwebqa.base_url,
                    mozwebqa.selenium,
                    index='add',
                    **default_credentials).open()


@pytest.fixture
def ui_projects_edit(
    project_with_schedule,
    mozwebqa,
    default_credentials
):
    return Projects(mozwebqa.base_url,
                    mozwebqa.selenium,
                    index=project_with_schedule.id,
                    **default_credentials).open()


@pytest.fixture
def ui_projects_schedule(
    project_with_schedule,
    mozwebqa,
    default_credentials
):
    return ProjectSchedules(mozwebqa.base_url,
                            mozwebqa.selenium,
                            index=project_with_schedule.id,
                            **default_credentials).open()


@pytest.fixture
def ui_jobs(
    mozwebqa,
    default_credentials
):
    return Jobs(mozwebqa.base_url,
                mozwebqa.selenium,
                **default_credentials).open()


@pytest.fixture
def ui_users(
    mozwebqa,
    default_credentials
):
    return Users(mozwebqa.base_url,
                 mozwebqa.selenium,
                 **default_credentials).open()


@pytest.fixture
def ui_users_add(
    mozwebqa,
    default_credentials
):
    return Users(mozwebqa.base_url,
                 mozwebqa.selenium,
                 index='add',
                 **default_credentials).open()


@pytest.fixture
def ui_users_edit(
    anonymous_user,
    mozwebqa,
    default_credentials
):
    return Users(mozwebqa.base_url,
                 mozwebqa.selenium,
                 index=anonymous_user.id,
                 **default_credentials).open()


@pytest.fixture
def ui_teams(
    mozwebqa,
    default_credentials
):
    return Teams(mozwebqa.base_url,
                 mozwebqa.selenium,
                 **default_credentials).open()


@pytest.fixture
def ui_teams_add(
    mozwebqa,
    default_credentials
):
    return Teams(mozwebqa.base_url,
                 mozwebqa.selenium,
                 index='add',
                 **default_credentials).open()


@pytest.fixture
def ui_teams_edit(
    team,
    mozwebqa,
    default_credentials
):
    return Teams(mozwebqa.base_url,
                 mozwebqa.selenium,
                 index=team.id,
                 **default_credentials).open()


@pytest.fixture
def ui_organizations(
    authtoken,
    install_enterprise_license_unlimited,
    mozwebqa,
    default_credentials
):
    return Organizations(mozwebqa.base_url,
                         mozwebqa.selenium,
                         **default_credentials).open()


@pytest.fixture
def ui_organizations_add(
    authtoken,
    install_enterprise_license_unlimited,
    mozwebqa,
    default_credentials
):
    return Organizations(mozwebqa.base_url,
                         mozwebqa.selenium,
                         index='add',
                         **default_credentials).open()


@pytest.fixture
def ui_organizations_edit(
    authtoken,
    install_enterprise_license_unlimited,
    another_organization,
    mozwebqa,
    default_credentials
):
    return Organizations(mozwebqa.base_url,
                         mozwebqa.selenium,
                         index=another_organization.id,
                         **default_credentials).open()


@pytest.fixture
def ui_credentials(
    mozwebqa,
    default_credentials
):
    return Credentials(mozwebqa.base_url,
                       mozwebqa.selenium,
                       **default_credentials).open()


@pytest.fixture
def ui_credentials_edit(
    ssh_credential,
    mozwebqa,
    default_credentials
):
    return Credentials(mozwebqa.base_url,
                       mozwebqa.selenium,
                       index=ssh_credential.id,
                       **default_credentials).open()


@pytest.fixture
def ui_credentials_add(
    mozwebqa,
    default_credentials
):
    return Credentials(mozwebqa.base_url,
                       mozwebqa.selenium,
                       index='add',
                       **default_credentials).open()


@pytest.fixture
def ui_hosts(
    mozwebqa,
    default_credentials
):
    return Hosts(mozwebqa.base_url,
                 mozwebqa.selenium,
                 **default_credentials).open()


@pytest.fixture
def ui_setup(
    mozwebqa,
    default_credentials
):
    return SetupMenu(mozwebqa.base_url,
                     mozwebqa.selenium,
                     **default_credentials).open()


@pytest.fixture
def ui_manage_inventory(
    request,
    host_local,
    mozwebqa,
    default_credentials
):
    inventory = host_local.get_related('inventory')

    inventory.get_related('groups').post({
        'name': 'ui-group-%s' % fauxfactory.gen_alphanumeric(),
        'description': fauxfactory.gen_utf8(),
        'inventory': inventory.id
    })

    return ManageInventory(mozwebqa.base_url,
                           mozwebqa.selenium,
                           inventory.id,
                           **default_credentials).open()


@pytest.fixture
def ui_activity_stream(
    mozwebqa,
    default_credentials
):
    return ActivityStream(mozwebqa.base_url,
                          mozwebqa.selenium,
                          **default_credentials).open()


@pytest.fixture
def ui_management_jobs(request, ansible_runner, mozwebqa, default_credentials):

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

    return ManagementJobs(mozwebqa.base_url,
                          mozwebqa.selenium,
                          **default_credentials).open()


@pytest.fixture
def ui_license(
    mozwebqa,
    default_credentials
):
    return License(mozwebqa.base_url,
                   mozwebqa.selenium,
                   **default_credentials).open()
