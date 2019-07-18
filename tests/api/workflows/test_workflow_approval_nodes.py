import json

import pytest
from towerkit.exceptions import NoContent
from towerkit.utils import poll_until

from tests.api import APITest
from tests.api.workflows.utils import get_job_node
from tests.lib.helpers.workflow_utils import (WorkflowTree, WorkflowTreeMapper)


@pytest.mark.usefixtures('authtoken')
class TestWorkflowApprovalNodes(APITest):
    """Test approval nodes that enable users to require manual approval as a part of a workflow.
    """

    def test_happiest_path(self, v2, factories):
        """Create a workflow with an approval node and approve it."""
        wfjt = factories.workflow_job_template()
        timeout = 100
        description = 'Mark my words'
        approval_node = factories.workflow_job_template_node(
            workflow_job_template=wfjt,
            unified_job_template=None
            ).make_approval_node(timeout=timeout, description=description)
        wf_job = wfjt.launch()
        wf_job.wait_until_status('running')
        approval_jt = approval_node.related.unified_job_template.get()
        assert approval_jt.timeout == timeout
        assert approval_jt.description == description
        # not sure if the approval job should be used, or be visable?
        poll_until(lambda: hasattr(approval_jt.get().related, 'current_job'), interval=1, timeout=60)
        approval_job = approval_jt.related.current_job.get()
        approval_job_node = wf_job.related.workflow_nodes.get(unified_job_template=approval_jt.id).results.pop()
        wf_approval = approval_job_node.related.job.get()
        wf_approval.related.approve.post()
        all_successful_approvals = v2.workflow_approvals.get(status='successful').results
        assert wf_approval.id in [ approval.id for approval in all_successful_approvals]
        # TODO need to make an approval job type in towerkit
        # approval_job.get().assert_successful()
        wf_job.wait_until_completed().assert_successful()
