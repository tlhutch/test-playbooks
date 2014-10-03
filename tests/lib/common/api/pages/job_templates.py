import base
from common.exceptions import *

class Job_Template_Callback_Page(base.Base):
    base_url = '/api/v1/job_templates/{id}/callback/'

    host_config_key = property(base.json_getter('host_config_key'), base.json_setter('host_config_key'))
    matching_hosts = property(base.json_getter('matching_hosts'), base.json_setter('matching_hosts'))

class Job_Template_Page(base.Base):
    base_url = '/api/v1/job_templates/{id}/'

    name = property(base.json_getter('name'), base.json_setter('name'))
    inventory = property(base.json_getter('inventory'), base.json_setter('inventory'))
    project = property(base.json_getter('project'), base.json_setter('project'))
    playbook = property(base.json_getter('playbook'), base.json_setter('playbook'))
    forks = property(base.json_getter('forks'), base.json_setter('forks'))
    credential = property(base.json_getter('credential'), base.json_setter('credential'))
    extra_vars = property(base.json_getter('extra_vars'), base.json_setter('extra_vars'))
    host_config_key = property(base.json_getter('host_config_key'), base.json_setter('host_config_key'))
    ask_variables_on_launch = property(base.json_getter('ask_variables_on_launch'), base.json_setter('ask_variables_on_launch'))

    def get_related(self, name, **kwargs):
        assert name in self.json['related']
        if name == 'start':
            related = base.Base(self.testsetup, base_url=self.json['related'][name])
        elif name == 'schedules':
            from schedules import Schedules_Page
            related = Schedules_Page(self.testsetup, base_url=self.json['related'][name])
        elif name == 'callback':
            related = Job_Template_Callback_Page(self.testsetup, base_url=self.json['related'][name])
        elif name == 'launch':
            related = Job_Template_Launch_Page(self.testsetup, base_url=self.json['related'][name])
        elif name == 'survey_spec':
            related = base.Base(self.testsetup, base_url=self.json['related'][name])
        elif name == 'jobs':
            from jobs import Jobs_Page
            related = Jobs_Page(self.testsetup, base_url=self.json['related'][name])
        else:
            raise NotImplementedError
        return related.get(**kwargs)

    def post_job(self, **kwargs):
        '''
        Create a job by issuing a POST to related->jobs
        '''
        if 'job_template' not in kwargs:
            kwargs['job_template'] = self.id
        return self.get_related('jobs').post(kwargs)

    def launch_job(self, **kwargs):
        '''
        Create and launch a job
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


class Job_Templates_Page(Job_Template_Page, base.Base_List):
    base_url = '/api/v1/job_templates/'


class Job_Template_Launch_Page(base.Base):
    base_url = '/api/v1/job_templates/\d+/launch'

    ask_variables_on_launch = property(base.json_getter('ask_variables_on_launch'), base.json_setter('ask_variables_on_launch'))
    passwords_needed_to_start = property(base.json_getter('passwords_needed_to_start'), base.json_setter('passwords_needed_to_start'))
    variables_needed_to_start = property(base.json_getter('variables_needed_to_start'), base.json_setter('variables_needed_to_start'))
    can_start_without_user_input = property(base.json_getter('can_start_without_user_input'), base.json_setter('can_start_without_user_input'))
