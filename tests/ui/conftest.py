from collections import namedtuple
import logging
import time

import fauxfactory
import pytest

from selenium.webdriver.remote.remote_connection import LOGGER

from towerkit import api, config, utils
from towerkit import exceptions as exc
from towerkit.rrule import RRule
from towerkit import TowerUI

LOGGER.setLevel(logging.WARNING)


# -----------------------------------------------------------------------------
# Options
# -----------------------------------------------------------------------------

def pytest_addoption(parser):
    # parser.addoption('--base-url',
    #                  action='store',
    #                  dest='base_url',
    #                  help='base url of tower instance under test')
    parser.addoption('--browser',
                     action='store',
                     dest='browser_name',
                     help='name of browser to use')
    parser.addoption('--driver-capabilities',
                     action='store',
                     dest='driver_capabilities',
                     default='platform:windows 10',
                     metavar='key1:value2,key2:value2',
                     help='remote webdriver capabilities')
    parser.addoption('--driver-type',
                     action='store',
                     dest='driver_type',
                     help='type of webdriver (local | remote)')
    parser.addoption('--driver-location',
                     action='store',
                     dest='driver_location',
                     help='remote webdriver url or file path to a webdriver binary')
    # parser.addoption('--credentials',
    #                  action='store',
    #                  dest='credentials',
    #                  help='path to towerkit credentials file')
    parser.addoption('--validate-schema',
                     action='store',
                     dest='validate_schema',
                     type=bool,
                     default=False,
                     help='enable implicit api schema validation')

# -----------------------------------------------------------------------------
# Session Fixtures
# -----------------------------------------------------------------------------


@pytest.fixture(scope='session')
def supported_window_sizes(request):
    yield NotImplemented


@pytest.fixture(scope='session')
def config_credentials(request):
    yield utils.load_credentials(request.config.getoption('credentials_file'))


@pytest.fixture(scope='session')
def default_tower_credentials(config_credentials):
    yield config_credentials['default']


@pytest.fixture(scope='session')
def base_url(request):
    return request.config.getoption('base_url')


@pytest.fixture(scope='session')
def api_v1(request, config_credentials, base_url):
    config.validate_schema = request.config.getoption('validate_schema')
    config.base_url = request.config.getoption('base_url')
    config.credentials = config_credentials
    v1 = api.ApiV1().load_default_authtoken().get()
    v1.config.get().install_license()
    return v1


@pytest.fixture(scope='session')
def ui_user(api_v1, default_tower_credentials):
    pw = default_tower_credentials['password']
    user = api_v1.users.create(password=pw, is_superuser=True)
    yield user
    user.silent_cleanup()


@pytest.yield_fixture(scope='session')
def session_org(api_v1):
    organization = api_v1.organizations.create()
    yield organization
    organization.silent_cleanup()


@pytest.yield_fixture(scope='session')
def session_machine_credential(api_v1, session_org):
    credential = api_v1.credentials.create(kind='ssh', organization=session_org)
    yield credential
    credential.silent_cleanup()


@pytest.yield_fixture(scope='session')
def session_cloud_credential(api_v1, session_org):
    credential = api_v1.credentials.create(kind='aws', organization=session_org)
    yield credential
    credential.silent_cleanup()


@pytest.yield_fixture(scope='session')
def session_network_credential(api_v1, session_org):
    credential = api_v1.credentials.create(kind='net', organization=session_org)
    yield credential
    credential.silent_cleanup()


@pytest.yield_fixture(scope='session')
def session_inventory(api_v1, session_org):
    inventory = api_v1.inventory.create(organization=session_org)
    yield inventory
    inventory.silent_cleanup()


@pytest.yield_fixture(scope='session')
def session_project(api_v1, session_org):
    project = api_v1.projects.create(
        organization=session_org,
        wait=True,
        scm_url='https://github.com/jlaska/ansible-playbooks.git')
    project.wait_until_completed()
    yield project
    project.silent_cleanup()


@pytest.yield_fixture(scope='session')
def session_job_template(api_v1,
                         session_inventory,
                         session_machine_credential,
                         session_project):
    job_template = api_v1.job_templates.create(
        credential=session_machine_credential,
        inventory=session_inventory,
        project=session_project)
    yield job_template
    job_template.silent_cleanup()


@pytest.fixture(scope='session')
def org_admin(api_v1, default_tower_credentials, get_role, session_org):
    user = api_v1.users.get().create(
        organization=session_org, password=default_tower_credentials['password'])
    with pytest.raises(exc.NoContent):
        get_role(session_org, 'Admin').get_related('users').post({'id': user.id})
    yield user
    user.silent_cleanup()


@pytest.fixture(scope='session')
def rando(api_v1, default_tower_credentials):
    user = api_v1.users.get().create(
        password=default_tower_credentials['password'])
    yield user
    user.silent_cleanup()


@pytest.fixture(scope='session')
def session_team(api_v1):
    team = api_v1.teams.create()
    yield team
    team.silent_cleanup()


session_user = rando

# -----------------------------------------------------------------------------
# Module Fixtures
# -----------------------------------------------------------------------------


@pytest.fixture(scope='module')
def inventory(api_v1, session_org):
    obj = api_v1.inventory.create(organization=session_org)
    yield obj
    obj.silent_cleanup()


@pytest.fixture(scope='module')
def project(api_v1, session_org):
    obj = api_v1.projects.create(organization=session_org)
    yield obj
    obj.silent_cleanup()


@pytest.fixture(scope='module')
def job_template(api_v1,
                 session_inventory,
                 session_project,
                 session_machine_credential):
    template = api_v1.job_templates.create(
        inventory=session_inventory,
        project=session_project,
        credential=session_machine_credential)
    yield template
    template.silent_cleanup()


@pytest.fixture(scope='module')
def job_template_schedule(job_template):
    rr = RRule(3, count=1, byminute='', bysecond='', byhour='')
    payload = {'name': fauxfactory.gen_alphanumeric(), 'rrule': str(rr)}
    schedule = job_template.related.schedules.post(payload)
    yield schedule
    schedule.silent_cleanup()


@pytest.fixture(scope='module')
def project_schedule(project):
    rr = RRule(3, count=1, byminute='', bysecond='', byhour='')
    payload = {'name': fauxfactory.gen_alphanumeric(), 'rrule': str(rr)}
    schedule = project.related.schedules.post(payload)
    yield schedule
    schedule.silent_cleanup()


# -----------------------------------------------------------------------------
# Class Fixtures
# -----------------------------------------------------------------------------


SessionObjects = namedtuple('SessionObjects', [
    'organization',
    'credential',
    'inventory',
    'project',
    'job_template',
    'user',
    'team',
])


@pytest.fixture(scope='session')
def session_fixtures(request,
                     session_org,
                     session_machine_credential,
                     session_inventory,
                     session_project,
                     session_job_template,
                     session_user,
                     session_team):
    objects = SessionObjects(
        organization=session_org,
        credential=session_machine_credential,
        inventory=session_inventory,
        project=session_project,
        job_template=session_job_template,
        user=session_user,
        team=session_team)

    if hasattr(request, 'cls'):
        request.cls.session_objects = objects

    yield objects


@pytest.fixture(scope='class')
def ui_client(request, v1, default_tower_credentials, ui_user):

    # 'action=append' for pytest parser hook doesn't appear to be working
    driver_capabilities_str = request.config.getoption('driver_capabilities')
    driver_capabilities = dict([v.split(':') for v in driver_capabilities_str.split(',')])

    if 'platform' in driver_capabilities:
        driver_capabilities['platform'] = driver_capabilities['platform'].replace('_', ' ')

    if request.config.getoption('driver_type') == 'remote':
        driver_capabilities['acceptSslCerts'] = True

        if request.config.getoption('browser_name') == 'firefox':
            if driver_capabilities.get('platform', None) != 'linux':
                driver_capabilities['version'] = '47'
            driver_capabilities['marionette'] = False

    client = TowerUI(
        base_url=request.config.getoption('base_url'),
        browser_name=request.config.getoption('browser_name'),
        driver_type=request.config.getoption('driver_type'),
        driver_location=request.config.getoption('driver_location'),
        driver_capabilities=driver_capabilities,
        username=ui_user.username,
        password=ui_user.password)
    if request.cls:
        request.cls.client = client
        request.cls.browser = client.browser
        request.cls.ui = client.ui
    yield client


@pytest.fixture(scope='class')
def ui(request, ui_client):
    ui_client.login()
    yield ui_client.ui
    ui_client.browser.quit()


@pytest.fixture(scope='session')
def v1(request, api_v1):
    if hasattr(request, 'cls'):
        request.cls.v1 = api_v1
    yield api_v1


# -----------------------------------------------------------------------------
# Utilities
# -----------------------------------------------------------------------------

@pytest.fixture(scope='session')
def get_role():
    def _get_role(obj, role_name):
        """Lookup and return a return a role page model by its role name.

        :param model: A resource api page model with related roles endpoint
        :role_name: The name of the role (case insensitive)

        Usage::
            >>> # get the description of the Use role for an inventory
            >>> bar_inventory = factories.inventory()
            >>> role_page = get_role(bar_inventory, 'Use')
            >>> role_page.description
            u'Can use the inventory in a job template'
        """
        search_name = role_name.lower()
        for role in obj.object_roles:
            if role.name.lower() == search_name:
                return role
        msg = "Role '{0}' not found for {1}".format(role_name, type(obj))
        raise ValueError(msg)
    return _get_role
