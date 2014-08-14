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

class Awx_Schema_User(Awx_Schema_Users):
    resource = '/api/v1/users/\d+/'

    @property
    def get(self):
        return self.load_file('users/item.yml')

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
    def put(self):
        return self.load_file('inventories/item.yml')

    @property
    def patch(self):
        return self.load_file('inventories/item.yml')

    @property
    def duplicate(self):
        return self.load_file('inventories/duplicate.yml')

class Awx_Schema_Inventories_N(Awx_Schema_Inventories):
    resource = '/api/v1/inventories/\d+/'

    @property
    def get(self):
        return self.load_file('inventories/item.yml')

class Awx_Schema_Variable_Data(Awx_Schema):
    resource = '/api/v1/.*\/variable_data/'

    @property
    def get(self):
        return self.load_file('dict.yml')
    def put(self):
        return self.get
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

class Awx_Schema_Group_Hosts(Awx_Schema_Hosts):
    resource = '/api/v1/groups/\d+/hosts/'

class Awx_Schema_Group_All_Hosts(Awx_Schema_Hosts):
    resource = '/api/v1/groups/\d+/all_hosts/'

class Awx_Schema_Inventory_Hosts(Awx_Schema_Hosts):
    resource = '/api/v1/inventories/\d+/hosts/'

class Awx_Schema_Inventory_Groups(Awx_Schema_Groups):
    resource = '/api/v1/inventories/\d+/groups/'

class Awx_Schema_Inventory_Root_Groups(Awx_Schema_Groups):
    resource = '/api/v1/inventories/\d+/root_groups/'

class Awx_Schema_Inventory_Script(Awx_Schema):
    resource = '/api/v1/inventories/\d+/script/'

    @property
    def get(self):
        return self.load_file('dict.yml')
    def put(self):
        return self.get
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

class Awx_Schema_Credential(Awx_Schema_Credentials):
    resource = '/api/v1/credentials/\d+/'

    @property
    def get(self):
        return self.load_file('credentials/item.yml')

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

class Awx_Schema_Project_Organizations(Awx_Schema_Organizations):
    resource = '/api/v1/projects/\d+/organizations/'

class Awx_Schema_Org_Projects(Awx_Schema_Projects):
    resource = '/api/v1/organizations/\d+/projects/'

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

class Awx_Schema_Job_Start(Awx_Schema):
    resource = '/api/v1/jobs/\d+/start/'

    @property
    def get(self):
        return self.load_file('jobs/start.yml')
    @property
    def post(self):
        return self.load_file('empty.yml')

class Awx_Schema_Job_Events(Awx_Schema):
    resource = '/api/v1/jobs/\d+/job_events/'

    @property
    def get(self):
        return self.load_file('job_events/list.yml')

class Awx_Schema_Job_Event(Awx_Schema_Job_Events):
    resource = '/api/v1/jobs/\d+/job_events/\d+/'

    @property
    def get(self):
        return self.load_file('job_events/item.yml')

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

class Awx_Schema_Inventory_Sources_N(Awx_Schema_Inventory_Sources):
    resource = '/api/v1/inventory_sources/\d+/'

    @property
    def get(self):
        return self.load_file('inventory_sources/item.yml')

class Awx_Schema_Inventory_Sources_Update(Awx_Schema):
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

class Awx_Schema_Inventory_Source_Update(Awx_Schema_Inventory_Source_Updates):
    resource = '/api/v1/inventory_updates/\d+/'

    @property
    def get(self):
        return self.load_file('inventory_updates/item.yml')

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

class Awx_Schema_Project_Teams(Awx_Schema_Teams):
    resource = '/api/v1/projects/\d+/teams/'

class Awx_Schema_Org_Teams(Awx_Schema_Teams):
    resource = '/api/v1/organizations/\d+/teams/'

class Awx_Schema_Team_Credentials(Awx_Schema_Credentials):
    resource = '/api/v1/teams/\d+/credentials/'

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
        return self.load_file('users/list.yml')

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

class Awx_Schema_Activity_Stream_N(Awx_Schema_Activity_Stream):
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
