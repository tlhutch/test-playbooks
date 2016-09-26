from qe.api.pages import UnifiedJob
from qe.api import resources
import base


class WorkflowJob(UnifiedJob):

    def __str__(self):
        # TODO: Update after endpoint's fields are finished filling out
        return super(UnifiedJob, self).__str__()


base.register_page(resources.v1_workflow_job, WorkflowJob)


class WorkflowJobs(base.BaseList, WorkflowJob):

    pass

base.register_page([resources.v1_workflow_jobs,
                    resources.v1_workflow_job_template_jobs],
                   WorkflowJobs)
