from common.api.pages import Base, Base_List, Unified_Job_Template_Page, json_setter, json_getter
from common.exceptions import Method_Not_Allowed_Exception


class Job_Template_Callback_Page(Base):
    base_url = '/api/v1/job_templates/{id}/callback/'

    host_config_key = property(json_getter('host_config_key'), json_setter('host_config_key'))
    matching_hosts = property(json_getter('matching_hosts'), json_setter('matching_hosts'))


class Job_Template_Page(Unified_Job_Template_Page):
    base_url = '/api/v1/job_templates/{id}/'

    url = property(json_getter('url'), json_setter('url'))
    type = property(json_getter('type'), json_setter('type'))
    inventory = property(json_getter('inventory'), json_setter('inventory'))
    project = property(json_getter('project'), json_setter('project'))
    playbook = property(json_getter('playbook'), json_setter('playbook'))
    forks = property(json_getter('forks'), json_setter('forks'))
    credential = property(json_getter('credential'), json_setter('credential'))
    extra_vars = property(json_getter('extra_vars'), json_setter('extra_vars'))
    host_config_key = property(json_getter('host_config_key'), json_setter('host_config_key'))
    ask_credential_on_launch = property(json_getter('ask_credential_on_launch'), json_setter('ask_credential_on_launch'))
    ask_inventory_on_launch = property(json_getter('ask_inventory_on_launch'), json_setter('ask_inventory_on_launch'))
    ask_job_type_on_launch = property(json_getter('ask_job_type_on_launch'), json_setter('ask_job_type_on_launch'))
    ask_limit_on_launch = property(json_getter('ask_limit_on_launch'), json_setter('ask_limit_on_launch'))
    ask_tags_on_launch = property(json_getter('ask_tags_on_launch'), json_setter('ask_tags_on_launch'))
    ask_variables_on_launch = property(json_getter('ask_variables_on_launch'), json_setter('ask_variables_on_launch'))
    limit = property(json_getter('limit'), json_setter('limit'))
    job_tags = property(json_getter('job_tags'), json_setter('job_tags'))
    skip_tags = property(json_getter('skip_tags'), json_setter('skip_tags'))
    verbosity = property(json_getter('verbosity'), json_setter('verbosity'))
    job_type = property(json_getter('job_type'), json_setter('job_type'))
    summary_fields = property(json_getter('summary_fields'), json_setter('summary_fields'))

    def get_related(self, attr, **kwargs):
        assert attr in self.json['related'], \
            "No such related attribute '%s'" % attr

        if attr == 'start':
            cls = Base
        elif attr in ('credential', 'cloud_credential'):
            from credentials import Credential_Page
            cls = Credential_Page
        elif attr == 'schedules':
            from schedules import Schedules_Page
            cls = Schedules_Page
        elif attr == 'callback':
            cls = Job_Template_Callback_Page
        elif attr == 'launch':
            cls = Job_Template_Launch_Page
        elif attr == 'survey_spec':
            cls = Job_Template_Survey_Spec
        elif attr == 'jobs':
            from jobs import Jobs_Page
            cls = Jobs_Page
        elif attr == 'last_job':
            from jobs import Job_Page
            cls = Job_Page
        elif attr == 'inventory':
            from inventory import Inventory_Page
            cls = Inventory_Page
        elif attr == 'project':
            from projects import Project_Page
            cls = Project_Page
        elif attr == 'labels':
            from labels import Labels_Page
            cls = Labels_Page
        elif attr == 'notification_templates_any':
            from notification_templates import Notification_Templates_Page
            cls = Notification_Templates_Page
        elif attr == 'notification_templates_error':
            from notification_templates import Notification_Templates_Page
            cls = Notification_Templates_Page
        elif attr == 'notification_templates_success':
            from notification_templates import Notification_Templates_Page
            cls = Notification_Templates_Page
        elif attr == 'access_list':
            from access_list import Access_List_Page
            cls = Access_List_Page
        elif attr == 'object_roles':
            from roles import Roles_Page
            cls = Roles_Page
        elif attr in ['created_by', 'modified_by']:
            from users import User_Page
            cls = User_Page
        elif attr == 'activity_stream':
            from activity_stream import Activity_Stream_Page
            cls = Activity_Stream_Page
        else:
            raise NotImplementedError("No related class found for '%s'" % attr)

        return cls(self.testsetup, base_url=self.json['related'][attr]).get(**kwargs)

    def post_job(self, **kwargs):
        '''
        Create a job by issuing a POST to related->jobs
        '''
        if 'job_template' not in kwargs:
            kwargs['job_template'] = self.id
        return self.get_related('jobs').post(kwargs)

    def launch_job(self, **kwargs):
        '''
        Create a job, and start a job.  Note, the method used is no longer the
        preferred mechanism for launching jobs.  Instead, job_templates should
        be launched (refer to `launch`).
        '''
        # Create a job
        job_pg = self.post_job(**kwargs)

        # GET related->start
        start_pg = job_pg.get_related('start')
        assert start_pg.json['can_start'], \
            "The created job is not able to launch (can_start:%s)" % start_pg.json['can_start']

        # Launch job, passing kwargs (if provided)
        start_pg.post(**kwargs)

        return job_pg

    def launch(self, payload={}):
        '''
        Launch the job_template using related->launch endpoint.
        '''
        # get related->launch
        launch_pg = self.get_related('launch')

        # launch the job_template
        result = launch_pg.post(payload)

        # return job
        jobs_pg = self.get_related('jobs', id=result.json['job'])
        assert jobs_pg.count == 1, \
            "job_template launched (id:%s) but job not found in response at %s/jobs/" % \
            (result.json['job'], self.url)
        return jobs_pg.results[0]

    def _cleanup(self, delete_method):
        try:
            delete_method()
        except Method_Not_Allowed_Exception as e:
            if "there are jobs running" in e[1]['error']:
                jobs = self.get_related('jobs', status__in=','.join(['new', 'pending', 'waiting', 'running']))
                for job in jobs.results:
                    cancel = job.get_related('cancel')
                    if cancel.can_cancel:
                        cancel.post()
                for job in jobs.results:
                    job.wait_until_completed()
                delete_method()
            else:
                raise(e)


class Job_Templates_Page(Job_Template_Page, Base_List):
    base_url = '/api/v1/job_templates/'


class Job_Template_Launch_Page(Base):
    base_url = '/api/v1/job_templates/{id}/launch'

    can_start_without_user_input = property(json_getter('can_start_without_user_input'), json_setter('can_start_without_user_input'))
    ask_credential_on_launch = property(json_getter('ask_tags_on_launch'), json_setter('ask_tags_on_launch'))
    ask_inventory_on_launch = property(json_getter('ask_inventory_on_launch'), json_setter('ask_inventory_on_launch'))
    ask_job_type_on_launch = property(json_getter('ask_job_type_on_launch'), json_setter('ask_job_type_on_launch'))
    ask_limit_on_launch = property(json_getter('ask_limit_on_launch'), json_setter('ask_limit_on_launch'))
    ask_tags_on_launch = property(json_getter('ask_tags_on_launch'), json_setter('ask_tags_on_launch'))
    ask_variables_on_launch = property(json_getter('ask_variables_on_launch'), json_setter('ask_variables_on_launch'))
    passwords_needed_to_start = property(json_getter('passwords_needed_to_start'), json_setter('passwords_needed_to_start'))
    credential_needed_to_start = property(json_getter('credential_needed_to_start'), json_setter('credential_needed_to_start'))
    inventory_needed_to_start = property(json_getter('inventory_needed_to_start'), json_setter('inventory_needed_to_start'))
    variables_needed_to_start = property(json_getter('variables_needed_to_start'), json_setter('variables_needed_to_start'))
    survey_enabled = property(json_getter('survey_enabled'), json_setter('survey_enabled'))
    job_template_data = property(json_getter('job_template_data'), json_setter('job_template_data'))
    defaults = property(json_getter('defaults'), json_setter('defaults'))


class Job_Template_Survey_Spec(Base):
    base_url = '/api/v1/job_templates/{id}/survey_spec/'

    name = property(json_getter('name'), json_setter('name'))
    description = property(json_getter('description'), json_setter('description'))
    spec = property(json_getter('spec'), json_setter('spec'))
