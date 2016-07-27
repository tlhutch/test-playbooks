import logging

import fauxfactory
import pytest

from common.rrule import RRule

from common.ui.models import (
    ActivityStream,
    Credentials,
    CredentialAdd,
    CredentialEdit,
    Dashboard,
    Inventories,
    InventoryAdd,
    InventoryEdit,
    Jobs,
    JobTemplates,
    JobTemplateAdd,
    JobTemplateEdit,
    JobTemplateSchedules,
    JobTemplateScheduleAdd,
    JobTemplateScheduleEdit,
    License,
    Login,
    Organizations,
    OrganizationAdd,
    OrganizationEdit,
    Projects,
    ProjectAdd,
    ProjectEdit,
    ProjectSchedules,
    ProjectScheduleAdd,
    ProjectScheduleEdit,
    SetupMenu,
    Teams,
    TeamAdd,
    TeamEdit,
    Users,
    UserAdd,
    UserEdit,
)

log = logging.getLogger(__name__)


# -----------------------------------------------------------------------------
# Window Size and Position
# -----------------------------------------------------------------------------


def pytest_addoption(parser):
    parser.addoption('--supported-window-sizes',
                     action='store',
                     default='maximized,800x600',
                     help='comma-separated list of supported window sizes')


def pytest_generate_tests(metafunc):
    if 'window_size' in metafunc.fixturenames:
        params = metafunc.config.getoption('--supported-window-sizes')
        params = list(set(params.split(',')))
        metafunc.parametrize('window_size', params)


def _max_window(driver):
    if driver.name == 'chrome':
        script = 'return [screen.width, screen.height];'
        (width, height) = driver.execute_script(script)
        driver.set_window_position(0, 0)
        driver.set_window_size(width, height)
    else:
        driver.maximize_window()
    return True


@pytest.fixture
def max_window(selenium):
    log.debug('Calling fixture maximized')
    return _max_window(selenium)


@pytest.fixture
def supported_window_sizes(window_size, selenium):
    if window_size.lower() in 'maximized':
        return _max_window(selenium)
    (width, height) = map(int, window_size.split('x'))
    selenium.set_window_position(0, 0)
    selenium.set_window_size(width, height)
    return True

# -----------------------------------------------------------------------------
# Data
# -----------------------------------------------------------------------------


@pytest.fixture
def default_credentials(testsetup):
    return testsetup.credentials['default']


@pytest.fixture
def ui_user_credentials(authtoken, factories, default_credentials):
    default_password = default_credentials['password']
    user = factories.user(password=default_password, is_superuser=True)
    return {'username': user.username, 'password': default_password}


# -----------------------------------------------------------------------------
# Application Models
# -----------------------------------------------------------------------------

@pytest.fixture
def ui_login(selenium, base_url):
    return Login(selenium, base_url).open()


@pytest.fixture
def ui_dashboard(ui_user_credentials, ui_login, selenium, base_url):
    ui_login.login(**ui_user_credentials)
    return Dashboard(selenium, base_url)


@pytest.fixture
def ui_activity_stream(ui_dashboard, selenium, base_url):
    return ActivityStream(selenium, base_url).open()


@pytest.fixture
def ui_credentials(ui_dashboard, selenium, base_url):
    return Credentials(selenium, base_url).open()


@pytest.fixture
def ui_credential_add(ui_dashboard, selenium, base_url):
    return CredentialAdd(selenium, base_url).open()


@pytest.fixture
def ui_credential_edit(factories, ui_dashboard, selenium, base_url):
    credential = factories.credential()
    return CredentialEdit(selenium, base_url, id=credential.id).open()


@pytest.fixture
def ui_inventories(ui_dashboard, selenium, base_url):
    return Inventories(selenium, base_url).open()


@pytest.fixture
def ui_inventory_add(ui_dashboard, selenium, base_url):
    return InventoryAdd(selenium, base_url).open()


@pytest.fixture
def ui_inventory_edit(factories, ui_dashboard, selenium, base_url):
    inventory = factories.inventory()
    return InventoryEdit(selenium, base_url, id=inventory.id).open()


@pytest.fixture
def ui_job_templates(ui_dashboard, selenium, base_url):
    return JobTemplates(selenium, base_url).open()


@pytest.fixture
def ui_job_template_add(ui_dashboard, selenium, base_url):
    return JobTemplateAdd(selenium, base_url).open()


@pytest.fixture
def ui_job_template_edit(factories, ui_dashboard, selenium, base_url):
    job_template = factories.job_template()
    return JobTemplateEdit(selenium, base_url, id=job_template.id).open()


@pytest.fixture
def ui_job_template_schedules(ui_dashboard, selenium, base_url):
    return JobTemplateSchedules(selenium, base_url).open()


@pytest.fixture
def ui_job_template_schedule_add(ui_dashboard, selenium, base_url):
    return JobTemplateScheduleAdd(selenium, base_url).open()


@pytest.fixture
def ui_job_template_schedule_edit(factories, ui_dashboard, selenium, base_url):

    rr = RRule(3, count=1, byminute='', bysecond='', byhour='')
    payload = {'name': fauxfactory.gen_alphanumeric(), 'rrule': str(rr)}

    job_template = factories.job_template()
    schedule = job_template.get_related('schedules').post(payload)

    return \
        JobTemplateScheduleEdit(
            selenium,
            base_url,
            id=job_template.id,
            schedule_id=schedule.id).open()


@pytest.fixture
def ui_jobs(ui_dashboard, selenium, base_url):
    return Jobs(selenium, base_url).open()


@pytest.fixture
def ui_license(ui_dashboard, selenium, base_url):
    return License(selenium, base_url).open()


@pytest.fixture
def ui_organizations(ui_dashboard, selenium, base_url):
    return Organizations(selenium, base_url).open()


@pytest.fixture
def ui_organization_add(ui_dashboard, selenium, base_url):
    return OrganizationAdd(selenium, base_url).open()


@pytest.fixture
def ui_organization_edit(factories, ui_dashboard, selenium, base_url):
    organization = factories.organization()
    return OrganizationEdit(selenium, base_url, id=organization.id).open()


@pytest.fixture
def ui_projects(ui_dashboard, selenium, base_url):
    return Projects(selenium, base_url).open()


@pytest.fixture
def ui_project_add(ui_dashboard, selenium, base_url):
    return ProjectAdd(selenium, base_url).open()


@pytest.fixture
def ui_project_edit(factories, ui_dashboard, selenium, base_url):
    project = factories.project()
    return ProjectEdit(selenium, base_url, id=project.id).open()


@pytest.fixture
def ui_job_project_schedules(ui_dashboard, selenium, base_url):
    return ProjectSchedules(selenium, base_url).open()


@pytest.fixture
def ui_project_schedule_add(ui_dashboard, selenium, base_url):
    return ProjectScheduleAdd(selenium, base_url).open()


@pytest.fixture
def ui_project_schedule_edit(factories, ui_dashboard, selenium, base_url):

    rr = RRule(3, count=1, byminute='', bysecond='', byhour='')
    payload = {'name': fauxfactory.gen_alphanumeric(), 'rrule': str(rr)}

    project = factories.project()
    schedule = project.get_related('schedules').post(payload)

    return \
        ProjectScheduleEdit(
            selenium,
            base_url,
            id=project.id,
            schedule_id=schedule.id).open()


@pytest.fixture
def ui_setup(ui_dashboard, selenium, base_url):
    return SetupMenu(selenium, base_url).open()


@pytest.fixture
def ui_teams(ui_dashboard, selenium, base_url):
    return Teams(selenium, base_url).open()


@pytest.fixture
def ui_team_add(ui_dashboard, selenium, base_url):
    return TeamAdd(selenium, base_url).open()


@pytest.fixture
def ui_team_edit(factories, ui_dashboard, selenium, base_url):
    team = factories.team()
    return TeamEdit(selenium, base_url, id=team.id).open()


@pytest.fixture
def ui_users(ui_dashboard, selenium, base_url):
    return Users(selenium, base_url).open()


@pytest.fixture
def ui_user_add(ui_dashboard, selenium, base_url):
    return UserAdd(selenium, base_url).open()


@pytest.fixture
def ui_user_edit(factories, ui_dashboard, selenium, base_url):
    user = factories.user()
    return UserEdit(selenium, base_url, id=user.id).open()
