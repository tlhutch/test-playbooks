from common.api.pages import Base, Base_List, Unified_Job_Template_Page, json_setter, json_getter


class Job_Template_Callback_Page(Base):
    base_url = '/api/v1/job_templates/{id}/callback/'

    host_config_key = property(json_getter('host_config_key'), json_setter('host_config_key'))
    matching_hosts = property(json_getter('matching_hosts'), json_setter('matching_hosts'))


class Job_Template_Page(Unified_Job_Template_Page):
    base_url = '/api/v1/job_templates/{id}/'

    url = property(json_getter('url'), json_setter('url'))
    inventory = property(json_getter('inventory'), json_setter('inventory'))
    project = property(json_getter('project'), json_setter('project'))
    playbook = property(json_getter('playbook'), json_setter('playbook'))
    forks = property(json_getter('forks'), json_setter('forks'))
    credential = property(json_getter('credential'), json_setter('credential'))
    extra_vars = property(json_getter('extra_vars'), json_setter('extra_vars'))
    host_config_key = property(json_getter('host_config_key'), json_setter('host_config_key'))
    ask_variables_on_launch = property(json_getter('ask_variables_on_launch'), json_setter('ask_variables_on_launch'))

    def get_related(self, name, **kwargs):
        assert name in self.json['related']
        if name == 'start':
            related = Base(self.testsetup, base_url=self.json['related'][name])
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
        elif name == 'inventory':
            from inventory import Inventory_Page
            related = Inventory_Page(self.testsetup, base_url=self.json['related'][name])
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


class Job_Templates_Page(Job_Template_Page, Base_List):
    base_url = '/api/v1/job_templates/'


class Job_Template_Launch_Page(Base):
    base_url = '/api/v1/job_templates/{id}/launch'

    can_start_without_user_input = property(json_getter('can_start_without_user_input'), json_setter('can_start_without_user_input'))
    ask_variables_on_launch = property(json_getter('ask_variables_on_launch'), json_setter('ask_variables_on_launch'))
    passwords_needed_to_start = property(json_getter('passwords_needed_to_start'), json_setter('passwords_needed_to_start'))
    credential_needed_to_start = property(json_getter('credential_needed_to_start'), json_setter('credential_needed_to_start'))
    variables_needed_to_start = property(json_getter('variables_needed_to_start'), json_setter('variables_needed_to_start'))


class Job_Template_Survey_Spec(Base):
    base_url = '/api/v1/job_templates/{id}/survey_spec/'

    name = property(json_getter('name'), json_setter('name'))
    description = property(json_getter('description'), json_setter('description'))
    spec = property(json_getter('spec'), json_setter('spec'))
