from qe.api.pages import UnifiedJobTemplate
from qe.api import resources
import base


class JobTemplate(UnifiedJobTemplate):

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

base.register_page(resources.v1_job_template, JobTemplate)


class JobTemplates(JobTemplate, base.BaseList):

    pass

base.register_page([resources.v1_job_templates,
                    resources.v1_related_job_templates], JobTemplates)


class JobTemplateCallback(base.Base):

    pass

base.register_page(resources.v1_job_template_callback, JobTemplateCallback)


class JobTemplateLaunch(base.Base):

    pass

base.register_page(resources.v1_job_template_launch, JobTemplateLaunch)


class JobTemplateSurveySpec(base.Base):

    pass

base.register_page(resources.v1_job_template_survey_spec, JobTemplateSurveySpec)

# backwards compatibility
Job_Template_Page = JobTemplate
Job_Templates_Page = JobTemplates
Job_Template_Callback_Page = JobTemplateCallback
Job_Template_Launch_Page = JobTemplateLaunch
Job_Template_Survey_Spec = JobTemplateSurveySpec
