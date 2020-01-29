from awxkit.awx import version_cmp
from awxkit.api import get_registered_page
from awxkit.config import config as qe_config
import pytest
from urllib.parse import urlparse


@pytest.fixture(scope='session')
def api(connection):
    return get_registered_page('/api/')(connection).get()


@pytest.fixture(scope='session')
def available_versions(api):
    return api.available_versions


@pytest.fixture(scope='session')
def get_api_version(available_versions):
    def _get_api_version(desired_version):
        if desired_version not in available_versions:
            raise Exception("Requested tower version '{0}' not available.  Choices include: {1}"
                            .format(desired_version, available_versions))
        return available_versions.get(desired_version)
    return _get_api_version


@pytest.fixture(scope="class")
def api_v2_url(get_api_version):
    return get_api_version('v2')


@pytest.fixture(scope="class")
def api_v2_pg(connection, api_v2_url):
    return get_registered_page(api_v2_url)(connection, endpoint=api_v2_url).get()


@pytest.fixture(scope='class')
def v2_class(api_v2_pg):
    return api_v2_pg


@pytest.fixture(scope='session')
def v2_session(connection, get_api_version):
    return get_registered_page(get_api_version('v2'))(connection, endpoint=get_api_version('v2')).get()


@pytest.fixture(scope='session')
def v2_module(connection, get_api_version):
    return get_registered_page(get_api_version('v2'))(connection, endpoint=get_api_version('v2')).get()


@pytest.fixture
def v2(v2_class):
    return v2_class


# /api/v2/authtoken
@pytest.fixture(scope="class")
def api_authtoken_url(v2_class):
    return v2_class.authtoken


@pytest.fixture(scope="class")
def api_authtoken_pg(api_authtoken_url):
    return api_authtoken_url.get()


@pytest.fixture(scope="class")
def authtoken(v2_class):
    """Logs in to the application with default credentials"""
    if qe_config.use_sessions:
        v2_class.load_session()
        return v2_class.connection.session_id
    token = v2_class.get_authtoken()
    v2_class.connection.login(token=token)
    return token


@pytest.fixture(scope="session")
def session_authtoken(v2_session):
    """Logs in to the application with default credentials"""
    if qe_config.use_sessions:
        v2_session.load_session()
        return v2_session.connection.session_id
    token = v2_session.get_authtoken()
    v2_session.connection.login(token=token)
    return token


@pytest.fixture(scope="module")
def module_authtoken(v2_module):
    """Logs in to the application with default credentials"""
    if qe_config.use_sessions:
        v2_module.load_session()
        return v2_module.connection.session_id
    token = v2_module.get_authtoken()
    v2_session.connection.login(token=token)
    return token

@pytest.fixture(scope="class")
def oauth2_authtoken(v2_class):
    """Logs in to the application with default credentials"""
    token = v2_class.get_oauth2_token()
    return token


@pytest.fixture(scope="session")
def session_oauth2_authtoken(v2_session):
    """Logs in to the application with default credentials"""
    token = v2_session.get_oauth2_token()
    return token


@pytest.fixture(scope="module")
def module_oauth2_authtoken(v2_module):
    """Logs in to the application with default credentials"""
    token = v2_module.get_oauth2_token()
    return token


# /api/v2/dashboard
@pytest.fixture(scope="class")
def api_dashboard_url(v2_class):
    return v2_class.dashboard


@pytest.fixture(scope="class")
def api_dashboard_pg(api_dashboard_url):
    return api_dashboard_url.get()


# /api/v2/ping
@pytest.fixture(scope="class")
def api_ping_url(v2_class):
    return v2_class.ping


@pytest.fixture(scope="class")
def api_ping_pg(api_ping_url):
    return api_ping_url.get()


# /api/v2/config
@pytest.fixture(scope="class")
def api_config_url(v2_class):
    return v2_class.config


@pytest.fixture(scope="class")
def api_config_pg(api_config_url):
    return api_config_url.get()


@pytest.fixture(scope="class")
def tower_version(api_config_pg):
    return api_config_pg.version


@pytest.fixture(scope="class")
def tower_version_cmp(request, tower_version):
    def func(x):
        return version_cmp(tower_version, x)
    return func


@pytest.fixture(scope='class')
def ansible_version(api_config_pg):
    """Returns the ansible version of the system under test."""
    return api_config_pg.get().ansible_version


@pytest.fixture(scope='session')
def ansible_version_cmp(request, v2_session):
    def func(x):
        ansible_version = v2_session.config.get().ansible_version
        return version_cmp(ansible_version, x)
    return func


@pytest.fixture(scope="class")
def awx_config(v2_class):
    return v2_class.config.get()


# /api/v2/me
@pytest.fixture(scope="class")
def api_me_url(v2_class):
    return v2_class.me


@pytest.fixture(scope="class")
def api_me_pg(api_me_url):
    return api_me_url.get()


# /api/v2/organizations
@pytest.fixture(scope="class")
def api_organizations_url(v2_class):
    return v2_class.organizations


@pytest.fixture(scope="class")
def api_organizations_pg(api_organizations_url):
    return api_organizations_url.get()


# /api/v2/users
@pytest.fixture(scope="class")
def api_users_url(v2_class):
    return v2_class.users


@pytest.fixture(scope="class")
def api_users_pg(api_users_url):
    return api_users_url.get()


# /api/v2/teams
@pytest.fixture(scope="class")
def api_teams_url(v2_class):
    return v2_class.teams


@pytest.fixture(scope="class")
def api_teams_pg(api_teams_url):
    return api_teams_url.get()


# /api/v2/projects
@pytest.fixture(scope="class")
def api_projects_url(v2_class):
    return v2_class.projects


@pytest.fixture(scope="class")
def api_projects_pg(api_projects_url):
    return api_projects_url.get()


# /api/v2/project_updates
@pytest.fixture(scope="class")
def api_project_updates_url(v2_class):
    return v2_class.project_updates


@pytest.fixture(scope="class")
def api_project_updates_pg(api_project_updates_url):
    return api_project_updates_url.get()


# /api/v2/activity_stream
@pytest.fixture(scope="class")
def api_activity_stream_url(v2_class):
    return v2_class.activity_stream


@pytest.fixture(scope="class")
def api_activity_stream_pg(api_activity_stream_url):
    return api_activity_stream_url.get()


# /api/v2/credentials
@pytest.fixture(scope="class")
def api_credentials_url(v2_class):
    return v2_class.credentials


@pytest.fixture(scope="class")
def api_credentials_pg(api_credentials_url):
    return api_credentials_url.get()


# /api/v2/inventory
@pytest.fixture(scope="class")
def api_inventories_url(v2_class):
    return v2_class.inventory


@pytest.fixture(scope="class")
def api_inventories_pg(api_inventories_url):
    return api_inventories_url.get()


# /api/v2/inventory_updates
@pytest.fixture(scope="class")
def api_inventory_updates_url(v2_class):
    return v2_class.inventory_updates


@pytest.fixture(scope="class")
def api_inventory_updates_pg(api_inventory_updates_url):
    return api_inventory_updates_url.get()


# /api/v2/inventory_sources
@pytest.fixture(scope="class")
def api_inventory_sources_url(v2_class):
    return v2_class.inventory_sources


@pytest.fixture(scope="class")
def api_inventory_sources_pg(api_inventory_sources_url):
    return api_inventory_sources_url.get()


# /api/v2/inventory_scripts
@pytest.fixture(scope="class")
def api_inventory_scripts_url(v2_class):
    return v2_class.inventory_scripts


@pytest.fixture(scope="class")
def api_inventory_scripts_pg(api_inventory_scripts_url):
    return api_inventory_scripts_url.get()


# /api/v2/groups
@pytest.fixture(scope="class")
def api_groups_url(v2_class):
    return v2_class.groups


@pytest.fixture(scope="class")
def api_groups_pg(api_groups_url):
    return api_groups_url.get()


# /api/v2/hosts
@pytest.fixture(scope="class")
def api_hosts_url(v2_class):
    return v2_class.hosts


@pytest.fixture(scope="class")
def api_hosts_pg(api_hosts_url):
    return api_hosts_url.get()


# /api/v2/job_templates
@pytest.fixture(scope="class")
def api_job_templates_url(v2_class):
    return v2_class.job_templates


@pytest.fixture(scope="class")
def api_job_templates_pg(api_job_templates_url):
    return api_job_templates_url.get()


# /api/v2/schedules
@pytest.fixture(scope="class")
def api_schedules_url(v2_class):
    return v2_class.schedules


@pytest.fixture(scope="class")
def api_schedules_pg(api_schedules_url):
    return api_schedules_url.get()


# /api/v2/jobs
@pytest.fixture(scope="class")
def api_jobs_url(v2_class):
    return v2_class.jobs


@pytest.fixture(scope="class")
def api_jobs_pg(api_jobs_url):
    return api_jobs_url.get()


# /api/v2/unified_jobs
@pytest.fixture(scope="class")
def api_unified_jobs_url(v2_class):
    return v2_class.unified_jobs


@pytest.fixture(scope="class")
def api_unified_jobs_pg(api_unified_jobs_url):
    return api_unified_jobs_url.get()


# /api/v2/unified_job_templates
@pytest.fixture(scope="class")
def api_unified_job_templates_url(v2_class):
    return v2_class.unified_job_templates


@pytest.fixture(scope="class")
def api_unified_job_templates_pg(api_unified_job_templates_url):
    return api_unified_job_templates_url.get()


# /api/v2/system_jobs
@pytest.fixture(scope="class")
def api_system_jobs_url(v2_class):
    return v2_class.system_jobs


@pytest.fixture(scope="class")
def api_system_jobs_pg(api_system_jobs_url):
    return api_system_jobs_url.get()


# /api/v2/system_job_templates
@pytest.fixture(scope="class")
def api_system_job_templates_url(v2_class):
    return v2_class.system_job_templates


@pytest.fixture(scope="class")
def api_system_job_templates_pg(api_system_job_templates_url):
    return api_system_job_templates_url.get()


# /api/v2/ad_hoc_commands
@pytest.fixture(scope="class")
def api_ad_hoc_commands_url(v2_class):
    return v2_class.ad_hoc_commands


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


# /api/v2/notifications
@pytest.fixture(scope="class")
def api_notifications_url(v2_class):
    return v2_class.notifications


@pytest.fixture(scope="class")
def api_notifications_pg(api_notifications_url):
    return api_notifications_url.get()


# /api/v2/notification_templates
@pytest.fixture(scope="class")
def api_notification_templates_url(v2_class):
    return v2_class.notification_templates


@pytest.fixture(scope="class")
def api_notification_templates_pg(api_notification_templates_url):
    return api_notification_templates_url.get()


# /api/v2/labels
@pytest.fixture(scope="class")
def api_labels_url(v2_class):
    return v2_class.labels


@pytest.fixture(scope="class")
def api_labels_pg(api_labels_url):
    return api_labels_url.get()


# /api/v2/roles
@pytest.fixture(scope="class")
def api_roles_url(v2_class):
    return v2_class.roles


@pytest.fixture(scope="class")
def api_roles_pg(api_roles_url):
    return api_roles_url.get()


# /api/v2/workflow_job_templates
@pytest.fixture(scope="class")
def api_workflow_job_templates_url(v2_class):
    return v2_class.workflow_job_templates


@pytest.fixture(scope="class")
def api_workflow_job_templates_pg(api_workflow_job_templates_url):
    return api_workflow_job_templates_url.get()


# /api/v2/workflow_job_template_nodes
@pytest.fixture(scope="class")
def api_workflow_job_template_nodes_url(v2_class):
    return v2_class.workflow_job_template_nodes


@pytest.fixture(scope="class")
def api_workflow_job_template_nodes_pg(api_workflow_job_template_nodes_url):
    return api_workflow_job_template_nodes_url.get()


# /api/v2/workflow_jobs
@pytest.fixture(scope="class")
def api_workflow_jobs_url(v2_class):
    return v2_class.workflow_jobs


@pytest.fixture(scope="class")
def api_workflow_jobs_pg(api_workflow_jobs_url):
    return api_workflow_jobs_url.get()


# /api/v2/workflow_job_nodes
@pytest.fixture(scope="class")
def api_workflow_job_nodes_url(v2_class):
    return v2_class.workflow_job_nodes


@pytest.fixture(scope="class")
def api_workflow_job_nodes_pg(api_workflow_job_nodes_url):
    return api_workflow_job_nodes_url.get()


# /api/v2/settings
@pytest.fixture(scope="class")
def api_settings_url(v2_class):
    return v2_class.settings


@pytest.fixture(scope="class")
def api_settings_pg(api_settings_url):
    return api_settings_url.get()


# /api/v2/settings/all
@pytest.fixture(scope="class")
def api_settings_all_pg(api_settings_pg):
    return api_settings_pg.get_endpoint('all')


# /api/v2/settings/authentication
@pytest.fixture(scope="class")
def api_settings_auth_pg(api_settings_pg):
    return api_settings_pg.get_endpoint('authentication')


# /api/v2/settings/azuread-oauth2
@pytest.fixture(scope="class")
def api_settings_azuread_pg(api_settings_pg):
    return api_settings_pg.get_endpoint('azuread-oauth2')


# /api/v2/settings/changed
@pytest.fixture(scope="class")
def api_settings_changed_pg(api_settings_pg):
    return api_settings_pg.get_endpoint('changed')


# /api/v2/settings/github
@pytest.fixture(scope="class")
def api_settings_github_pg(api_settings_pg):
    return api_settings_pg.get_endpoint('github')


# /api/v2/settings/github-org
@pytest.fixture(scope="class")
def api_settings_github_org_pg(api_settings_pg):
    return api_settings_pg.get_endpoint('github-org')


# /api/v2/settings/github-team
@pytest.fixture(scope="class")
def api_settings_github_team_pg(api_settings_pg):
    return api_settings_pg.get_endpoint('github-team')


# /api/v2/settings/google-oauth2
@pytest.fixture(scope="class")
def api_settings_google_pg(api_settings_pg):
    return api_settings_pg.get_endpoint('google-oauth2')


# /api/v2/settings/jobs
@pytest.fixture(scope="class")
def api_settings_jobs_pg(api_settings_pg):
    return api_settings_pg.get_endpoint('jobs')


# /api/v2/settings/ldap
@pytest.fixture(scope="class")
def api_settings_ldap_pg(api_settings_pg):
    return api_settings_pg.get_endpoint('ldap')


# /api/v2/settings/radius
@pytest.fixture(scope="class")
def api_settings_radius_pg(api_settings_pg):
    return api_settings_pg.get_endpoint('radius')


# /api/v2/settings/saml
@pytest.fixture(scope="class")
def api_settings_saml_pg(api_settings_pg):
    return api_settings_pg.get_endpoint('saml')


# /api/v2/settings/system
@pytest.fixture(scope="class")
def api_settings_system_pg(api_settings_pg):
    return api_settings_pg.get_endpoint('system')


# /api/v2/settings/tacasplus
@pytest.fixture(scope="class")
def api_settings_tacacsplus_pg(api_settings_pg):
    return api_settings_pg.get_endpoint('tacacsplus')


# /api/v2/settings/ui
@pytest.fixture(scope="class")
def api_settings_ui_pg(api_settings_pg):
    return api_settings_pg.get_endpoint('ui')


# /api/v2/settings/user
@pytest.fixture(scope="class")
def api_settings_user_pg(api_settings_pg):
    return api_settings_pg.get_endpoint('user')


# /api/v2/settings/user-defaults
@pytest.fixture(scope="class")
def api_settings_user_defaults_pg(api_settings_pg):
    return api_settings_pg.get_endpoint('user-defaults')

# /api/v2/settings/logging
@pytest.fixture(scope="class")
def api_settings_logging_pg(api_settings_pg):
    return api_settings_pg.get_endpoint('logging')


@pytest.fixture(scope='session')
def tower_baseurl(is_docker, is_openshift_cluster):
    base_url = urlparse(qe_config.base_url)
    scheme = 'http' if base_url.scheme is None else base_url.scheme
    hostname = base_url.hostname
    if is_docker and not is_openshift_cluster:
        hostname = 'towerhost'
    return '{0}://{1}'.format(scheme, hostname)
