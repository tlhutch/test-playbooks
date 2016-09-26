from qe.api.pages import base, JobTemplate
from qe.api import resources

class WorkflowJobTemplateNode(base.Base):

    dependencies = [JobTemplate]

    def create(self, unified_job_template=JobTemplate, workflow_job_template=None, **kw):
        self.create_and_update_dependencies(unified_job_template)
        payload = dict(unified_job_template=self.dependency_store[JobTemplate].id)
        if workflow_job_template:
            payload['workflow_job_template'] = workflow_job_template.id

        return self.update_identity(WorkflowJobTemplateNodes(self.testsetup).post(payload))

base.register_page(resources.v1_workflow_job_template_node, WorkflowJobTemplateNode)


class WorkflowJobTemplateNodes(base.BaseList, WorkflowJobTemplateNode):

    pass

base.register_page([resources.v1_workflow_job_template_nodes, resources.v1_workflow_job_template_workflow_nodes,
                    resources.v1_workflow_job_template_nodes_always_nodes, resources.v1_workflow_job_template_nodes_failure_nodes,
                    resources.v1_workflow_job_template_nodes_success_nodes], WorkflowJobTemplateNodes)
