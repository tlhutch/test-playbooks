import os
import glob
import logging
import common.yaml_file
from common.api.schema import Schema_Base


# FIXME - cache all schema files
schema_files = glob.glob(os.path.join(__path__[0], '*.yml'))


class Awx_Schema(Schema_Base):
    version = 'v1'
    resource = '/api/'

    def load_file(self, filename):
        try:
            return common.yaml_file.load_file(os.path.join(__path__[0], filename))
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
    def method_not_allowed(self):
        return self.load_file('errors/405.yml')

    @property
    def license_exceeded(self):
        return self.load_file('errors/license_exceeded.yml')


class Awx_Schema_v1(Awx_Schema):
    resource = '/api/v1/'

    @property
    def get(self):
        return self.load_file('api_v1.yml')


class Awx_Schema_Settings(Awx_Schema):
    resource = '/api/v1/settings/'

    @property
    def get(self):
        return self.load_file('settings/list.yml')

    @property
    def post(self):
        return self.load_file('settings/item.yml')


class Awx_Schema_Organizations(Awx_Schema):
    resource = '/api/v1/organizations/'

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
    resource = '/api/v1/organizations/\d+/'

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
    resource = '/api/v1/organizations/\d+/access_list/'

    @property
    def get(self):
        return self.load_file('access_list/list.yml')


class Awx_Schema_Users(Awx_Schema):
    resource = '/api/v1/users/'

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
    resource = '/api/v1/\w+/\d+/users/'


class Awx_Schema_User(Awx_Schema_Users):
    resource = '/api/v1/users/\d+/'

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
    resource = '/api/v1/users/\d+/access_list/'

    @property
    def get(self):
        return self.load_file('access_list/list.yml')


class Awx_Schema_Team_Users(Awx_Schema_Users):
    resource = '/api/v1/teams/\d+/users/'


class Awx_Schema_Org_Users(Awx_Schema_Users):
    resource = '/api/v1/organizations/\d+/users/'


class Awx_Schema_Org_Admins(Awx_Schema_Users):
    resource = '/api/v1/organizations/\d+/admins/'


class Awx_Schema_Inventories(Awx_Schema):
    resource = '/api/v1/inventories/'

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
    resource = '/api/v1/inventories/\d+/'

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
    resource = '/api/v1/organizations/\d+/inventories/'


class Awx_Schema_Inventory_Access_List(Awx_Schema):
    resource = '/api/v1/inventories/\d+/access_list/'

    @property
    def get(self):
        return self.load_file('access_list/list.yml')


class Awx_Schema_Inventory_Tree(Awx_Schema):
    resource = '/api/v1/inventories/\d+/tree/'

    @property
    def get(self):
        return self.load_file('tree.yml')


class Awx_Schema_Related_Inventory(Awx_Schema_Inventories):
    resource = '/api/v1/\w+/\d+/inventories/'


class Awx_Schema_Variable_Data(Awx_Schema):
    resource = '/api/v1/.*\/variable_data/'

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
    resource = '/api/v1/groups/'

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
    resource = '/api/v1/groups/\d+/'

    @property
    def get(self):
        return self.load_file('groups/item.yml')

    @property
    def put(self):
        return self.put

    @property
    def patch(self):
        return self.get


class Awx_Schema_Group_Access_List(Awx_Schema):
    resource = '/api/v1/groups/\d+/access_list/'

    @property
    def get(self):
        return self.load_file('access_list/list.yml')


class Awx_Schema_Host_Groups(Awx_Schema_Groups):
    resource = '/api/v1/hosts/\d+/groups/'


class Awx_Schema_Group_Children(Awx_Schema_Groups):
    resource = '/api/v1/groups/\d+/children/'


class Awx_Schema_Hosts(Awx_Schema):
    resource = '/api/v1/hosts/'

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
    resource = '/api/v1/hosts/\d+/'

    @property
    def get(self):
        return self.load_file('hosts/item.yml')

    @property
    def put(self):
        return self.put

    @property
    def patch(self):
        return self.get


class Awx_Schema_Host_Related_Fact_Versions(Awx_Schema):
    resource = '/api/v1/hosts/\d+/fact_versions/'

    @property
    def get(self):
        return self.load_file('fact_versions/list.yml')


class Awx_Schema_Fact_View(Awx_Schema):
    resource = '/api/v1/hosts/\d+/fact_view/'

    @property
    def get(self):
        return self.load_file('fact_view/item.yml')


class Awx_Schema_Group_Related_Hosts(Awx_Schema_Hosts):
    resource = '/api/v1/groups/\d+/hosts/'


class Awx_Schema_Group_Related_All_Hosts(Awx_Schema_Hosts):
    resource = '/api/v1/groups/\d+/all_hosts/'


class Awx_Schema_Inventory_Related_Hosts(Awx_Schema_Hosts):
    resource = '/api/v1/inventories/\d+/hosts/'


class Awx_Schema_Inventory_Related_Groups(Awx_Schema_Groups):
    resource = '/api/v1/inventories/\d+/groups/'


class Awx_Schema_Inventory_Related_Root_Groups(Awx_Schema_Groups):
    resource = '/api/v1/inventories/\d+/root_groups/'


class Awx_Schema_Inventory_Related_Script(Awx_Schema):
    resource = '/api/v1/inventories/\d+/script/'

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
    resource = '/api/v1/credentials/'

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
    resource = '/api/v1/\w+/\d+/credentials/'


class Awx_Schema_Credential(Awx_Schema_Credentials):
    resource = '/api/v1/credentials/\d+/'

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
    resource = '/api/v1/credentials/\d+/access_list/'

    @property
    def get(self):
        return self.load_file('access_list/list.yml')


class Awx_Schema_User_Credentials(Awx_Schema_Credentials):
    resource = '/api/v1/users/\d+/credentials/'


class Awx_Schema_User_Permissions(Awx_Schema):
    resource = '/api/v1/users/\d+/permissions/'

    @property
    def get(self):
        return self.load_file('permissions/list.yml')

    @property
    def post(self):
        return self.load_file('permissions/item.yml')


class Awx_Schema_Projects(Awx_Schema):
    resource = '/api/v1/projects/'

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
    resource = '/api/v1/projects/\d+/'

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
    resource = '/api/v1/\w+/\d+/projects/'


class Awx_Schema_Project_Access_List(Awx_Schema):
    resource = '/api/v1/projects/\d+/access_list/'

    @property
    def get(self):
        return self.load_file('access_list/list.yml')


class Awx_Schema_Org_Projects(Awx_Schema_Projects):
    resource = '/api/v1/organizations/\d+/projects/'


class Awx_Schema_User_Organizations(Awx_Schema_Organizations):
    resource = '/api/v1/users/\d+/organizations/'


class Awx_Schema_User_Admin_Organizations(Awx_Schema_Organizations):
    resource = '/api/v1/users/\d+/admin_of_organizations/'


class Awx_Schema_Project_Organizations(Awx_Schema_Organizations):
    resource = '/api/v1/projects/\d+/organizations/'


class Awx_Schema_Projects_Project_Updates(Awx_Schema):
    resource = '/api/v1/projects/\d+/project_updates/'

    @property
    def get(self):
        return self.load_file('project_updates/list.yml')


class Awx_Schema_Project_Playbooks(Awx_Schema):
    resource = '/api/v1/projects/\d+/playbooks/'

    @property
    def get(self):
        return self.load_file('list.yml')


class Awx_Schema_Project_Update(Awx_Schema):
    resource = '/api/v1/projects/\d+/update/'

    @property
    def get(self):
        return self.load_file('projects/update.yml')

    @property
    def post(self):
        return self.load_file('projects/updated.yml')


class Awx_Schema_Project_Updates(Awx_Schema_Projects_Project_Updates):
    resource = '/api/v1/project_updates/\d+/'

    @property
    def get(self):
        return self.load_file('project_updates/item.yml')


class Awx_Schema_Project_Update_Cancel(Awx_Schema):
    resource = '/api/v1/project_updates/\d+/cancel/'

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
    resource = '/api/v1/unified_job_templates/'

    @property
    def get(self):
        return self.load_file('unified_job_templates/list.yml')


class Awx_Schema_Unified_Job_Template(Awx_Schema_Unified_Job_Templates):
    resource = '/api/v1/unified_job_templates/\d+/'

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
    resource = '/api/v1/unified_jobs/'

    @property
    def get(self):
        return self.load_file('unified_jobs/list.yml')


class Awx_Schema_Schedules_Jobs(Awx_Schema_Unified_Jobs):
    resource = '/api/v1/schedules/\d+/jobs/'


#
# /system_job_templates
#
class Awx_Schema_System_Job_Templates(Awx_Schema):
    resource = '/api/v1/system_job_templates/'

    @property
    def get(self):
        return self.load_file('system_job_templates/list.yml')


class Awx_Schema_System_Job_Template(Awx_Schema_System_Job_Templates):
    resource = '/api/v1/system_job_templates/\d+/'

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
    resource = '/api/v1/system_job_templates/\d+/launch/'

    @property
    def get(self):
        return self.load_file('system_job_templates/launch.yml')

    @property
    def post(self):
        return self.load_file('system_job_templates/launched.yml')


class Awx_Schema_System_Job_Template_Jobs(Awx_Schema_Unified_Jobs):
    resource = '/api/v1/system_job_templates/\d+/jobs/'


#
# /system_jobs
#
class Awx_Schema_System_Jobs(Awx_Schema):
    resource = '/api/v1/system_jobs/'

    @property
    def get(self):
        return self.load_file('system_jobs/list.yml')


class Awx_Schema_System_Job(Awx_Schema_System_Jobs):
    resource = '/api/v1/system_jobs/\d+/'

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
    resource = '/api/v1/system_jobs/\d+/cancel/'

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
    resource = '/api/v1/job_templates/'

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
    resource = '/api/v1/job_templates/\d+/'

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
    resource = '/api/v1/job_templates/\d+/access_list/'

    @property
    def get(self):
        return self.load_file('access_list/list.yml')


class Awx_Schema_Job_Template_Launch(Awx_Schema):
    resource = '/api/v1/job_templates/\d+/launch/'

    @property
    def get(self):
        return self.load_file('job_templates/launch.yml')

    @property
    def post(self):
        return self.load_file('job_templates/launched.yml')


class Awx_Schema_Job_Template_Survey_Spec(Awx_Schema):
    resource = '/api/v1/job_templates/\d+/survey_spec/'

    @property
    def get(self):
        return self.load_file('job_templates/survey_spec.yml')

    @property
    def post(self):
        return self.load_file('empty.yml')


class Awx_Schema_Related_Job_Templates(Awx_Schema_Job_Templates):
    resource = '/api/v1/\w+/\d+/job_templates/'


class Awx_Schema_Inventory_Scan_Job_Templates(Awx_Schema_Job_Templates):
    resource = '/api/v1/inventories/\d+/scan_job_templates/'


#
# /job_template/N/callback/
#
class Awx_Schema_Job_Template_Callback(Awx_Schema):
    resource = '/api/v1/job_templates/\d+/callback/'

    @property
    def get(self):
        return self.load_file('job_templates/callback.yml')


#
# /jobs
#
class Awx_Schema_Jobs(Awx_Schema):
    resource = '/api/v1/jobs/'

    @property
    def get(self):
        return self.load_file('jobs/list.yml')

    @property
    def post(self):
        return self.load_file('jobs/item.yml')


class Awx_Schema_Job(Awx_Schema_Jobs):
    resource = '/api/v1/jobs/\d+/'

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
    resource = '/api/v1/jobs/\d+/cancel/'

    @property
    def get(self):
        return self.load_file('jobs/cancel.yml')

    @property
    def post(self):
        return self.load_file('empty.yml')


class Awx_Schema_Job_Start(Awx_Schema):
    resource = '/api/v1/jobs/\d+/start/'

    @property
    def get(self):
        return self.load_file('jobs/start.yml')

    @property
    def post(self):
        return self.load_file('empty.yml')


class Awx_Schema_Job_Relaunch(Awx_Schema):
    resource = '/api/v1/jobs/\d+/relaunch/'

    @property
    def get(self):
        return self.load_file('jobs/relaunch.yml')

    @property
    def post(self):
        return self.load_file('jobs/relaunched.yml')


class Awx_Schema_Job_Host_Summaries(Awx_Schema):
    resource = '/api/v1/jobs/\d+/job_host_summaries/'

    @property
    def get(self):
        return self.load_file('job_host_summaries/list.yml')


class Awx_Schema_Job_Host_Summary(Awx_Schema_Job_Host_Summaries):
    resource = '/api/v1/jobs/\d+/job_host_summaries/\d+/'

    @property
    def get(self):
        return self.load_file('job_host_summaries/item.yml')


class Awx_Schema_Job_Plays(Awx_Schema):
    resource = '/api/v1/jobs/\d+/job_plays/'

    @property
    def get(self):
        return self.load_file('job_plays/list.yml')


class Awx_Schema_Job_Play(Awx_Schema_Job_Plays):
    resource = '/api/v1/jobs/\d+/job_plays/\d+/'

    @property
    def get(self):
        return self.load_file('job_plays/item.yml')


class Awx_Schema_Job_Tasks(Awx_Schema):
    resource = '/api/v1/jobs/\d+/job_tasks/'

    @property
    def get(self):
        return self.load_file('job_tasks/list.yml')


class Awx_Schema_Job_Task(Awx_Schema_Job_Tasks):
    resource = '/api/v1/jobs/\d+/job_tasks/\d+/'

    @property
    def get(self):
        return self.load_file('job_tasks/item.yml')


class Awx_Schema_Job_Events(Awx_Schema):
    resource = '/api/v1/job_events/'

    @property
    def get(self):
        return self.load_file('job_events/list.yml')


class Awx_Schema_Job_Job_Events(Awx_Schema_Job_Events):
    resource = '/api/v1/jobs/\d+/job_events/'


class Awx_Schema_Job_Event(Awx_Schema_Job_Events):
    resource = '/api/v1/job_events/\d+/'

    @property
    def get(self):
        return self.load_file('job_events/item.yml')


class Awx_Schema_Job_Event_Children(Awx_Schema_Job_Events):
    resource = '/api/v1/job_events/\d+/children/'


class Awx_Schema_Job_Stdout(Awx_Schema):
    resource = '/api/v1/jobs/\d+/stdout/'

    @property
    def get(self):
        return self.load_file('job_stdout/item.yml')


#
# /inventory_sources
#
class Awx_Schema_Inventory_Sources(Awx_Schema):
    resource = '/api/v1/inventory_sources/'

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
    resource = '/api/v1/inventory_sources/\d+/'

    @property
    def get(self):
        return self.load_file('inventory_sources/item.yml')


class Awx_Schema_Related_Inventory_Sources(Awx_Schema_Inventory_Sources):
    resource = '/api/v1/\w+/\d+/inventory_sources/'


class Awx_Schema_Inventory_Sources_Related_Update(Awx_Schema):
    resource = '/api/v1/inventory_sources/\d+/update/'

    @property
    def get(self):
        return self.load_file('inventory_sources/update.yml')

    @property
    def post(self):
        return self.load_file('inventory_sources/updated.yml')


class Awx_Schema_Inventory_Source_Updates(Awx_Schema):
    resource = '/api/v1/inventory_sources/\d+/inventory_updates/'

    @property
    def get(self):
        return self.load_file('inventory_updates/list.yml')


class Awx_Schema_Inventory_Sources_Related_Groups(Awx_Schema_Groups):
    resource = '/api/v1/inventory_sources/\d+/groups/'


class Awx_Schema_Inventory_Source_Update(Awx_Schema_Inventory_Source_Updates):
    resource = '/api/v1/inventory_updates/\d+/'

    @property
    def get(self):
        return self.load_file('inventory_updates/item.yml')


class Awx_Schema_Inventory_Source_Update_Cancel(Awx_Schema):
    resource = '/api/v1/inventory_updates/\d+/cancel/'

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
    resource = '/api/v1/inventory_scripts/'

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
    resource = '/api/v1/inventory_scripts/\d+/'

    @property
    def get(self):
        return self.load_file('inventory_scripts/item.yml')


#
# /teams
#
class Awx_Schema_Teams(Awx_Schema):
    resource = '/api/v1/teams/'

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
    resource = '/api/v1/teams/\d+/'

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
    resource = '/api/v1/teams/\d+/access_list/'

    @property
    def get(self):
        return self.load_file('access_list/list.yml')


class Awx_Schema_Project_Teams(Awx_Schema_Teams):
    resource = '/api/v1/projects/\d+/teams/'


class Awx_Schema_Team_Permissions(Awx_Schema_User_Permissions):
    resource = '/api/v1/teams/\d+/permissions/'


class Awx_Schema_Team_Credentials(Awx_Schema_Credentials):
    resource = '/api/v1/teams/\d+/credentials/'


class Awx_Schema_Org_Teams(Awx_Schema_Teams):
    resource = '/api/v1/organizations/\d+/teams/'


class Awx_Schema_User_Teams(Awx_Schema_Teams):
    resource = '/api/v1/users/\d+/teams/'


#
# /config
#
class Awx_Schema_Config(Awx_Schema):
    resource = '/api/v1/config/'

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
    resource = '/api/v1/ping/'

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
    resource = '/api/v1/me/'

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
    resource = '/api/v1/authtoken/'

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
    resource = '/api/v1/dashboard/'

    @property
    def get(self):
        return self.load_file('dashboard.yml')


#
# /activity_stream
#
class Awx_Schema_Activity_Stream(Awx_Schema):
    resource = '/api/v1/activity_stream/'

    @property
    def get(self):
        return self.load_file('activity_stream/list.yml')


class Awx_Schema_Activity(Awx_Schema_Activity_Stream):
    resource = '/api/v1/activity_stream/\d+/'

    @property
    def get(self):
        return self.load_file('activity_stream/item.yml')


class Awx_Schema_Object_Activity_Stream(Awx_Schema_Activity_Stream):
    resource = '/api/v1/[^/]+/\d+/activity_stream/'


#
# /schedules
#
class Awx_Schema_Schedules(Awx_Schema):
    resource = '/api/v1/schedules/'

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
    resource = '/api/v1/schedules/\d+/'

    @property
    def get(self):
        return self.load_file('schedules/item.yml')


class Awx_Schema_Project_Schedules(Awx_Schema_Schedules):
    resource = '/api/v1/projects/\d+/schedules/'


class Awx_Schema_Project_Schedule(Awx_Schema_Schedule):
    resource = '/api/v1/projects/\d+/schedules/\d+/'


class Awx_Schema_Inventory_Source_Schedules(Awx_Schema_Schedules):
    resource = '/api/v1/inventory_sources/\d+/schedules/'


class Awx_Schema_Inventory_Source_Schedule(Awx_Schema_Schedule):
    resource = '/api/v1/inventory_sources/\d+/schedules/\d+/'


class Awx_Schema_Job_Template_Schedules(Awx_Schema_Schedules):
    resource = '/api/v1/job_templates/\d+/schedules/'


class Awx_Schema_Job_Template_Schedule(Awx_Schema_Schedule):
    resource = '/api/v1/job_templates/\d+/schedules/\d+/'


class Awx_Schema_Job_Template_Jobs(Awx_Schema_Jobs):
    resource = '/api/v1/job_templates/\d+/jobs/'


class Awx_Schema_System_Job_Template_Schedules(Awx_Schema_Schedules):
    resource = '/api/v1/system_job_templates/\d+/schedules/'


class Awx_Schema_System_Job_Template_Schedule(Awx_Schema_Schedule):
    resource = '/api/v1/system_job_templates/\d+/schedules/\d+/'


#
# /ad_hoc_commands
#
class Awx_Schema_Ad_Hoc_Commmands(Awx_Schema):
    resource = '/api/v1/ad_hoc_commands/'

    @property
    def get(self):
        return self.load_file('ad_hoc_commands/list.yml')

    @property
    def post(self):
        return self.load_file('ad_hoc_commands/item.yml')


class Awx_Schema_Ad_Hoc_Commmand(Awx_Schema_Ad_Hoc_Commmands):
    resource = '/api/v1/ad_hoc_commands/\d+/'

    @property
    def get(self):
        return self.load_file('ad_hoc_commands/item.yml')


class Awx_Schema_Ad_Hoc_Relaunch(Awx_Schema):
    resource = '/api/v1/ad_hoc_commands/\d+/relaunch/'

    @property
    def get(self):
        return self.load_file('jobs/relaunch.yml')

    @property
    def post(self):
        return self.load_file('ad_hoc_commands/item.yml')


class Awx_Schema_Ad_Hoc_Events(Awx_Schema):
    resource = '/api/v1/ad_hoc_commands/\d+/events/'

    @property
    def get(self):
        return self.load_file('ad_hoc_command_events/list.yml')


class Awx_Schema_Ad_Hoc_Event(Awx_Schema_Job_Events):
    resource = '/api/v1/ad_hoc_command_events/\d+/'

    @property
    def get(self):
        return self.load_file('ad_hoc_command_events/item.yml')


class Awx_Schema_Ad_Hoc_Related_Cancel(Awx_Schema):
    resource = '/api/v1/ad_hoc_commands/\d+/cancel/'

    @property
    def get(self):
        return self.load_file('ad_hoc_commands/cancel.yml')

    @property
    def post(self):
        return self.load_file('empty.yml')


class Awx_Schema_Inventory_Related_Ad_Hoc_Commands(Awx_Schema_Ad_Hoc_Commmands):
    resource = '/api/v1/inventories/\d+/ad_hoc_commands/'


class Awx_Schema_Group_Related_Ad_Hoc_Commands(Awx_Schema_Ad_Hoc_Commmands):
    resource = '/api/v1/groups/\d+/ad_hoc_commands/'


class Awx_Schema_Host_Related_Ad_Hoc_Commands(Awx_Schema_Ad_Hoc_Commmands):
    resource = '/api/v1/hosts/\d+/ad_hoc_commands/'


#
# /notification_templates
#
class Awx_Schema_Notification_Templates(Awx_Schema):
    resource = '/api/v1/notification_templates/'

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
    resource = '/api/v1/notification_templates/\d+/'

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
    resource = '/api/v1/\w+/\d+/notification_templates/'


class Awx_Schema_Notification_Template_Test(Awx_Schema):
    resource = '/api/v1/notification_templates/\d+/test/'

    @property
    def post(self):
        return self.load_file('notification_templates/test.yml')


class Awx_Schema_Notification_Templates_Any(Awx_Schema):
    resource = '/api/v1/\w+/\d+/notification_templates_any/'

    @property
    def get(self):
        return self.load_file('notification_templates/list.yml')

    @property
    def post(self):
        return self.load_file('empty.yml')

    @property
    def duplicate(self):
        return self.load_file('notification_templates/duplicate.yml')


class Awx_Schema_Notification_Template_Any(Awx_Schema_Notification_Templates_Any):
    resource = '/api/v1/\w+/\d+/notification_templates_any/\d+/'

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
    resource = '/api/v1/\w+/\d+/notification_templates_error/'

    @property
    def get(self):
        return self.load_file('notification_templates/list.yml')

    @property
    def post(self):
        return self.load_file('empty.yml')

    @property
    def duplicate(self):
        return self.load_file('notification_templates/duplicate.yml')


class Awx_Schema_Notification_Template_Error(Awx_Schema_Notification_Templates_Error):
    resource = '/api/v1/\w+/\d+/notification_templates_error/\d+/'

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
    resource = '/api/v1/\w+/\d+/notification_templates_success/'

    @property
    def get(self):
        return self.load_file('notification_templates/list.yml')

    @property
    def post(self):
        return self.load_file('empty.yml')

    @property
    def duplicate(self):
        return self.load_file('notification_templates/duplicate.yml')


class Awx_Schema_Notification_Template_Success(Awx_Schema_Notification_Templates_Success):
    resource = '/api/v1/\w+/\d+/notification_templates_success/\d+/'

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
    resource = '/api/v1/notifications/'

    @property
    def get(self):
        return self.load_file('notifications/list.yml')


class Awx_Schema_Notification(Awx_Schema_Notifications):
    resource = '/api/v1/notifications/\d+/'

    @property
    def get(self):
        return self.load_file('notifications/item.yml')


class Awx_Schema_Job_Notifications(Awx_Schema_Notifications):
    resource = '/api/v1/jobs/\d+/notifications/'


#
# /labels
#
class Awx_Schema_Labels(Awx_Schema):
    resource = '/api/v1/labels/'

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
    resource = '/api/v1/labels/\d+/'

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
    resource = '/api/v1/job_templates/\d+/labels/'


class Awx_Schema_Job_Labels(Awx_Schema_Labels):
    resource = '/api/v1/jobs/\d+/labels/'


#
# /roles
#
class Awx_Schema_Roles(Awx_Schema):
    resource = '/api/v1/roles/'

    @property
    def get(self):
        return self.load_file('roles/list.yml')


class Awx_Schema_Role(Awx_Schema):
    resource = '/api/v1/roles/\d+/'

    @property
    def get(self):
        return self.load_file('roles/item.yml')


class Awx_Schema_Related_Roles(Awx_Schema_Roles):
    resource = '/api/v1/\w+/\d+/roles/'


class Awx_Schema_Related_Object_Roles(Awx_Schema):
    resource = '/api/v1/\w+/\d+/object_roles/'

    @property
    def get(self):
        return self.load_file('roles/list.yml')
