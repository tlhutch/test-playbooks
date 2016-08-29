from qe.api.pages import UnifiedJobTemplate
from qe.api import resources
import base


class SystemJobTemplate(UnifiedJobTemplate):

    def launch(self, payload={}):
        '''
        Launch the system_job_template using related->launch endpoint.
        '''
        # get related->launch
        launch_pg = self.get_related('launch')

        # launch the job_template
        result = launch_pg.post(payload)

        # return job
        jobs_pg = self.get_related('jobs', id=result.json['system_job'])
        assert jobs_pg.count == 1, \
            "system_job_template launched (id:%s) but unable to find matching " \
            "job at %s/jobs/" % (result.json['job'], self.url)
        return jobs_pg.results[0]

base.register_page(resources.v1_system_job_template, SystemJobTemplate)


class SystemJobTemplates(SystemJobTemplate, base.BaseList):

    pass

base.register_page(resources.v1_system_job_templates, SystemJobTemplates)

# backwards compatibility
System_Job_Template_Page = SystemJobTemplate
System_Job_Templates_Page = SystemJobTemplates
