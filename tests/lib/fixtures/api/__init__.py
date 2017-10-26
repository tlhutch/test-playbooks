from towerkit.api import get_registered_page
import towerkit.tower
import pytest


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
            raise(Exception("Requested tower version '{0}' not available.  Choices include: {1}"
                            .format(desired_version, available_versions)))
        return available_versions.get(desired_version)
    return _get_api_version


@pytest.fixture(scope="class")
def api_v1_url(get_api_version):
    return get_api_version('v1')


@pytest.fixture(scope="class")
def api_v1_pg(connection, api_v1_url):
    return get_registered_page(api_v1_url)(connection, endpoint=api_v1_url).get()


@pytest.fixture(scope='class')
def v1_class(api_v1_pg):
    return api_v1_pg


@pytest.fixture
def v1(v1_class):
    return v1_class


@pytest.fixture(scope="class")
def api_v2_url(get_api_version):
    return get_api_version('v2')


@pytest.fixture(scope="class")
def api_v2_pg(connection, api_v2_url):
    return get_registered_page(api_v2_url)(connection, endpoint=api_v2_url).get()


@pytest.fixture(scope='class')
def v2_class(api_v2_pg):
    return api_v2_pg


@pytest.fixture
def v2(v2_class):
    return v2_class


# /api/v1/authtoken
@pytest.fixture(scope="class")
def api_authtoken_url(v1_class):
    return v1_class.authtoken


@pytest.fixture(scope="class")
def api_authtoken_pg(api_authtoken_url):
    return api_authtoken_url.get()


@pytest.fixture(scope="class")
def authtoken(connection, v1_class):
    """Logs in to the application with default credentials"""
    authtoken = v1_class.get_authtoken()
    connection.login(token=authtoken)
    return authtoken


# /api/v1/dashboard
@pytest.fixture(scope="class")
def api_dashboard_url(v1_class):
    return v1_class.dashboard


@pytest.fixture(scope="class")
def api_dashboard_pg(api_dashboard_url):
    return api_dashboard_url.get()


# /api/v1/ping
@pytest.fixture(scope="class")
def api_ping_url(v1_class):
    return v1_class.ping


@pytest.fixture(scope="class")
def api_ping_pg(api_ping_url):
    return api_ping_url.get()


# /api/v1/config
@pytest.fixture(scope="class")
def api_config_url(v1_class):
    return v1_class.config


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
def awx_config(v1_class):
    return v1_class.config.get()


# /api/v1/me
@pytest.fixture(scope="class")
def api_me_url(v1_class):
    return v1_class.me


@pytest.fixture(scope="class")
def api_me_pg(api_me_url):
    return api_me_url.get()


# /api/v1/organizations
@pytest.fixture(scope="class")
def api_organizations_url(v1_class):
    return v1_class.organizations


@pytest.fixture(scope="class")
def api_organizations_pg(api_organizations_url):
    return api_organizations_url.get()


# /api/v1/users
@pytest.fixture(scope="class")
def api_users_url(v1_class):
    return v1_class.users


@pytest.fixture(scope="class")
def api_users_pg(api_users_url):
    return api_users_url.get()


# /api/v1/teams
@pytest.fixture(scope="class")
def api_teams_url(v1_class):
    return v1_class.teams


@pytest.fixture(scope="class")
def api_teams_pg(api_teams_url):
    return api_teams_url.get()


# /api/v1/projects
@pytest.fixture(scope="class")
def api_projects_url(v1_class):
    return v1_class.projects


@pytest.fixture(scope="class")
def api_projects_pg(api_projects_url):
    return api_projects_url.get()


# /api/v1/project_updates
@pytest.fixture(scope="class")
def api_project_updates_url(v1_class):
    return v1_class.project_updates


@pytest.fixture(scope="class")
def api_project_updates_pg(api_project_updates_url):
    return api_project_updates_url.get()


# /api/v1/activity_stream
@pytest.fixture(scope="class")
def api_activity_stream_url(v1_class):
    return v1_class.activity_stream


@pytest.fixture(scope="class")
def api_activity_stream_pg(api_activity_stream_url):
    return api_activity_stream_url.get()


# /api/v1/credentials
@pytest.fixture(scope="class")
def api_credentials_url(v1_class):
    return v1_class.credentials


@pytest.fixture(scope="class")
def api_credentials_pg(api_credentials_url):
    return api_credentials_url.get()


# /api/v1/inventory
@pytest.fixture(scope="class")
def api_inventories_url(v1_class):
    return v1_class.inventory


@pytest.fixture(scope="class")
def api_inventories_pg(api_inventories_url):
    return api_inventories_url.get()


# /api/v1/inventory_updates
@pytest.fixture(scope="class")
def api_inventory_updates_url(v1_class):
    return v1_class.inventory_updates


@pytest.fixture(scope="class")
def api_inventory_updates_pg(api_inventory_updates_url):
    return api_inventory_updates_url.get()


# /api/v1/inventory_sources
@pytest.fixture(scope="class")
def api_inventory_sources_url(v1_class):
    return v1_class.inventory_sources


@pytest.fixture(scope="class")
def api_inventory_sources_pg(api_inventory_sources_url):
    return api_inventory_sources_url.get()


# /api/v1/inventory_scripts
@pytest.fixture(scope="class")
def api_inventory_scripts_url(v1_class):
    return v1_class.inventory_scripts


@pytest.fixture(scope="class")
def api_inventory_scripts_pg(api_inventory_scripts_url):
    return api_inventory_scripts_url.get()


# /api/v1/groups
@pytest.fixture(scope="class")
def api_groups_url(v1_class):
    return v1_class.groups


@pytest.fixture(scope="class")
def api_groups_pg(api_groups_url):
    return api_groups_url.get()


# /api/v1/hosts
@pytest.fixture(scope="class")
def api_hosts_url(v1_class):
    return v1_class.hosts


@pytest.fixture(scope="class")
def api_hosts_pg(api_hosts_url):
    return api_hosts_url.get()


# /api/v1/job_templates
@pytest.fixture(scope="class")
def api_job_templates_url(v1_class):
    return v1_class.job_templates


@pytest.fixture(scope="class")
def api_job_templates_pg(api_job_templates_url):
    return api_job_templates_url.get()


# /api/v1/schedules
@pytest.fixture(scope="class")
def api_schedules_url(v1_class):
    return v1_class.schedules


@pytest.fixture(scope="class")
def api_schedules_pg(api_schedules_url):
    return api_schedules_url.get()


# /api/v1/jobs
@pytest.fixture(scope="class")
def api_jobs_url(v1_class):
    return v1_class.jobs


@pytest.fixture(scope="class")
def api_jobs_pg(api_jobs_url):
    return api_jobs_url.get()


# /api/v1/unified_jobs
@pytest.fixture(scope="class")
def api_unified_jobs_url(v1_class):
    return v1_class.unified_jobs


@pytest.fixture(scope="class")
def api_unified_jobs_pg(api_unified_jobs_url):
    return api_unified_jobs_url.get()


# /api/v1/unified_job_templates
@pytest.fixture(scope="class")
def api_unified_job_templates_url(v1_class):
    return v1_class.unified_job_templates


@pytest.fixture(scope="class")
def api_unified_job_templates_pg(api_unified_job_templates_url):
    return api_unified_job_templates_url.get()


# /api/v1/system_jobs
@pytest.fixture(scope="class")
def api_system_jobs_url(v1_class):
    return v1_class.system_jobs


@pytest.fixture(scope="class")
def api_system_jobs_pg(api_system_jobs_url):
    return api_system_jobs_url.get()


# /api/v1/system_job_templates
@pytest.fixture(scope="class")
def api_system_job_templates_url(v1_class):
    return v1_class.system_job_templates


@pytest.fixture(scope="class")
def api_system_job_templates_pg(api_system_job_templates_url):
    return api_system_job_templates_url.get()


# /api/v1/ad_hoc_commands
@pytest.fixture(scope="class")
def api_ad_hoc_commands_url(v1_class):
    return v1_class.ad_hoc_commands


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
def api_notifications_url(v1_class):
    return v1_class.notifications


@pytest.fixture(scope="class")
def api_notifications_pg(api_notifications_url):
    return api_notifications_url.get()


# /api/v1/notification_templates
@pytest.fixture(scope="class")
def api_notification_templates_url(v1_class):
    return v1_class.notification_templates


@pytest.fixture(scope="class")
def api_notification_templates_pg(api_notification_templates_url):
    return api_notification_templates_url.get()


# /api/v1/labels
@pytest.fixture(scope="class")
def api_labels_url(v1_class):
    return v1_class.labels


@pytest.fixture(scope="class")
def api_labels_pg(api_labels_url):
    return api_labels_url.get()


# /api/v1/roles
@pytest.fixture(scope="class")
def api_roles_url(v1_class):
    return v1_class.roles


@pytest.fixture(scope="class")
def api_roles_pg(api_roles_url):
    return api_roles_url.get()


# /api/v1/workflow_job_templates
@pytest.fixture(scope="class")
def api_workflow_job_templates_url(v1_class):
    return v1_class.workflow_job_templates


@pytest.fixture(scope="class")
def api_workflow_job_templates_pg(api_workflow_job_templates_url):
    return api_workflow_job_templates_url.get()


# /api/v1/workflow_job_template_nodes
@pytest.fixture(scope="class")
def api_workflow_job_template_nodes_url(v1_class):
    return v1_class.workflow_job_template_nodes


@pytest.fixture(scope="class")
def api_workflow_job_template_nodes_pg(api_workflow_job_template_nodes_url):
    return api_workflow_job_template_nodes_url.get()


# /api/v1/workflow_jobs
@pytest.fixture(scope="class")
def api_workflow_jobs_url(v1_class):
    return v1_class.workflow_jobs


@pytest.fixture(scope="class")
def api_workflow_jobs_pg(api_workflow_jobs_url):
    return api_workflow_jobs_url.get()


# /api/v1/workflow_job_nodes
@pytest.fixture(scope="class")
def api_workflow_job_nodes_url(v1_class):
    return v1_class.workflow_job_nodes


@pytest.fixture(scope="class")
def api_workflow_job_nodes_pg(api_workflow_job_nodes_url):
    return api_workflow_job_nodes_url.get()


# /api/v1/settings
@pytest.fixture(scope="class")
def api_settings_url(v1_class):
    return v1_class.settings


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
