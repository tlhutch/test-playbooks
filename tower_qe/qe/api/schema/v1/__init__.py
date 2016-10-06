import logging
import glob
import os

from qe.api.schema import Schema_Base
from qe.api import resources
import qe.yaml_file


# FIXME - cache all schema files
schema_files = glob.glob(os.path.join(__path__[0], '*.yml'))


class Awx_Schema(Schema_Base):
    version = 'v1'
    resource = resources.api
    _file_cache = {}

    def load_file(self, filename):
        try:
            if filename in self._file_cache:
                return self._file_cache[filename]

            loaded_file = qe.yaml_file.load_file(os.path.join(__path__[0], filename))
            self._file_cache[filename] = loaded_file
            return loaded_file
        except Exception, e:
            logging.debug(e)
            return {}

    @property
    def put(self):
        return self.load_file('empty.yml')

    @property
    def patch(self):
        return self.load_file('empty.yml')

    @property
    def post(self):
        return self.load_file('empty.yml')

    @property
    def head(self):
        return self.load_file('empty.yml')

    @property
    def get(self):
        return self.load_file('api.yml')

    @property
    def options(self):
        return self.load_file('options.yml')

    @property
    def bad_request(self):
        return self.load_file('errors/400.yml')

    @property
    def unauthorized(self):
        return self.load_file('errors/401.yml')

    @property
    def payment_required(self):
        return self.load_file('errors/402.yml')

    @property
    def forbidden(self):
        return self.load_file('errors/403.yml')

    @property
    def method_not_allowed(self):
        return self.load_file('errors/405.yml')

    @property
    def license_exceeded(self):
        return self.load_file('errors/license_exceeded.yml')


class Awx_Schema_v1(Awx_Schema):
    resource = resources.v1

    @property
    def get(self):
        return self.load_file('api_v1.yml')


class Awx_Schema_Settings(Awx_Schema):
    resource = resources.v1_settings

    @property
    def get(self):
        return self.load_file('settings/main.yml')


class Awx_Schema_Settings_All(Awx_Schema):
    resource = resources.v1_settings_all

    @property
    def get(self):
        return self.load_file('settings/settings_all.yml')

    @property
    def put(self):
        return self.load_file('settings/settings_all.yml')

    @property
    def patch(self):
        return self.load_file('settings/settings_all.yml')


class Awx_Schema_Settings_Authentication(Awx_Schema):
    resource = resources.v1_settings_authentication

    @property
    def get(self):
        return self.load_file('settings/settings_authentication.yml')

    @property
    def put(self):
        return self.load_file('settings/settings_authentication.yml')

    @property
    def patch(self):
        return self.load_file('settings/settings_authentication.yml')


class Awx_Schema_Settings_Changed(Awx_Schema):
    resource = resources.v1_settings_changed

    @property
    def get(self):
        return self.load_file('settings/settings_changed.yml')

    @property
    def put(self):
        return self.load_file('settings/settings_changed.yml')

    @property
    def patch(self):
        return self.load_file('settings/settings_changed.yml')


class Awx_Schema_Settings_Github(Awx_Schema):
    resource = resources.v1_settings_github

    @property
    def get(self):
        return self.load_file('settings/settings_github.yml')

    @property
    def put(self):
        return self.load_file('settings/settings_github.yml')

    @property
    def patch(self):
        return self.load_file('settings/settings_github.yml')


class Awx_Schema_Settings_Github_Org(Awx_Schema):
    resource = resources.v1_settings_github_org

    @property
    def get(self):
        return self.load_file('settings/settings_github_org.yml')

    @property
    def put(self):
        return self.load_file('settings/settings_github_org.yml')

    @property
    def patch(self):
        return self.load_file('settings/settings_github_org.yml')


class Awx_Schema_Settings_Github_Team(Awx_Schema):
    resource = resources.v1_settings_github_team

    @property
    def get(self):
        return self.load_file('settings/settings_github_team.yml')

    @property
    def put(self):
        return self.load_file('settings/settings_github_team.yml')

    @property
    def patch(self):
        return self.load_file('settings/settings_github_team.yml')


class Awx_Schema_Settings_Google_OAuth2(Awx_Schema):
    resource = resources.v1_settings_google_oauth2

    @property
    def get(self):
        return self.load_file('settings/settings_google_oauth2.yml')

    @property
    def put(self):
        return self.load_file('settings/settings_google_oauth2.yml')

    @property
    def patch(self):
        return self.load_file('settings/settings_google_oauth2.yml')


class Awx_Schema_Settings_Jobs(Awx_Schema):
    resource = resources.v1_settings_jobs

    @property
    def get(self):
        return self.load_file('settings/settings_jobs.yml')

    @property
    def put(self):
        return self.load_file('settings/settings_jobs.yml')

    @property
    def patch(self):
        return self.load_file('settings/settings_jobs.yml')


class Awx_Schema_Settings_LDAP(Awx_Schema):
    resource = resources.v1_settings_ldap

    @property
    def get(self):
        return self.load_file('settings/settings_ldap.yml')

    @property
    def put(self):
        return self.load_file('settings/settings_ldap.yml')

    @property
    def patch(self):
        return self.load_file('settings/settings_ldap.yml')


class Awx_Schema_Settings_RADIUS(Awx_Schema):
    resource = resources.v1_settings_radius

    @property
    def get(self):
        return self.load_file('settings/settings_radius.yml')

    @property
    def put(self):
        return self.load_file('settings/settings_radius.yml')

    @property
    def patch(self):
        return self.load_file('settings/settings_radius.yml')


class Awx_Schema_Settings_SAML(Awx_Schema):
    resource = resources.v1_settings_saml

    @property
    def get(self):
        return self.load_file('settings/settings_saml.yml')

    @property
    def put(self):
        return self.load_file('settings/settings_saml.yml')

    @property
    def patch(self):
        return self.load_file('settings/settings_saml.yml')


class Awx_Schema_Settings_System(Awx_Schema):
    resource = resources.v1_settings_system

    @property
    def get(self):
        return self.load_file('settings/settings_system.yml')

    @property
    def put(self):
        return self.load_file('settings/settings_system.yml')

    @property
    def patch(self):
        return self.load_file('settings/settings_system.yml')


class Awx_Schema_Settings_UI(Awx_Schema):
    resource = resources.v1_settings_ui

    @property
    def get(self):
        return self.load_file('settings/settings_ui.yml')

    @property
    def put(self):
        return self.load_file('settings/settings_ui.yml')

    @property
    def patch(self):
        return self.load_file('settings/settings_ui.yml')


class Awx_Schema_Settings_User(Awx_Schema):
    resource = resources.v1_settings_user

    @property
    def get(self):
        return self.load_file('settings/settings_user.yml')

    @property
    def put(self):
        return self.load_file('settings/settings_user.yml')

    @property
    def patch(self):
        return self.load_file('settings/settings_user.yml')


class Awx_Schema_Settings_User_Defaults(Awx_Schema):
    resource = resources.v1_settings_user_defaults

    @property
    def get(self):
        return self.load_file('settings/settings_user_defaults.yml')

    @property
    def put(self):
        return self.load_file('settings/settings_user_defaults.yml')

    @property
    def patch(self):
        return self.load_file('settings/settings_user_defaults.yml')


class Awx_Schema_Organizations(Awx_Schema):
    resource = resources.v1_organizations

    @property
    def duplicate(self):
        return self.load_file('organizations/duplicate.yml')

    @property
    def get(self):
        return self.load_file('organizations/list.yml')

    @property
    def post(self):
        return self.load_file('organizations/item.yml')


class Awx_Schema_Organization(Awx_Schema_Organizations):
    resource = resources.v1_organization

    @property
    def get(self):
        return self.load_file('organizations/item.yml')

    @property
    def put(self):
        return self.get

    @property
    def patch(self):
        return self.get


class Awx_Schema_Organization_Access_List(Awx_Schema):
    resource = resources.v1_organization_access_list

    @property
    def get(self):
        return self.load_file('access_list/list.yml')


class Awx_Schema_Users(Awx_Schema):
    resource = resources.v1_users

    @property
    def duplicate(self):
        return self.load_file('users/duplicate.yml')

    @property
    def get(self):
        return self.load_file('users/list.yml')

    @property
    def post(self):
        return self.load_file('users/item.yml')


class Awx_Schema_Related_Users(Awx_Schema_Users):
    resource = resources.v1_related_users


class Awx_Schema_User(Awx_Schema_Users):
    resource = resources.v1_user

    @property
    def get(self):
        return self.load_file('users/item.yml')

    @property
    def patch(self):
        return self.get

    @property
    def put(self):
        return self.get


class Awx_Schema_User_Access_List(Awx_Schema):
    resource = resources.v1_user_access_list

    @property
    def get(self):
        return self.load_file('access_list/list.yml')


class Awx_Schema_Team_Users(Awx_Schema_Users):
    resource = resources.v1_team_users


class Awx_Schema_Org_Users(Awx_Schema_Users):
    resource = resources.v1_organization_users


class Awx_Schema_Org_Admins(Awx_Schema_Users):
    resource = resources.v1_organization_admins


class Awx_Schema_Inventories(Awx_Schema):
    resource = resources.v1_inventories

    @property
    def get(self):
        return self.load_file('inventories/list.yml')

    @property
    def post(self):
        return self.load_file('inventories/item.yml')

    @property
    def duplicate(self):
        return self.load_file('inventories/duplicate.yml')


class Awx_Schema_Inventory(Awx_Schema_Inventories):
    resource = resources.v1_inventory

    @property
    def get(self):
        return self.load_file('inventories/item.yml')

    @property
    def put(self):
        return self.get

    @property
    def patch(self):
        return self.get


class Awx_Schema_Organization_Inventories(Awx_Schema_Inventories):
    resource = resources.v1_organization_inventories


class Awx_Schema_Inventory_Access_List(Awx_Schema):
    resource = resources.v1_inventory_access_list

    @property
    def get(self):
        return self.load_file('access_list/list.yml')


class Awx_Schema_Inventory_Tree(Awx_Schema):
    resource = resources.v1_inventory_tree

    @property
    def get(self):
        return self.load_file('tree.yml')


class Awx_Schema_Related_Inventory(Awx_Schema_Inventories):
    resource = resources.v1_related_inventories


class Awx_Schema_Variable_Data(Awx_Schema):
    resource = resources.v1_variable_data

    @property
    def get(self):
        return self.load_file('dict.yml')

    @property
    def put(self):
        return self.get

    @property
    def patch(self):
        return self.get


class Awx_Schema_Groups(Awx_Schema):
    resource = resources.v1_groups

    @property
    def get(self):
        return self.load_file('groups/list.yml')

    @property
    def post(self):
        return self.load_file('groups/item.yml')

    @property
    def duplicate(self):
        return self.load_file('groups/duplicate.yml')


class Awx_Schema_Group(Awx_Schema_Groups):
    resource = resources.v1_group

    @property
    def get(self):
        return self.load_file('groups/item.yml')

    @property
    def put(self):
        return self.get

    @property
    def patch(self):
        return self.get


class Awx_Schema_Group_Access_List(Awx_Schema):
    resource = resources.v1_group_access_list

    @property
    def get(self):
        return self.load_file('access_list/list.yml')


class Awx_Schema_Host_Groups(Awx_Schema_Groups):
    resource = resources.v1_host_groups


class Awx_Schema_Group_Children(Awx_Schema_Groups):
    resource = resources.v1_group_children


class Awx_Schema_Hosts(Awx_Schema):
    resource = resources.v1_hosts

    @property
    def get(self):
        return self.load_file('hosts/list.yml')

    @property
    def post(self):
        return self.load_file('hosts/item.yml')

    @property
    def duplicate(self):
        return self.load_file('hosts/duplicate.yml')


class Awx_Schema_Host(Awx_Schema_Hosts):
    resource = resources.v1_host

    @property
    def get(self):
        return self.load_file('hosts/item.yml')

    @property
    def put(self):
        return self.get

    @property
    def patch(self):
        return self.get


class Awx_Schema_Host_Related_Fact_Versions(Awx_Schema):
    resource = resources.v1_host_related_fact_versions

    @property
    def get(self):
        return self.load_file('fact_versions/list.yml')


class Awx_Schema_Fact_View(Awx_Schema):
    resource = resources.v1_fact_view

    @property
    def get(self):
        return self.load_file('fact_view/item.yml')


class Awx_Schema_Group_Related_Hosts(Awx_Schema_Hosts):
    resource = resources.v1_group_related_hosts


class Awx_Schema_Group_Related_All_Hosts(Awx_Schema_Hosts):
    resource = resources.v1_group_related_all_hosts


class Awx_Schema_Inventory_Related_Hosts(Awx_Schema_Hosts):
    resource = resources.v1_inventory_related_hosts


class Awx_Schema_Inventory_Related_Groups(Awx_Schema_Groups):
    resource = resources.v1_inventory_related_groups


class Awx_Schema_Inventory_Related_Root_Groups(Awx_Schema_Groups):
    resource = resources.v1_inventory_related_root_groups


class Awx_Schema_Inventory_Related_Script(Awx_Schema):
    resource = resources.v1_inventory_related_script

    @property
    def get(self):
        return self.load_file('dict.yml')

    @property
    def put(self):
        return self.get

    @property
    def patch(self):
        return self.get


class Awx_Schema_Credentials(Awx_Schema):
    resource = resources.v1_credentials

    @property
    def get(self):
        return self.load_file('credentials/list.yml')

    @property
    def post(self):
        return self.load_file('credentials/item.yml')

    @property
    def duplicate(self):
        return self.load_file('credentials/duplicate.yml')


class Awx_Schema_Related_Credentials(Awx_Schema_Credentials):
    resource = resources.v1_related_credentials


class Awx_Schema_Credential(Awx_Schema_Credentials):
    resource = resources.v1_credential

    @property
    def get(self):
        return self.load_file('credentials/item.yml')

    @property
    def put(self):
        return self.get

    @property
    def patch(self):
        return self.get


class Awx_Schema_Credential_Access_List(Awx_Schema):
    resource = resources.v1_credential_access_list

    @property
    def get(self):
        return self.load_file('access_list/list.yml')


class Awx_Schema_Credential_Owner_Users(Awx_Schema_Users):
    resource = resources.v1_credential_owner_users


class Awx_Schema_Credential_Owner_Teams(Awx_Schema):
    resource = resources.v1_credential_owner_teams

    @property
    def get(self):
        return self.load_file('teams/list.yml')

    @property
    def post(self):
        return self.load_file('teams/item.yml')

    @property
    def duplicate(self):
        return self.load_file('teams/duplicate.yml')


class Awx_Schema_User_Credentials(Awx_Schema_Credentials):
    resource = resources.v1_user_credentials


class Awx_Schema_User_Permissions(Awx_Schema):
    resource = resources.v1_user_permissions

    @property
    def get(self):
        return self.load_file('permissions/list.yml')

    @property
    def post(self):
        return self.load_file('permissions/item.yml')


class Awx_Schema_Projects(Awx_Schema):
    resource = resources.v1_projects

    @property
    def get(self):
        return self.load_file('projects/list.yml')

    @property
    def post(self):
        return self.load_file('projects/item.yml')

    @property
    def duplicate(self):
        return self.load_file('projects/duplicate.yml')


class Awx_Schema_Project(Awx_Schema_Projects):
    resource = resources.v1_project

    @property
    def get(self):
        return self.load_file('projects/item.yml')

    @property
    def patch(self):
        return self.get

    @property
    def put(self):
        return self.get


class Awx_Schema_Related_Project(Awx_Schema_Projects):
    resource = resources.v1_related_project


class Awx_Schema_Project_Access_List(Awx_Schema):
    resource = resources.v1_project_access_list

    @property
    def get(self):
        return self.load_file('access_list/list.yml')


class Awx_Schema_Org_Projects(Awx_Schema_Projects):
    resource = resources.v1_org_projects


class Awx_Schema_User_Organizations(Awx_Schema_Organizations):
    resource = resources.v1_user_organizations


class Awx_Schema_User_Admin_Organizations(Awx_Schema_Organizations):
    resource = resources.v1_user_admin_organizations


class Awx_Schema_Project_Organizations(Awx_Schema_Organizations):
    resource = resources.v1_project_organizations


class Awx_Schema_Project_Project_Updates(Awx_Schema):
    resource = resources.v1_project_project_updates

    @property
    def get(self):
        return self.load_file('project_updates/list.yml')


class Awx_Schema_Project_Playbooks(Awx_Schema):
    resource = resources.v1_project_playbooks

    @property
    def get(self):
        return self.load_file('list.yml')


class Awx_Schema_Project_Updates(Awx_Schema):
    resource = resources.v1_project_updates

    @property
    def get(self):
        return self.load_file('project_updates/list.yml')


class Awx_Schema_Project_Update(Awx_Schema_Project_Updates):
    resource = resources.v1_project_update

    @property
    def get(self):
        return self.load_file('project_updates/item.yml')


class Awx_Schema_Project_Related_Update(Awx_Schema):
    resource = resources.v1_project_related_update

    @property
    def get(self):
        return self.load_file('projects/update.yml')

    @property
    def post(self):
        return self.load_file('projects/updated.yml')


class Awx_Schema_Project_Update_Cancel(Awx_Schema):
    resource = resources.v1_project_update_cancel

    @property
    def get(self):
        return self.load_file('project_updates/cancel.yml')

    @property
    def post(self):
        return self.load_file('empty.yml')


#
# /unified_job_templates
#
class Awx_Schema_Unified_Job_Templates(Awx_Schema):
    resource = resources.v1_unified_job_templates

    @property
    def get(self):
        return self.load_file('unified_job_templates/list.yml')


class Awx_Schema_Unified_Job_Template(Awx_Schema_Unified_Job_Templates):
    resource = resources.v1_unified_job_template

    @property
    def get(self):
        return self.load_file('unified_job_templates/item.yml')

    @property
    def patch(self):
        return self.get

    @property
    def put(self):
        return self.get


#
# /unified_jobs
#
class Awx_Schema_Unified_Jobs(Awx_Schema):
    resource = resources.v1_unified_jobs

    @property
    def get(self):
        return self.load_file('unified_jobs/list.yml')


class Awx_Schema_Schedules_Jobs(Awx_Schema_Unified_Jobs):
    resource = resources.v1_schedules_jobs


#
# /system_job_templates
#
class Awx_Schema_System_Job_Templates(Awx_Schema):
    resource = resources.v1_system_job_templates

    @property
    def get(self):
        return self.load_file('system_job_templates/list.yml')


class Awx_Schema_System_Job_Template(Awx_Schema_System_Job_Templates):
    resource = resources.v1_system_job_template

    @property
    def get(self):
        return self.load_file('system_job_templates/item.yml')

    @property
    def patch(self):
        return self.get

    @property
    def put(self):
        return self.get


class Awx_Schema_System_Job_Template_Launch(Awx_Schema):
    resource = resources.v1_system_job_template_launch

    @property
    def get(self):
        return self.load_file('system_job_templates/launch.yml')

    @property
    def post(self):
        return self.load_file('system_job_templates/launched.yml')


class Awx_Schema_System_Job_Template_Jobs(Awx_Schema_Unified_Jobs):
    resource = resources.v1_system_job_template_jobs


#
# /system_jobs
#
class Awx_Schema_System_Jobs(Awx_Schema):
    resource = resources.v1_system_jobs

    @property
    def get(self):
        return self.load_file('system_jobs/list.yml')


class Awx_Schema_System_Job(Awx_Schema_System_Jobs):
    resource = resources.v1_system_job

    @property
    def get(self):
        return self.load_file('system_jobs/item.yml')

    @property
    def patch(self):
        return self.post

    @property
    def put(self):
        return self.post


class Awx_Schema_System_Job_Cancel(Awx_Schema):
    resource = resources.v1_system_job_cancel

    @property
    def get(self):
        return self.load_file('jobs/cancel.yml')

    @property
    def post(self):
        return self.load_file('empty.yml')


#
# /job_templates
#
class Awx_Schema_Job_Templates(Awx_Schema):
    resource = resources.v1_job_templates

    @property
    def get(self):
        return self.load_file('job_templates/list.yml')

    @property
    def post(self):
        return self.load_file('job_templates/item.yml')

    @property
    def duplicate(self):
        return self.load_file('job_templates/duplicate.yml')


class Awx_Schema_Job_Template(Awx_Schema_Job_Templates):
    resource = resources.v1_job_template

    @property
    def get(self):
        return self.load_file('job_templates/item.yml')

    @property
    def patch(self):
        return self.get

    @property
    def put(self):
        return self.get


class Awx_Schema_Job_Template_Access_List(Awx_Schema):
    resource = resources.v1_job_template_access_list

    @property
    def get(self):
        return self.load_file('access_list/list.yml')


class Awx_Schema_Job_Template_Launch(Awx_Schema):
    resource = resources.v1_job_template_launch

    @property
    def get(self):
        return self.load_file('job_templates/launch.yml')

    @property
    def post(self):
        return self.load_file('job_templates/launched.yml')


class Awx_Schema_Job_Template_Survey_Spec(Awx_Schema):
    resource = resources.v1_job_template_survey_spec

    @property
    def get(self):
        return self.load_file('job_templates/survey_spec.yml')

    @property
    def post(self):
        return self.load_file('empty.yml')


class Awx_Schema_Related_Job_Templates(Awx_Schema_Job_Templates):
    resource = resources.v1_related_job_templates


class Awx_Schema_Inventory_Scan_Job_Templates(Awx_Schema_Job_Templates):
    resource = resources.v1_inventory_scan_job_templates


#
# /job_template/N/callback/
#
class Awx_Schema_Job_Template_Callback(Awx_Schema):
    resource = resources.v1_job_template_callback

    @property
    def get(self):
        return self.load_file('job_templates/callback.yml')


#
# /jobs
#
class Awx_Schema_Jobs(Awx_Schema):
    resource = resources.v1_jobs

    @property
    def get(self):
        return self.load_file('jobs/list.yml')

    @property
    def post(self):
        return self.load_file('jobs/item.yml')


class Awx_Schema_Job(Awx_Schema_Jobs):
    resource = resources.v1_job

    @property
    def get(self):
        return self.load_file('jobs/item.yml')

    @property
    def patch(self):
        return self.post

    @property
    def put(self):
        return self.post


class Awx_Schema_Job_Cancel(Awx_Schema):
    resource = resources.v1_job_cancel

    @property
    def get(self):
        return self.load_file('jobs/cancel.yml')

    @property
    def post(self):
        return self.load_file('empty.yml')


class Awx_Schema_Job_Start(Awx_Schema):
    resource = resources.v1_job_start

    @property
    def get(self):
        return self.load_file('jobs/start.yml')

    @property
    def post(self):
        return self.load_file('empty.yml')


class Awx_Schema_Job_Relaunch(Awx_Schema):
    resource = resources.v1_job_relaunch

    @property
    def get(self):
        return self.load_file('jobs/relaunch.yml')

    @property
    def post(self):
        return self.load_file('jobs/relaunched.yml')


class Awx_Schema_Job_Host_Summaries(Awx_Schema):
    resource = resources.v1_job_host_summaries

    @property
    def get(self):
        return self.load_file('job_host_summaries/list.yml')


class Awx_Schema_Job_Host_Summary(Awx_Schema_Job_Host_Summaries):
    resource = resources.v1_job_host_summary

    @property
    def get(self):
        return self.load_file('job_host_summaries/item.yml')


class Awx_Schema_Job_Plays(Awx_Schema):
    resource = resources.v1_job_plays

    @property
    def get(self):
        return self.load_file('job_plays/list.yml')


class Awx_Schema_Job_Play(Awx_Schema_Job_Plays):
    resource = resources.v1_job_play

    @property
    def get(self):
        return self.load_file('job_plays/item.yml')


class Awx_Schema_Job_Tasks(Awx_Schema):
    resource = resources.v1_job_tasks

    @property
    def get(self):
        return self.load_file('job_tasks/list.yml')


class Awx_Schema_Job_Task(Awx_Schema_Job_Tasks):
    resource = resources.v1_job_task

    @property
    def get(self):
        return self.load_file('job_tasks/item.yml')


class Awx_Schema_Job_Events(Awx_Schema):
    resource = resources.v1_job_events

    @property
    def get(self):
        return self.load_file('job_events/list.yml')


class Awx_Schema_Job_Job_Events(Awx_Schema_Job_Events):
    resource = resources.v1_job_job_events


class Awx_Schema_Job_Event(Awx_Schema_Job_Events):
    resource = resources.v1_job_event

    @property
    def get(self):
        return self.load_file('job_events/item.yml')


class Awx_Schema_Job_Event_Children(Awx_Schema_Job_Events):
    resource = resources.v1_job_event_children


class Awx_Schema_Job_Stdout(Awx_Schema):
    resource = resources.v1_job_stdout

    @property
    def get(self):
        return self.load_file('job_stdout/item.yml')


#
# /workflow_job_templates
#
class Awx_Schema_Workflow_Job_Templates(Awx_Schema):
    resource = resources.v1_workflow_job_templates

    @property
    def get(self):
        return self.load_file('workflow_job_templates/list.yml')

    @property
    def post(self):
        return self.load_file('workflow_job_templates/item.yml')

    @property
    def duplicate(self):
        return self.load_file('workflow_job_templates/duplicate.yml')


class Awx_Schema_Workflow_Job_Template(Awx_Schema_Workflow_Job_Templates):
    resource = resources.v1_workflow_job_template

    @property
    def get(self):
        return self.load_file('workflow_job_templates/item.yml')

    @property
    def patch(self):
        return self.get

    @property
    def put(self):
        return self.get


class Awx_Schema_Workflow_Job_Template_Workflow_Nodes(Awx_Schema):
    resource = resources.v1_workflow_job_template_workflow_nodes

    @property
    def get(self):
        return self.load_file('workflow_job_template_nodes/list.yml')

    @property
    def post(self):
        return self.load_file('workflow_job_template_nodes/item.yml')

    # Note: Duplicate payloads are actually accepted


class Awx_Schema_Workflow_Job_Template_Launch(Awx_Schema):
    resource = resources.v1_workflow_job_template_launch

    @property
    def get(self):
        return self.load_file('workflow_job_templates/launch.yml')

    @property
    def post(self):
        return self.load_file('workflow_job_templates/launched.yml')


class Awx_Schema_Workflow_Job_Template_Jobs(Awx_Schema):
    resource = resources.v1_workflow_job_template_jobs

    @property
    def get(self):
        return self.load_file('workflow_jobs/list.yml')


#
# /workflow_job_template_nodes
#
class Awx_Schema_Workflow_Job_Template_Nodes(Awx_Schema):
    resource = resources.v1_workflow_job_template_nodes

    @property
    def get(self):
        return self.load_file('workflow_job_template_nodes/list.yml')

    @property
    def post(self):
        return self.load_file('workflow_job_template_nodes/item.yml')

    # Note: Duplicate payloads are actually accepted

    @property
    # Posting {} to workflow_job_template_nodes creates a resource
    # Behavior is being evaluated in https://github.com/ansible/ansible-tower/issues/3552
    def workflow_job_template_node_created(self):
        return self.load_file('workflow_job_template_nodes/item.yml')


class Awx_Schema_Workflow_Job_Template_Node(Awx_Schema_Workflow_Job_Template_Nodes):
    resource = resources.v1_workflow_job_template_node

    @property
    def get(self):
        return self.load_file('workflow_job_template_nodes/item.yml')

    @property
    def patch(self):
        return self.get

    @property
    def put(self):
        return self.get


class Awx_Schema_Workflow_Job_Template_Node_Success_Nodes(Awx_Schema):
    resource = resources.v1_workflow_job_template_node_success_nodes

    @property
    def get(self):
        return self.load_file('workflow_job_template_nodes/list.yml')

    @property
    def post(self):
        return self.load_file('workflow_job_template_nodes/item.yml')

    # Note: Duplicate payloads are actually accepted


class Awx_Schema_Workflow_Job_Template_Node_Failure_Nodes(Awx_Schema):
    resource = resources.v1_workflow_job_template_node_failure_nodes

    @property
    def get(self):
        return self.load_file('workflow_job_template_nodes/list.yml')

    @property
    def post(self):
        return self.load_file('workflow_job_template_nodes/item.yml')

    # Note: Duplicate payloads are actually accepted


class Awx_Schema_Workflow_Job_Template_Node_Always_Nodes(Awx_Schema):
    resource = resources.v1_workflow_job_template_node_always_nodes

    @property
    def get(self):
        return self.load_file('workflow_job_template_nodes/list.yml')

    @property
    def post(self):
        return self.load_file('workflow_job_template_nodes/item.yml')

    # Note: Duplicate payloads are actually accepted


#
# /workflow_jobs
#
class Awx_Schema_Workflow_Jobs(Awx_Schema):
    resource = resources.v1_workflow_jobs

    @property
    def get(self):
        return self.load_file('workflow_jobs/list.yml')


class Awx_Schema_Workflow_Job(Awx_Schema_Workflow_Jobs):
    resource = resources.v1_workflow_job

    @property
    def get(self):
        return self.load_file('workflow_jobs/item.yml')

# TODO: Add /workflow_jobs/\d+/workflow_nodes/
# (Currently get ISE when visiting this endpoint)


#
# /workflow_job_nodes
#
class Awx_Schema_Workflow_Job_Nodes(Awx_Schema):
    resource = resources.v1_workflow_job_nodes

    @property
    def get(self):
        return self.load_file('workflow_job_nodes/list.yml')


class Awx_Schema_Workflow_Job_Node(Awx_Schema_Workflow_Job_Nodes):
    resource = resources.v1_workflow_job_node

    @property
    def get(self):
        return self.load_file('workflow_job_nodes/item.yml')


class Awx_Schema_Workflow_Job_Node_Success_Nodes(Awx_Schema):
    resource = resources.v1_workflow_job_node_success_nodes

    @property
    def get(self):
        return self.load_file('workflow_job_nodes/list.yml')


class Awx_Schema_Workflow_Job_Node_Failure_Nodes(Awx_Schema):
    resource = resources.v1_workflow_job_node_failure_nodes

    @property
    def get(self):
        return self.load_file('workflow_job_nodes/list.yml')


class Awx_Schema_Workflow_Job_Node_Always_Nodes(Awx_Schema):
    resource = resources.v1_workflow_job_node_always_nodes

    @property
    def get(self):
        return self.load_file('workflow_job_nodes/list.yml')


#
# /inventory_sources
#
class Awx_Schema_Inventory_Sources(Awx_Schema):
    resource = resources.v1_inventory_sources

    @property
    def get(self):
        return self.load_file('inventory_sources/list.yml')

    @property
    def post(self):
        return self.load_file('inventory_sources/item.yml')

    @property
    def duplicate(self):
        return self.load_file('inventory_sources/duplicate.yml')

    @property
    def patch(self):
        return self.post

    @property
    def put(self):
        return self.post


class Awx_Schema_Inventory_Source(Awx_Schema_Inventory_Sources):
    resource = resources.v1_inventory_source

    @property
    def get(self):
        return self.load_file('inventory_sources/item.yml')


class Awx_Schema_Related_Inventory_Sources(Awx_Schema_Inventory_Sources):
    resource = resources.v1_related_inventory_sources


class Awx_Schema_Inventory_Sources_Related_Update(Awx_Schema):
    resource = resources.v1_inventory_sources_related_update

    @property
    def get(self):
        return self.load_file('inventory_sources/update.yml')

    @property
    def post(self):
        return self.load_file('inventory_sources/updated.yml')


class Awx_Schema_Inventory_Updates(Awx_Schema):
    resource = resources.v1_inventory_updates

    @property
    def get(self):
        return self.load_file('inventory_updates/list.yml')


class Awx_Schema_Inventory_Source_Updates(Awx_Schema):
    resource = resources.v1_inventory_source_updates

    @property
    def get(self):
        return self.load_file('inventory_updates/list.yml')


class Awx_Schema_Inventory_Sources_Related_Groups(Awx_Schema_Groups):
    resource = resources.v1_inventory_sources_related_groups


class Awx_Schema_Inventory_Update(Awx_Schema_Inventory_Updates):
    resource = resources.v1_inventory_update

    @property
    def get(self):
        return self.load_file('inventory_updates/item.yml')


class Awx_Schema_Inventory_Update_Cancel(Awx_Schema):
    resource = resources.v1_inventory_update_cancel

    @property
    def get(self):
        return self.load_file('inventory_updates/cancel.yml')

    @property
    def post(self):
        return self.load_file('empty.yml')


#
# /inventory_scripts
#
class Awx_Schema_Inventory_Scripts(Awx_Schema):
    resource = resources.v1_inventory_scripts

    @property
    def get(self):
        return self.load_file('inventory_scripts/list.yml')

    @property
    def post(self):
        return self.load_file('inventory_scripts/item.yml')

    @property
    def duplicate(self):
        return self.load_file('inventory_scripts/duplicate.yml')

    @property
    def patch(self):
        return self.post

    @property
    def put(self):
        return self.post


class Awx_Schema_Inventory_Script(Awx_Schema_Inventory_Scripts):
    resource = resources.v1_inventory_script

    @property
    def get(self):
        return self.load_file('inventory_scripts/item.yml')


#
# /teams
#
class Awx_Schema_Teams(Awx_Schema):
    resource = resources.v1_teams

    @property
    def get(self):
        return self.load_file('teams/list.yml')

    @property
    def post(self):
        return self.load_file('teams/item.yml')

    @property
    def duplicate(self):
        return self.load_file('teams/duplicate.yml')


class Awx_Schema_Team(Awx_Schema_Teams):
    resource = resources.v1_team

    @property
    def get(self):
        return self.load_file('teams/item.yml')

    @property
    def patch(self):
        return self.get

    @property
    def put(self):
        return self.get


class Awx_Schema_Team_Access_List(Awx_Schema):
    resource = resources.v1_team_access_list

    @property
    def get(self):
        return self.load_file('access_list/list.yml')


class Awx_Schema_Project_Teams(Awx_Schema_Teams):
    resource = resources.v1_project_teams


class Awx_Schema_Team_Permissions(Awx_Schema_User_Permissions):
    resource = resources.v1_team_permissions


class Awx_Schema_Team_Credentials(Awx_Schema_Credentials):
    resource = resources.v1_team_credentials


class Awx_Schema_Org_Teams(Awx_Schema_Teams):
    resource = resources.v1_org_teams


class Awx_Schema_User_Teams(Awx_Schema_Teams):
    resource = resources.v1_user_teams


#
# /config
#
class Awx_Schema_Config(Awx_Schema):
    resource = resources.v1_config

    @property
    def get(self):
        return self.load_file('config/list.yml')

    @property
    def post(self):
        return self.load_file('config/license.yml')

    @property
    def license_invalid(self):
        return self.load_file('errors/license_invalid.yml')


#
# /ping
#
class Awx_Schema_Ping(Awx_Schema):
    resource = resources.v1_ping

    @property
    def get(self):
        return self.load_file('ping.yml')

    @property
    def post(self):
        return self.method_not_allowed

    @property
    def put(self):
        return self.method_not_allowed

    @property
    def patch(self):
        return self.method_not_allowed


#
# /me
#
class Awx_Schema_Me(Awx_Schema):
    resource = resources.v1_me

    @property
    def put(self):
        return self.load_file('empty.yml')

    @property
    def patch(self):
        return self.load_file('empty.yml')

    @property
    def post(self):
        return self.load_file('empty.yml')

    @property
    def get(self):
        return self.load_file('me/list.yml')


#
# /authtoken
#
class Awx_Schema_Authtoken(Awx_Schema):
    resource = resources.v1_authtoken

    @property
    def get(self):
        return self.load_file('errors/405.yml')

    @property
    def put(self):
        return self.load_file('errors/405.yml')

    @property
    def patch(self):
        return self.load_file('errors/405.yml')

    @property
    def post(self):
        return self.load_file('authtoken.yml')


#
# /dashboard
#
class Awx_Schema_Dashboard(Awx_Schema):
    resource = resources.v1_dashboard

    @property
    def get(self):
        return self.load_file('dashboard.yml')


#
# /activity_stream
#
class Awx_Schema_Activity_Stream(Awx_Schema):
    resource = resources.v1_activity_stream

    @property
    def get(self):
        return self.load_file('activity_stream/list.yml')


class Awx_Schema_Activity(Awx_Schema_Activity_Stream):
    resource = resources.v1_activity

    @property
    def get(self):
        return self.load_file('activity_stream/item.yml')


class Awx_Schema_Object_Activity_Stream(Awx_Schema_Activity_Stream):
    resource = resources.v1_object_activity_stream


#
# /schedules
#
class Awx_Schema_Schedules(Awx_Schema):
    resource = resources.v1_schedules

    @property
    def get(self):
        return self.load_file('schedules/list.yml')

    @property
    def post(self):
        return self.load_file('schedules/item.yml')

    @property
    def patch(self):
        return self.post

    @property
    def put(self):
        return self.post

    @property
    def duplicate(self):
        return self.load_file('schedules/duplicate.yml')


class Awx_Schema_Schedule(Awx_Schema_Schedules):
    resource = resources.v1_schedule

    @property
    def get(self):
        return self.load_file('schedules/item.yml')


class Awx_Schema_Project_Schedules(Awx_Schema_Schedules):
    resource = resources.v1_project_schedules


class Awx_Schema_Project_Schedule(Awx_Schema_Schedule):
    resource = resources.v1_project_schedule


class Awx_Schema_Inventory_Source_Schedules(Awx_Schema_Schedules):
    resource = resources.v1_inventory_source_schedules


class Awx_Schema_Inventory_Source_Schedule(Awx_Schema_Schedule):
    resource = resources.v1_inventory_source_schedule


class Awx_Schema_Job_Template_Schedules(Awx_Schema_Schedules):
    resource = resources.v1_job_template_schedules


class Awx_Schema_Job_Template_Schedule(Awx_Schema_Schedule):
    resource = resources.v1_job_template_schedule


class Awx_Schema_Job_Template_Jobs(Awx_Schema_Jobs):
    resource = resources.v1_job_template_jobs


class Awx_Schema_System_Job_Template_Schedules(Awx_Schema_Schedules):
    resource = resources.v1_system_job_template_schedules


class Awx_Schema_System_Job_Template_Schedule(Awx_Schema_Schedule):
    resource = resources.v1_system_job_template_schedule


#
# /ad_hoc_commands
#
class Awx_Schema_Ad_Hoc_Commmands(Awx_Schema):
    resource = resources.v1_ad_hoc_commmands

    @property
    def get(self):
        return self.load_file('ad_hoc_commands/list.yml')

    @property
    def post(self):
        return self.load_file('ad_hoc_commands/item.yml')


class Awx_Schema_Ad_Hoc_Commmand(Awx_Schema_Ad_Hoc_Commmands):
    resource = resources.v1_ad_hoc_commmand

    @property
    def get(self):
        return self.load_file('ad_hoc_commands/item.yml')


class Awx_Schema_Ad_Hoc_Relaunch(Awx_Schema):
    resource = resources.v1_ad_hoc_relaunch

    @property
    def get(self):
        return self.load_file('jobs/relaunch.yml')

    @property
    def post(self):
        return self.load_file('ad_hoc_commands/item.yml')


class Awx_Schema_Ad_Hoc_Events(Awx_Schema):
    resource = resources.v1_ad_hoc_events

    @property
    def get(self):
        return self.load_file('ad_hoc_command_events/list.yml')


class Awx_Schema_Ad_Hoc_Event(Awx_Schema_Job_Events):
    resource = resources.v1_ad_hoc_event

    @property
    def get(self):
        return self.load_file('ad_hoc_command_events/item.yml')


class Awx_Schema_Ad_Hoc_Related_Cancel(Awx_Schema):
    resource = resources.v1_ad_hoc_related_cancel

    @property
    def get(self):
        return self.load_file('ad_hoc_commands/cancel.yml')

    @property
    def post(self):
        return self.load_file('empty.yml')


class Awx_Schema_Inventory_Related_Ad_Hoc_Commands(Awx_Schema_Ad_Hoc_Commmands):
    resource = resources.v1_inventory_related_ad_hoc_commands


class Awx_Schema_Group_Related_Ad_Hoc_Commands(Awx_Schema_Ad_Hoc_Commmands):
    resource = resources.v1_group_related_ad_hoc_commands


class Awx_Schema_Host_Related_Ad_Hoc_Commands(Awx_Schema_Ad_Hoc_Commmands):
    resource = resources.v1_host_related_ad_hoc_commands


#
# /notification_templates
#
class Awx_Schema_Notification_Templates(Awx_Schema):
    resource = resources.v1_notification_templates

    @property
    def get(self):
        return self.load_file('notification_templates/list.yml')

    @property
    def post(self):
        return self.load_file('notification_templates/item.yml')

    @property
    def duplicate(self):
        return self.load_file('notification_templates/duplicate.yml')


class Awx_Schema_Notification_Template(Awx_Schema_Notification_Templates):
    resource = resources.v1_notification_template

    @property
    def get(self):
        return self.load_file('notification_templates/item.yml')

    @property
    def patch(self):
        return self.get

    @property
    def put(self):
        return self.get


class Awx_Schema_Related_Notification_Templates(Awx_Schema_Notification_Templates):
    resource = resources.v1_related_notification_templates


class Awx_Schema_Notification_Template_Test(Awx_Schema):
    resource = resources.v1_notification_template_test

    @property
    def post(self):
        return self.load_file('notification_templates/test.yml')


class Awx_Schema_Notification_Templates_Any(Awx_Schema):
    resource = resources.v1_notification_templates_any

    @property
    def get(self):
        return self.load_file('notification_templates/list.yml')

    @property
    def post(self):
        return self.load_file('notification_templates/notification_templates_any.yml')

    @property
    def duplicate(self):
        return self.load_file('notification_templates/duplicate.yml')


class Awx_Schema_Notification_Template_Any(Awx_Schema_Notification_Templates_Any):
    resource = resources.v1_notification_template_any

    @property
    def get(self):
        return self.load_file('notification_templates/item.yml')

    @property
    def patch(self):
        return self.get

    @property
    def put(self):
        return self.get


class Awx_Schema_Notification_Templates_Error(Awx_Schema):
    resource = resources.v1_notification_templates_error

    @property
    def get(self):
        return self.load_file('notification_templates/list.yml')

    @property
    def post(self):
        return self.load_file('notification_templates/notification_templates_error.yml')

    @property
    def duplicate(self):
        return self.load_file('notification_templates/duplicate.yml')


class Awx_Schema_Notification_Template_Error(Awx_Schema_Notification_Templates_Error):
    resource = resources.v1_notification_template_error

    @property
    def get(self):
        return self.load_file('notification_templates/item.yml')

    @property
    def patch(self):
        return self.get

    @property
    def put(self):
        return self.get


class Awx_Schema_Notification_Templates_Success(Awx_Schema):
    resource = resources.v1_notification_templates_success

    @property
    def get(self):
        return self.load_file('notification_templates/list.yml')

    @property
    def post(self):
        return self.load_file('notification_templates/notification_templates_success.yml')

    @property
    def duplicate(self):
        return self.load_file('notification_templates/duplicate.yml')


class Awx_Schema_Notification_Template_Success(Awx_Schema_Notification_Templates_Success):
    resource = resources.v1_notification_template_success

    @property
    def get(self):
        return self.load_file('notification_templates/item.yml')

    @property
    def patch(self):
        return self.get

    @property
    def put(self):
        return self.get


#
# /notifications
#
class Awx_Schema_Notifications(Awx_Schema):
    resource = resources.v1_notifications

    @property
    def get(self):
        return self.load_file('notifications/list.yml')


class Awx_Schema_Notification(Awx_Schema_Notifications):
    resource = resources.v1_notification

    @property
    def get(self):
        return self.load_file('notifications/item.yml')


class Awx_Schema_Notification_Template_Notifications(Awx_Schema_Notifications):
    resource = resources.v1_notification_template_notifications


class Awx_Schema_Job_Notifications(Awx_Schema_Notifications):
    resource = resources.v1_job_notifications


class Awx_Schema_System_Job_Notifications(Awx_Schema_Notifications):
    resource = resources.v1_system_job_notifications


#
# /labels
#
class Awx_Schema_Labels(Awx_Schema):
    resource = resources.v1_labels

    @property
    def get(self):
        return self.load_file('labels/list.yml')

    @property
    def post(self):
        return self.load_file('labels/item.yml')

    @property
    def duplicate(self):
        return self.load_file('labels/duplicate.yml')


class Awx_Schema_Label(Awx_Schema_Labels):
    resource = resources.v1_label

    @property
    def get(self):
        return self.load_file('labels/item.yml')

    @property
    def patch(self):
        return self.get

    @property
    def put(self):
        return self.get


class Awx_Schema_Job_Template_Labels(Awx_Schema_Labels):
    resource = resources.v1_job_template_labels


class Awx_Schema_Job_Labels(Awx_Schema_Labels):
    resource = resources.v1_job_labels


#
# /roles
#
class Awx_Schema_Roles(Awx_Schema):
    resource = resources.v1_roles

    @property
    def get(self):
        return self.load_file('roles/list.yml')


class Awx_Schema_Role(Awx_Schema):
    resource = resources.v1_role

    @property
    def get(self):
        return self.load_file('roles/item.yml')


class Awx_Schema_Roles_Related_Teams(Awx_Schema_Teams):
    resource = resources.v1_roles_related_teams


class Awx_Schema_Related_Roles(Awx_Schema_Roles):
    resource = resources.v1_related_roles


class Awx_Schema_Related_Object_Roles(Awx_Schema):
    resource = resources.v1_related_object_roles

    @property
    def get(self):
        return self.load_file('roles/list.yml')
