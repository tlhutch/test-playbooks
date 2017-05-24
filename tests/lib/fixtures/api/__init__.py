from towerkit.api import get_registered_page
import towerkit.tower
import pytest


def navigate(api, url, field):
    """Return a json attribute from the given url.  While one can simply
    concatenate strings to form a URL, this method is preferred to ensure the
    API is capable of self-referencing.

    Examples:
     * navigate(api, '/api/', 'current_version') returns '/api/v1'
     * navigate(api, '/api/v1/, 'config') returns '/api/v1/config'

    Update: towerkit traces the api in its functionality and is the preferred
    resource object builder.  `navigate` is just used for api_v1_url and test will
    be done by towerkit `Base` subclasses.
    """
    if not url.endswith('/'):
        url += '/'
    data = api.get(url).json()
    return data.get(field)


@pytest.fixture(scope="session")
def api(testsetup):
    """Convenience fixture that returns api object"""
    return testsetup.api


@pytest.fixture(scope='session')
def available_versions(api):
    return navigate(api, '/api', 'available_versions')


@pytest.fixture(scope='session')
def get_api_version(available_versions):
    def _get_api_version(desired_version):
        if desired_version not in available_versions:
            raise(Exception("Requested tower version '{0}' not available.  Choices include: {1}"
                            .format(desired_version, available_versions)))
        return available_versions.get(desired_version)
    return _get_api_version


@pytest.fixture(scope="class")
def api_v1_url(get_api_version):
    return get_api_version('v1')


@pytest.fixture(scope="class")
def api_v1_pg(testsetup, api_v1_url):
    return get_registered_page(api_v1_url)(testsetup.api, endpoint=api_v1_url).get()


@pytest.fixture(scope='class')
def v1_module(api_v1_pg):
    return api_v1_pg


@pytest.fixture
def v1(v1_module):
    return v1_module


@pytest.fixture(scope="class")
def api_v2_url(get_api_version):
    return get_api_version('v2')


@pytest.fixture(scope="class")
def api_v2_pg(testsetup, api_v2_url):
    return get_registered_page(api_v2_url)(testsetup.api, endpoint=api_v2_url).get()


@pytest.fixture(scope='class')
def v2_module(api_v2_pg):
    return api_v2_pg


@pytest.fixture
def v2(v2_module):
    return v2_module


# /api/v1/authtoken
@pytest.fixture(scope="class")
def api_authtoken_url(v1_module):
    return v1_module.authtoken


@pytest.fixture(scope="class")
def api_authtoken_pg(api_authtoken_url):
    return api_authtoken_url.get()


@pytest.fixture(scope="class")
def authtoken(testsetup, v1_module):
    """Logs in to the application with default credentials"""
    authtoken = v1_module.get_authtoken()
    testsetup.api.login(token=authtoken)
    return authtoken


# /api/v1/dashboard
@pytest.fixture(scope="class")
def api_dashboard_url(v1_module):
    return v1_module.dashboard


@pytest.fixture(scope="class")
def api_dashboard_pg(api_dashboard_url):
    return api_dashboard_url.get()


# /api/v1/ping
@pytest.fixture(scope="class")
def api_ping_url(v1_module):
    return v1_module.ping


@pytest.fixture(scope="class")
def api_ping_pg(api_ping_url):
    return api_ping_url.get()


# /api/v1/config
@pytest.fixture(scope="class")
def api_config_url(v1_module):
    return v1_module.config


@pytest.fixture(scope="class")
def api_config_pg(api_config_url):
    return api_config_url.get()


@pytest.fixture(scope="class")
def tower_version(api_config_pg):
    return api_config_pg.version


@pytest.fixture(scope="class")
def tower_version_cmp(request, tower_version):
    def func(x):
        return towerkit.tower.version_cmp(tower_version, x)
    return func


@pytest.fixture(scope='class')
def ansible_version(api_config_pg):
    """Returns the ansible version of the system under test."""
    return api_config_pg.get().ansible_version


@pytest.fixture(scope="class")
def ansible_version_cmp(request, ansible_version):
    def func(x):
        return towerkit.tower.version_cmp(ansible_version, x)
    return func


@pytest.fixture(scope="class")
def awx_config(v1_module):
    return v1_module.config.get()


# /api/v1/me
@pytest.fixture(scope="class")
def api_me_url(v1_module):
    return v1_module.me


@pytest.fixture(scope="class")
def api_me_pg(api_me_url):
    return api_me_url.get()


# /api/v1/organizations
@pytest.fixture(scope="class")
def api_organizations_url(v1_module):
    return v1_module.organizations


@pytest.fixture(scope="class")
def api_organizations_pg(api_organizations_url):
    return api_organizations_url.get()


# /api/v1/users
@pytest.fixture(scope="class")
def api_users_url(v1_module):
    return v1_module.users


@pytest.fixture(scope="class")
def api_users_pg(api_users_url):
    return api_users_url.get()


# /api/v1/teams
@pytest.fixture(scope="class")
def api_teams_url(v1_module):
    return v1_module.teams


@pytest.fixture(scope="class")
def api_teams_pg(api_teams_url):
    return api_teams_url.get()


# /api/v1/projects
@pytest.fixture(scope="class")
def api_projects_url(v1_module):
    return v1_module.projects


@pytest.fixture(scope="class")
def api_projects_pg(api_projects_url):
    return api_projects_url.get()


# /api/v1/project_updates
@pytest.fixture(scope="class")
def api_project_updates_url(v1_module):
    return v1_module.project_updates


@pytest.fixture(scope="class")
def api_project_updates_pg(api_project_updates_url):
    return api_project_updates_url.get()


# /api/v1/activity_stream
@pytest.fixture(scope="class")
def api_activity_stream_url(v1_module):
    return v1_module.activity_stream


@pytest.fixture(scope="class")
def api_activity_stream_pg(api_activity_stream_url):
    return api_activity_stream_url.get()


# /api/v1/credentials
@pytest.fixture(scope="class")
def api_credentials_url(v1_module):
    return v1_module.credentials


@pytest.fixture(scope="class")
def api_credentials_pg(api_credentials_url):
    return api_credentials_url.get()


# /api/v1/inventory
@pytest.fixture(scope="class")
def api_inventories_url(v1_module):
    return v1_module.inventory


@pytest.fixture(scope="class")
def api_inventories_pg(api_inventories_url):
    return api_inventories_url.get()


# /api/v1/inventory_updates
@pytest.fixture(scope="class")
def api_inventory_updates_url(v1_module):
    return v1_module.inventory_updates


@pytest.fixture(scope="class")
def api_inventory_updates_pg(api_inventory_updates_url):
    return api_inventory_updates_url.get()


# /api/v1/inventory_sources
@pytest.fixture(scope="class")
def api_inventory_sources_url(v1_module):
    return v1_module.inventory_sources


@pytest.fixture(scope="class")
def api_inventory_sources_pg(api_inventory_sources_url):
    return api_inventory_sources_url.get()


# /api/v1/inventory_scripts
@pytest.fixture(scope="class")
def api_inventory_scripts_url(v1_module):
    return v1_module.inventory_scripts


@pytest.fixture(scope="class")
def api_inventory_scripts_pg(api_inventory_scripts_url):
    return api_inventory_scripts_url.get()


# /api/v1/groups
@pytest.fixture(scope="class")
def api_groups_url(v1_module):
    return v1_module.groups


@pytest.fixture(scope="class")
def api_groups_pg(api_groups_url):
    return api_groups_url.get()


# /api/v1/hosts
@pytest.fixture(scope="class")
def api_hosts_url(v1_module):
    return v1_module.hosts


@pytest.fixture(scope="class")
def api_hosts_pg(api_hosts_url):
    return api_hosts_url.get()


# /api/v1/job_templates
@pytest.fixture(scope="class")
def api_job_templates_url(v1_module):
    return v1_module.job_templates


@pytest.fixture(scope="class")
def api_job_templates_pg(api_job_templates_url):
    return api_job_templates_url.get()


# /api/v1/schedules
@pytest.fixture(scope="class")
def api_schedules_url(v1_module):
    return v1_module.schedules


@pytest.fixture(scope="class")
def api_schedules_pg(api_schedules_url):
    return api_schedules_url.get()


# /api/v1/jobs
@pytest.fixture(scope="class")
def api_jobs_url(v1_module):
    return v1_module.jobs


@pytest.fixture(scope="class")
def api_jobs_pg(api_jobs_url):
    return api_jobs_url.get()


# /api/v1/unified_jobs
@pytest.fixture(scope="class")
def api_unified_jobs_url(v1_module):
    return v1_module.unified_jobs


@pytest.fixture(scope="class")
def api_unified_jobs_pg(api_unified_jobs_url):
    return api_unified_jobs_url.get()


# /api/v1/unified_job_templates
@pytest.fixture(scope="class")
def api_unified_job_templates_url(v1_module):
    return v1_module.unified_job_templates


@pytest.fixture(scope="class")
def api_unified_job_templates_pg(api_unified_job_templates_url):
    return api_unified_job_templates_url.get()


# /api/v1/system_jobs
@pytest.fixture(scope="class")
def api_system_jobs_url(v1_module):
    return v1_module.system_jobs


@pytest.fixture(scope="class")
def api_system_jobs_pg(api_system_jobs_url):
    return api_system_jobs_url.get()


# /api/v1/system_job_templates
@pytest.fixture(scope="class")
def api_system_job_templates_url(v1_module):
    return v1_module.system_job_templates


@pytest.fixture(scope="class")
def api_system_job_templates_pg(api_system_job_templates_url):
    return api_system_job_templates_url.get()


# /api/v1/ad_hoc_commands
@pytest.fixture(scope="class")
def api_ad_hoc_commands_url(v1_module):
    return v1_module.ad_hoc_commands


@pytest.fixture(scope="class")
def api_ad_hoc_commands_pg(api_ad_hoc_commands_url):
    return api_ad_hoc_commands_url.get()


@pytest.fixture(scope="class")
def region_choices(api_inventory_sources_pg):
    options = api_inventory_sources_pg.options()

    # The format is a list of lists in the format: [['<internal-string>', '<human-readable-string>'], ...]
    return dict(ec2=[r[0] for r in options.json.get('actions', {}).get('GET', {}).get('source_regions', {}).get('ec2_region_choices', [])],
                azure=[r[0] for r in options.json.get('actions', {}).get('GET', {}).get('source_regions', {}).get('azure_region_choices', [])],
                gce=[r[0] for r in options.json.get('actions', {}).get('GET', {}).get('source_regions', {}).get('gce_region_choices', [])])


# /api/v1/notifications
@pytest.fixture(scope="class")
def api_notifications_url(v1_module):
    return v1_module.notifications


@pytest.fixture(scope="class")
def api_notifications_pg(api_notifications_url):
    return api_notifications_url.get()


# /api/v1/notification_templates
@pytest.fixture(scope="class")
def api_notification_templates_url(v1_module):
    return v1_module.notification_templates


@pytest.fixture(scope="class")
def api_notification_templates_pg(api_notification_templates_url):
    return api_notification_templates_url.get()


# /api/v1/labels
@pytest.fixture(scope="class")
def api_labels_url(v1_module):
    return v1_module.labels


@pytest.fixture(scope="class")
def api_labels_pg(api_labels_url):
    return api_labels_url.get()


# /api/v1/roles
@pytest.fixture(scope="class")
def api_roles_url(v1_module):
    return v1_module.roles


@pytest.fixture(scope="class")
def api_roles_pg(api_roles_url):
    return api_roles_url.get()


# /api/v1/workflow_job_templates
@pytest.fixture(scope="class")
def api_workflow_job_templates_url(v1_module):
    return v1_module.workflow_job_templates


@pytest.fixture(scope="class")
def api_workflow_job_templates_pg(api_workflow_job_templates_url):
    return api_workflow_job_templates_url.get()


# /api/v1/workflow_job_template_nodes
@pytest.fixture(scope="class")
def api_workflow_job_template_nodes_url(v1_module):
    return v1_module.workflow_job_template_nodes


@pytest.fixture(scope="class")
def api_workflow_job_template_nodes_pg(api_workflow_job_template_nodes_url):
    return api_workflow_job_template_nodes_url.get()


# /api/v1/workflow_jobs
@pytest.fixture(scope="class")
def api_workflow_jobs_url(v1_module):
    return v1_module.workflow_jobs


@pytest.fixture(scope="class")
def api_workflow_jobs_pg(api_workflow_jobs_url):
    return api_workflow_jobs_url.get()


# /api/v1/workflow_job_nodes
@pytest.fixture(scope="class")
def api_workflow_job_nodes_url(v1_module):
    return v1_module.workflow_job_nodes


@pytest.fixture(scope="class")
def api_workflow_job_nodes_pg(api_workflow_job_nodes_url):
    return api_workflow_job_nodes_url.get()


# /api/v1/settings
@pytest.fixture(scope="class")
def api_settings_url(v1_module):
    return v1_module.settings


@pytest.fixture(scope="class")
def api_settings_pg(api_settings_url):
    return api_settings_url.get()


# /api/v1/settings/all
@pytest.fixture(scope="class")
def api_settings_all_pg(api_settings_pg):
    return api_settings_pg.get_endpoint('all')


# /api/v1/settings/authentication
@pytest.fixture(scope="class")
def api_settings_auth_pg(api_settings_pg):
    return api_settings_pg.get_endpoint('authentication')


# /api/v1/settings/azuread-oauth2
@pytest.fixture(scope="class")
def api_settings_azuread_pg(api_settings_pg):
    return api_settings_pg.get_endpoint('azuread-oauth2')


# /api/v1/settings/changed
@pytest.fixture(scope="class")
def api_settings_changed_pg(api_settings_pg):
    return api_settings_pg.get_endpoint('changed')


# /api/v1/settings/github
@pytest.fixture(scope="class")
def api_settings_github_pg(api_settings_pg):
    return api_settings_pg.get_endpoint('github')


# /api/v1/settings/github-org
@pytest.fixture(scope="class")
def api_settings_github_org_pg(api_settings_pg):
    return api_settings_pg.get_endpoint('github-org')


# /api/v1/settings/github-team
@pytest.fixture(scope="class")
def api_settings_github_team_pg(api_settings_pg):
    return api_settings_pg.get_endpoint('github-team')


# /api/v1/settings/google-oauth2
@pytest.fixture(scope="class")
def api_settings_google_pg(api_settings_pg):
    return api_settings_pg.get_endpoint('google-oauth2')


# /api/v1/settings/jobs
@pytest.fixture(scope="class")
def api_settings_jobs_pg(api_settings_pg):
    return api_settings_pg.get_endpoint('jobs')


# /api/v1/settings/ldap
@pytest.fixture(scope="class")
def api_settings_ldap_pg(api_settings_pg):
    return api_settings_pg.get_endpoint('ldap')


# /api/v1/settings/radius
@pytest.fixture(scope="class")
def api_settings_radius_pg(api_settings_pg):
    return api_settings_pg.get_endpoint('radius')


# /api/v1/settings/saml
@pytest.fixture(scope="class")
def api_settings_saml_pg(api_settings_pg):
    return api_settings_pg.get_endpoint('saml')


# /api/v1/settings/system
@pytest.fixture(scope="class")
def api_settings_system_pg(api_settings_pg):
    return api_settings_pg.get_endpoint('system')


# /api/v1/settings/tacasplus
@pytest.fixture(scope="class")
def api_settings_tacacsplus_pg(api_settings_pg):
    return api_settings_pg.get_endpoint('tacacsplus')


# /api/v1/settings/ui
@pytest.fixture(scope="class")
def api_settings_ui_pg(api_settings_pg):
    return api_settings_pg.get_endpoint('ui')


# /api/v1/settings/user
@pytest.fixture(scope="class")
def api_settings_user_pg(api_settings_pg):
    return api_settings_pg.get_endpoint('user')


# /api/v1/settings/user-defaults
@pytest.fixture(scope="class")
def api_settings_user_defaults_pg(api_settings_pg):
    return api_settings_pg.get_endpoint('user-defaults')
