import fauxfactory

from qe.api.pages import UnifiedJobTemplate
from qe.api import resources
from qe.exceptions import UnexpectedTowerState_Exception
import base


class WorkflowJobTemplate(UnifiedJobTemplate):

    dependencies = []

    def launch(self, payload={}):
        '''
        Launch the workflow_job_template using related->launch endpoint.
        '''
        # get related->launch
        launch_pg = self.get_related('launch')

        # launch the workflow_job_template
        result = launch_pg.post(payload)

        # return job
        jobs_pg = self.related.jobs.get(id=result.workflow_job)
        if jobs_pg.count != 1:
            msg = "workflow_job_template launched (id:{}) but job not found in response at {}/jobs/" % \
                  (result.json['workflow_job'], self.url)
            raise UnexpectedTowerState_Exception(msg)
        return jobs_pg.results[0]

    def create(self, name='', description='', **kw):
        payload = dict(name=name or 'WorkflowJobTemplate - {}'.format(fauxfactory.gen_alphanumeric()),
                       description=description or fauxfactory.gen_alphanumeric())

        return self.update_identity(WorkflowJobTemplates(self.testsetup).post(payload))

base.register_page(resources.v1_workflow_job_template, WorkflowJobTemplate)


class WorkflowJobTemplates(base.BaseList, WorkflowJobTemplate):

    pass

base.register_page(resources.v1_workflow_job_templates, WorkflowJobTemplates)
