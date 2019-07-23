import time

import pytest
from towerkit.utils import poll_until

from tests.api import APITest


@pytest.mark.usefixtures('authtoken')
class TestWorkflowApprovalNodes(APITest):
    """Test approval nodes that enable users to require manual approval as a part of a workflow.
    """

    @pytest.mark.parametrize('approve', [True, False], ids=['approve', 'deny'])
    @pytest.mark.parametrize('user', ['sysadmin', 'org_admin', 'approver'])
    def test_approval_node_happy_path(self, v2, factories, org_admin, approve, user):
        """Create a workflow with an approval node and approve it."""
        org = org_admin.related.organizations.get().results.pop()
        if user == 'approver':
            user = factories.user(organization=org)
            org.set_object_roles(user, 'approve')
        if user == 'org_admin':
            user = org_admin
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

        # TODO: should approval job template have an organization if the wfjt has one?
        # NO SHOULD NOT
        # assert approval_jt.related.organization.get().id == org.id

        if not approve:
            # add error handling node so workflow does not fail
            approval_node.add_failure_node(unified_job_template=inner_wfjt)

        wf_job = wfjt.launch()
        wf_job.wait_until_status('running')
        approval_job_node = wf_job.related.workflow_nodes.get(unified_job_template=approval_jt.id).results.pop()
        poll_until(lambda: hasattr(approval_job_node.get().related, 'job'), interval=1, timeout=60)
        wf_approval = approval_job_node.related.job.get()

        # Assert the workflow approval that was associated with the approval job node is in list of
        # approvals pending (this is what user will get notification about)
        all_pending_approvals = v2.workflow_approvals.get(status='pending').results
        assert wf_approval.id in [approval.id for approval in all_pending_approvals]

        if approve:
            if user != 'sysadmin':
                with self.current_user(user.username, user.password):
                    wf_approval.related.approve.post()
            else:
                wf_approval.related.approve.post()
            all_successful_approvals = v2.workflow_approvals.get(status='successful').results
            assert wf_approval.id in [approval.id for approval in all_successful_approvals]
        # we will deny
        else:
            if user != 'sysadmin':
                with self.current_user(user.username, user.password):
                    wf_approval.related.deny.post()
            else:
                wf_approval.related.deny.post()

            all_denied_approvals = v2.workflow_approvals.get(status='failed').results
            assert wf_approval.id in [approval.id for approval in all_denied_approvals]

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
        # HACK passing WFJT as the unified_job_template does not work with towerkit "create" method
        wfjt_node = wfjt.get_related('workflow_nodes').post(dict(
            workflow_job_template=wfjt.id,
            unified_job_template=inner_wfjt.id
        ))
        # Add success node so there is something to approve/deny
        wfjt_node.related.success_nodes.post(dict(unified_job_template=inner_wfjt.id))

        # WAIT! I want it to be an approval node
        # Remove UJT + ask to make it an approval node
        wfjt_node.unified_job_template = None
        wfjt_node.make_approval_node(timeout=timeout, description=description)
        # Confirm that approval JT created for us is what we expect
        approval_jt = wfjt_node.related.unified_job_template.get()
        assert approval_jt.timeout == timeout
        assert approval_jt.description == description
        wf_job = wfjt.launch()
        wf_job.wait_until_status('running')

        approval_job_node = wf_job.related.workflow_nodes.get(unified_job_template=approval_jt.id).results.pop()
        poll_until(lambda: hasattr(approval_job_node.get().related, 'job'), interval=1, timeout=60)
        wf_approval = approval_job_node.related.job.get()

        # Assert the workflow approval that was associated with the approval job node is in list of
        # approvals pending (this is what user will get notification about)
        all_pending_approvals = v2.workflow_approvals.get(status='pending').results
        assert wf_approval.id in [approval.id for approval in all_pending_approvals]

        wf_approval.related.approve.post()
        all_successful_approvals = v2.workflow_approvals.get(status='successful').results
        assert wf_approval.id in [approval.id for approval in all_successful_approvals]

        # TODO need to make an approval job type in towerkit
        # approval_job.get().assert_successful()
        wf_job.wait_until_completed().assert_successful()

    def test_approval_node_timeout(self, v2, factories):
        """Create a workflow with an approval node and approve it."""
        wfjt = factories.workflow_job_template()
        timeout = 1
        approval_node = factories.workflow_job_template_node(
            workflow_job_template=wfjt,
            unified_job_template=None
            ).make_approval_node(timeout=timeout)

        # Confirm that approval JT created for us is what we expect
        approval_jt = approval_node.related.unified_job_template.get()
        assert approval_jt.timeout == timeout

        wf_job = wfjt.launch()
        wf_job.wait_until_status('running')
        approval_job_node = wf_job.related.workflow_nodes.get(unified_job_template=approval_jt.id).results.pop()
        poll_until(lambda: hasattr(approval_job_node.get().related, 'job'), interval=1, timeout=60)
        wf_approval = approval_job_node.related.job.get()
        # Sleep for longer than timeout to be generous since it is so short
        time.sleep(timeout * 5)
        wf_approval = approval_job_node.related.job.get()
        assert wf_approval.status == f'failed', 'Workflow Approval did not fail after timeout passed! \n' \
                                     f'Workflow Approval: {wf_approval}\n' \
                                     f'Approval JT: {approval_jt}\n' \
                                     f'Workflow Job: {wf_job.get()}\n'
        all_failed_approvals = v2.workflow_approvals.get(status='failed').results
        assert wf_approval.id in [approval.id for approval in all_failed_approvals]

        # TODO need to make an approval job type in towerkit
        # approval_job.get().assert_status('failed')
        wf_job.wait_until_completed().assert_status('failed')

    def test_workflow_approval_visibility(self, v2, factories, org_admin):
        """Create a workflow with an approval node and approve it."""
        org = org_admin.related.organizations.get().results.pop()
        wf_approve_user = factories.user(organization=org)
        org_approve_user = factories.user(organization=org)
        org.set_object_roles(org_approve_user, 'approve')
        underpriv_user = factories.user(organization=org)
        wfjt = factories.workflow_job_template(organization=org)
        wfjt.set_object_roles(wf_approve_user, 'approve')
        wfjt = factories.workflow_job_template()
        approval_node = factories.workflow_job_template_node(
            workflow_job_template=wfjt,
            unified_job_template=None
            ).make_approval_node()

        # Confirm that approval JT created for us is what we expect
        approval_jt = approval_node.related.unified_job_template.get()

        wf_job = wfjt.launch()
        wf_job.wait_until_status('running')
        approval_job_node = wf_job.related.workflow_nodes.get(unified_job_template=approval_jt.id).results.pop()
        poll_until(lambda: hasattr(approval_job_node.get().related, 'job'), interval=1, timeout=60)
        wf_approval = approval_job_node.related.job.get()

        with self.current_user(wf_approve_user):
            assert v2.workflow_approvals.get(status='failed').count == 1, 'Not seeing proper number of approvals'
            approvals = v2.workflow_approvals.get(status='failed').results
            assert wf_approval.id in [approval.id for approval in approvals]

        with self.current_user(org_approve_user):
            approvals = v2.workflow_approvals.get(status='failed').results
            assert wf_approval.id in [approval.id for approval in approvals]

        with self.current_user(org_approve_user):
            approvals = v2.workflow_approvals.get(status='failed').results
            assert wf_approval.id in [approval.id for approval in approvals]

        with self.current_user(underpriv_user):
            assert v2.workflow_approvals.get(status='failed').count == 1, 'Not seeing proper number of approvals'
            approvals = v2.workflow_approvals.get(status='failed').results
            assert wf_approval.id in [approval.id for approval in approvals]

        wf_approval.related.approve.post()
        # TODO need to make an approval job type in towerkit
        # approval_job.get().assert_status('failed')
        wf_job.wait_until_completed().assert_status('success')
