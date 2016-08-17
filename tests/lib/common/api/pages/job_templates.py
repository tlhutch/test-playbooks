from common.api.pages import Unified_Job_Template_Page
from common.api import resources
import base


class Job_Template_Page(Unified_Job_Template_Page):

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

base.register_page(resources.v1_job_template, Job_Template_Page)


class Job_Templates_Page(Job_Template_Page, base.Base_List):

    pass

base.register_page([resources.v1_job_templates,
                    resources.v1_related_job_templates], Job_Templates_Page)


class Job_Template_Callback_Page(base.Base):

    pass

base.register_page(resources.v1_job_template_callback, Job_Template_Callback_Page)


class Job_Template_Launch_Page(base.Base):

    pass

base.register_page(resources.v1_job_template_launch, Job_Template_Launch_Page)


class Job_Template_Survey_Spec(base.Base):

    pass

base.register_page(resources.v1_job_template_survey_spec, Job_Template_Survey_Spec)
