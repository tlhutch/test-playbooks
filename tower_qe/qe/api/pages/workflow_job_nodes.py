from qe.api.pages import base
from qe.api import resources


class WorkflowJobNode(base.Base):

    pass

base.register_page(resources.v1_workflow_job_node, WorkflowJobNode)


class WorkflowJobNodes(base.BaseList, WorkflowJobNode):

    pass

base.register_page([resources.v1_workflow_job_nodes, resources.v1_workflow_job_node_always_nodes,
                    resources.v1_workflow_job_node_failure_nodes, resources.v1_workflow_job_node_success_nodes],
                   WorkflowJobNodes)
