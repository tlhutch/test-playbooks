import json
import base


class Job_Template_Callback_Page(base.Base):
    base_url = '/api/v1/job_templates/{id}/callback/'

    host_config_key = property(base.json_getter('host_config_key'), base.json_setter('host_config_key'))
    matching_hosts = property(base.json_getter('matching_hosts'), base.json_setter('matching_hosts'))


class Job_Template_Base_Page(base.Base):

    def launch(self, **kwargs):
        '''
        Launch the job_template using related->launch endpoint
        '''
        # get related->launch
        launch_pg = self.get_related('launch')

        # assert can_start_without_user_input
        assert launch_pg.can_start_without_user_input, \
            "The specified job_template (id:%s) is not able to launch without user input.\n%s" % \
            (launch_pg.id, json.dumps(launch_pg.json, indent=2))

        # launch the job_template
        result = launch_pg.post(**kwargs)

        # return job
        jobs_pg = self.get_related('jobs', id=result.json['job'])
        assert jobs_pg.count == 1, \
            "job_template launched (id:%s) but job not found in response at %s/jobs/" % \
            (result.json['job'], self.url)
        return jobs_pg.results[0]


class Job_Template_Page(Job_Template_Base_Page):
    base_url = '/api/v1/job_templates/{id}/'

    url = property(base.json_getter('url'), base.json_setter('url'))
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
            related = Job_Template_Survey_Spec(self.testsetup, base_url=self.json['related'][name])
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


class Job_Templates_Page(Job_Template_Page, base.Base_List):
    base_url = '/api/v1/job_templates/'


class Job_Template_Launch_Page(base.Base):
    base_url = '/api/v1/job_templates/{id}/launch'

    can_start_without_user_input = property(base.json_getter('can_start_without_user_input'), base.json_setter('can_start_without_user_input'))
    ask_variables_on_launch = property(base.json_getter('ask_variables_on_launch'), base.json_setter('ask_variables_on_launch'))
    passwords_needed_to_start = property(base.json_getter('passwords_needed_to_start'), base.json_setter('passwords_needed_to_start'))
    variables_needed_to_start = property(base.json_getter('variables_needed_to_start'), base.json_setter('variables_needed_to_start'))


class Job_Template_Survey_Spec(base.Base):
    base_url = '/api/v1/job_templates/{id}/survey_spec/'

    name = property(base.json_getter('name'), base.json_setter('name'))
    description = property(base.json_getter('description'), base.json_setter('description'))
    spec = property(base.json_getter('spec'), base.json_setter('spec'))
