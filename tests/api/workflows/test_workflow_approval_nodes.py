import pytest
import awxkit.exceptions

from tests.api import APITest


@pytest.mark.usefixtures('authtoken')
class TestWorkflowApprovalNodes(APITest):
    """Test approval nodes that enable users to require manual approval as a part of a workflow.
    """

    @pytest.mark.yolo
    @pytest.mark.parametrize('approve', [True, False], ids=['approve', 'deny'])
    @pytest.mark.parametrize('user', ['sysadmin', 'org_admin', 'org_approver', 'wf_approver'])
    def test_approval_node_happy_path(self, v2, factories, org_admin, approve, user):
        """Create a workflow with an approval node and approve it."""
        org = org_admin.related.organizations.get().results.pop()
        if user == 'org_approver':
            user = factories.user(organization=org)
            with self.current_user(org_admin):
                org.set_object_roles(user, 'approve')
        if user == 'org_admin':
            user = org_admin
        inner_wfjt = factories.workflow_job_template(organization=org)
        wfjt = factories.workflow_job_template(organization=org)
        if user == 'wf_approver':
            user = factories.user(organization=org)
            with self.current_user(org_admin):
                wfjt.set_object_roles(user, 'approve')

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

        if not approve:
            # add error handling node so workflow does not fail
            approval_node.add_failure_node(unified_job_template=inner_wfjt)

        wf_job = wfjt.launch()
        wf_job.wait_until_status('running')
        approval_job_node = wf_job.related.workflow_nodes.get(unified_job_template=approval_jt.id).results.pop()
        wf_approval = approval_job_node.wait_for_job().related.job.get().wait_until_status('pending')

        # Assert the workflow approval that was associated with the approval job node is in list of
        # approvals pending (this is what user will get notification about)
        all_pending_approvals = v2.workflow_approvals.get(status='pending').results
        assert wf_approval.id in [approval.id for approval in all_pending_approvals]
        assert wf_job.status == 'running'
        if approve:
            if user != 'sysadmin':
                with self.current_user(user.username, user.password):
                    wf_approval.approve()
            else:
                wf_approval.approve()
            all_successful_approvals = v2.workflow_approvals.get(status='successful').results
            assert wf_approval.id in [approval.id for approval in all_successful_approvals]
        # we will deny
        else:
            if user != 'sysadmin':
                with self.current_user(user.username, user.password):
                    wf_approval.deny()
            else:
                wf_approval.deny()

            all_denied_approvals = v2.workflow_approvals.get(status='failed').results
            assert wf_approval.id in [approval.id for approval in all_denied_approvals]

        wf_job.wait_until_completed().assert_successful()

    def test_update_existing_node_to_approval_node(self, v2, factories, org_admin):
        """Create a workflow with an approval node and approve it."""
        org = org_admin.related.organizations.get().results.pop()
        inner_wfjt = factories.workflow_job_template(organization=org)
        wfjt = factories.workflow_job_template(organization=org)
        timeout = 100
        description = 'Mark my words'

        # Create regular node
        # HACK passing WFJT as the unified_job_template does not work with awxkit "create" method
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
        wf_approval = approval_job_node.wait_for_job().related.job.get().wait_until_status('pending')

        # Assert the workflow approval that was associated with the approval job node is in list of
        # approvals pending (this is what user will get notification about)
        all_pending_approvals = v2.workflow_approvals.get(status='pending').results
        assert wf_approval.id in [approval.id for approval in all_pending_approvals]

        wf_approval.approve()
        all_successful_approvals = v2.workflow_approvals.get(status='successful').results
        assert wf_approval.id in [approval.id for approval in all_successful_approvals]

        wf_job.wait_until_completed().assert_successful()

    def test_approval_node_timeout(self, v2, factories):
        """Create a workflow with an approval node and approve it."""
        wfjt = factories.workflow_job_template()
        approval_node = factories.workflow_job_template_node(
            workflow_job_template=wfjt,
            unified_job_template=None
            ).make_approval_node()

        # Verify that the timeout is set 0 by default
        approval_jt = approval_node.related.unified_job_template.get()
        assert approval_jt.timeout == 0

        # Verify that we can edit the timeout
        approval_jt.timeout = 1
        approval_jt = approval_node.related.unified_job_template.get()
        assert approval_jt.timeout == 1

        wf_job = wfjt.launch()
        wf_job.wait_until_status('running')
        approval_job_node = wf_job.related.workflow_nodes.get(unified_job_template=approval_jt.id).results.pop()
        wf_approval = approval_job_node.wait_for_job().related.job.get().wait_until_status('failed')
        # Verify that the workflow approval is failed since the node timed out
        assert wf_approval.status == f'failed', 'Workflow Approval did not fail after timeout passed! \n' \
                                     f'Workflow Approval: {wf_approval}\n' \
                                     f'Approval JT: {approval_jt}\n' \
                                     f'Workflow Job: {wf_job.get()}\n'
        assert wf_approval.job_explanation == 'This approval node has timed out.'
        # also assert timeout variable whenever it is implemented
        all_failed_approvals = v2.workflow_approvals.get(status='failed').results
        assert wf_approval.id in [approval.id for approval in all_failed_approvals]
        # Verify that you can not approve/deny after the timeout
        with pytest.raises(awxkit.exceptions.Forbidden):
            wf_approval.approve()
        wf_job.wait_until_completed().assert_status('failed')

    def test_workflow_job_template_deletion_scenarios(self, v2, factories, org_admin):
        org = org_admin.related.organizations.get().results.pop()
        wfjt = factories.workflow_job_template(organization=org)
        approval_node = factories.workflow_job_template_node(
            workflow_job_template=wfjt,
            unified_job_template=None
        ).make_approval_node()

        approval_jt = approval_node.related.unified_job_template.get()
        wf_job = wfjt.launch()
        wf_job.wait_until_status('running')
        approval_job_node = wf_job.related.workflow_nodes.get(unified_job_template=approval_jt.id).results.pop()
        wf_approval = approval_job_node.wait_for_job().related.job.get().wait_until_status('pending')
        wf_approval.approve()
        all_successful_approvals = v2.workflow_approvals.get(status='successful').results
        assert wf_approval.id in [approval.id for approval in all_successful_approvals]
        # make sure you cannot approve again
        with pytest.raises(awxkit.exceptions.Forbidden):
            wf_approval.approve()

        wfjt.delete()
        assert v2.workflow_job_templates.get(id=wfjt.id).count == 0
        with pytest.raises(awxkit.exceptions.NotFound):
            wfjt.launch()
        with pytest.raises(awxkit.exceptions.NotFound):
            approval_node.related.unified_job_template.get()
        assert v2.workflow_approvals.get(id=wf_approval.id).results.count != 0

    def test_workflow_approval_node_deletion_scenarios(self, v2, factories, org_admin):
        org = org_admin.related.organizations.get().results.pop()
        wfjt = factories.workflow_job_template(organization=org)
        approval_node = factories.workflow_job_template_node(
            workflow_job_template=wfjt,
            unified_job_template=None
        ).make_approval_node()

        approval_jt = approval_node.related.unified_job_template.get()
        wf_job = wfjt.launch()
        wf_job.wait_until_status('running')
        approval_job_node = wf_job.related.workflow_nodes.get(unified_job_template=approval_jt.id).results.pop()
        wf_approval = approval_job_node.wait_for_job().related.job.get().wait_until_status('pending')
        wf_approval.deny()
        all_failed_approvals = v2.workflow_approvals.get(status='failed').results
        assert wf_approval.id in [approval.id for approval in all_failed_approvals]
        # make sure you cannot approve again
        with pytest.raises(awxkit.exceptions.Forbidden):
            wf_approval.approve()

        approval_node.delete()
        with pytest.raises(awxkit.exceptions.NotFound):
            approval_node.related.unified_job_template.get()
        assert v2.workflow_approvals.get(id=wf_approval.id).results.count != 0

    def test_various_workflow_branch_scenarios(self, v2, factories, org_admin):
        """Create a workflow with an approval node and approve it."""
        org = org_admin.related.organizations.get().results.pop()
        wfjt = factories.workflow_job_template(organization=org)
        jt1 = factories.job_template(organization=org)
        jt2 = factories.job_template(organization=org)
        job_template_node1 = factories.workflow_job_template_node(
            workflow_job_template=wfjt, unified_job_template=jt1)
        approval_node = factories.workflow_job_template_node(
            workflow_job_template=wfjt, unified_job_template=jt2).make_approval_node()

        # verify that the approval node does not impact the running of the job template node in a parallel branch
        wf_job = wfjt.launch()
        wf_job.wait_until_status('running')
        approval_jt = approval_node.related.unified_job_template.get()
        job_template_jt = job_template_node1.related.unified_job_template.get()
        approval_job_node = wf_job.related.workflow_nodes.get(unified_job_template=approval_jt.id).results.pop()
        job_template_job_node = wf_job.related.workflow_nodes.get(unified_job_template=job_template_jt.id).results.pop()
        wf_approval = approval_job_node.wait_for_job().related.job.get().wait_until_status('pending')

        job_template_job_node.related.job.get().wait_until_status('successful')
        assert wf_job.status == 'running'

        # verify that if the approval node got denied and it was the last node in that branch,
        # the job will still get failed irrespective of status of other parallel branches
        wf_approval.deny()
        all_denied_approvals = v2.workflow_approvals.get(status='failed').results
        assert wf_approval.id in [approval.id for approval in all_denied_approvals]
        wf_job.wait_until_completed()
        assert wf_job.status == 'failed'

        # verify that if there is a path to take after the approval node is denied, and if the path succeeds,
        # the job will still be successful
        job_template_node2 = factories.workflow_job_template_node(
            workflow_job_template=wfjt, unified_job_template=jt2)
        with pytest.raises(awxkit.exceptions.NoContent):
            approval_node.related.always_nodes.post(dict(id=job_template_node2.id))
        wf_job = wfjt.launch()
        wf_job.wait_until_status('running')
        approval_job_node = wf_job.related.workflow_nodes.get(unified_job_template=approval_jt.id).results.pop()
        wf_approval = approval_job_node.wait_for_job().related.job.get().wait_until_status('pending')
        wf_approval.deny()
        all_denied_approvals = v2.workflow_approvals.get(status='failed').results
        assert wf_approval.id in [approval.id for approval in all_denied_approvals]
        wf_job.wait_until_completed().assert_successful()
