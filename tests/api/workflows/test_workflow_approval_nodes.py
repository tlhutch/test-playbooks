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

    @pytest.mark.parametrize('approve', [True, False])
    def test_simplest_use_case(self, v2, factories, org_admin, approve):
        """Create a workflow with an approval node and approve it."""
        org = org_admin.related.organizations.get().results.pop()
        inner_wfjt = factories.workflow_job_template(organization=org)
        wfjt = factories.workflow_job_template(organization=org)
        timeout = 100
        description = 'Mark my words'
        name = 'hellow world'
        approval_node = factories.workflow_job_template_node(
            workflow_job_template=wfjt,
            unified_job_template=None
            ).make_approval_node(timeout=timeout, description=description, name=name)

        # Confirm that approval JT created for us is what we expect
        approval_jt = approval_node.related.unified_job_template.get()
        assert approval_jt.timeout == timeout
        assert approval_jt.description == description
        assert approval_jt.name == name

        #TODO: should approval job template have an organization if the wfjt has one?
        # NO SHOULD NOT
        # assert approval_jt.related.organization.get().id == org.id

        if not approve:
            # add error handling node so workflow does not fail
            approval_node.add_failure_node(unified_job_template=inner_wfjt)

        wf_job = wfjt.launch()
        wf_job.wait_until_status('running')

        approval_job_node = wf_job.related.workflow_nodes.get(unified_job_template=approval_jt.id).results.pop()
        wf_approval = approval_job_node.related.job.get()

        # Assert the workflow approval that was associated with the approval job node is in list of
        # approvals pending (this is what user will get notification about)
        all_pending_approvals = v2.workflow_approvals.get(status='pending').results
        assert wf_approval.id in [ approval.id for approval in all_pending_approvals]

        if approve:
            wf_approval.related.approve.post()
            all_successful_approvals = v2.workflow_approvals.get(status='successful').results
            assert wf_approval.id in [ approval.id for approval in all_successful_approvals]
        else:
            wf_approval.related.deny.post()
            all_denied_approvals = v2.workflow_approvals.get(status='failed').results
            assert wf_approval.id in [ approval.id for approval in all_denied_approvals]


        # TODO need to make an approval job type in towerkit
        # approval_job.get().assert_successful()
        wf_job.wait_until_completed().assert_successful()


    def test_update_existing_node_to_approval_node(self, v2, factories, org_admin):
        """Create a workflow with an approval node and approve it."""
        org = org_admin.related.organizations.get().results.pop()
        inner_wfjt = factories.workflow_job_template(organization=org)
        wfjt = factories.workflow_job_template(organization=org)
        timeout = 100
        description = 'Mark my words'

        # Create regular node
        wfjt_node = factories.workflow_job_template_node(
            workflow_job_template=wfjt,
            unified_job_template=inner_wfjt
            )
        wfjt_node.add_success_node(unified_job_template=inner_wfjt)

        # WAIT! I want it to be an approval node
        # Remove UJT + ask to make it an approval node
        wfjt_node.unified_job_template = None
        wfjt_node.make_approval_node(timeout=timeout, description=description, name=name)
        # Confirm that approval JT created for us is what we expect
        approval_jt = wfjt_node.related.unified_job_template.get()
        assert approval_jt.timeout == timeout
        assert approval_jt.description == description
        assert approval_jt.name == name
        wf_job = wfjt.launch()
        wf_job.wait_until_status('running')

        # not sure if the approval job should be used like this?
        poll_until(lambda: hasattr(approval_jt.get().related, 'current_job'), interval=1, timeout=60)
        approval_job = approval_jt.related.current_job.get()
        approval_job_node = wf_job.related.workflow_nodes.get(unified_job_template=approval_jt.id).results.pop()
        wf_approval = approval_job_node.related.job.get()

        # Assert the workflow approval that was associated with the approval job node is in list of
        # approvals pending (this is what user will get notification about)
        all_pending_approvals = v2.workflow_approvals.get(status='pending').results
        assert wf_approval.id in [ approval.id for approval in all_pending_approvals]

        wf_approval.related.approve.post()
        all_successful_approvals = v2.workflow_approvals.get(status='successful').results
        assert wf_approval.id in [ approval.id for approval in all_successful_approvals]
