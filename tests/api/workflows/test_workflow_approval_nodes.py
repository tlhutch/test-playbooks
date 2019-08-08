import pytest
from awxkit.utils import poll_until
import awxkit.exceptions

from tests.api import APITest


@pytest.mark.usefixtures('authtoken')
class TestWorkflowApprovalNodes(APITest):
    """Test approval nodes that enable users to require manual approval as a part of a workflow.
    """

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
        poll_until(lambda: hasattr(approval_job_node.get().related, 'job'), interval=1, timeout=60)
        wf_approval = approval_job_node.related.job.get()

        # Assert the workflow approval that was associated with the approval job node is in list of
        # approvals pending (this is what user will get notification about)
        poll_until(lambda: wf_approval.get().status == 'pending', interval=1, timeout=60)
        all_pending_approvals = v2.workflow_approvals.get(status='pending').results
        assert wf_approval.id in [approval.id for approval in all_pending_approvals]
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

    @pytest.mark.parametrize('role', ['wf_executor', 'wf_read', 'org_executor', 'org_read', 'system_auditor', 'user_in_org', 'random_user'])
    def test_users_without_role_cannot_approve(self, v2, factories, org_admin, role):
        """Verify that Users with no permission cannot approve a node"""
        org = org_admin.related.organizations.get().results.pop()
        wfjt = factories.workflow_job_template(organization=org)

        if role == 'wf_executor':
            user = factories.user()
            wfjt.set_object_roles(user, 'execute')
        if role == 'wf_read':
            user = factories.user()
            wfjt.set_object_roles(user, 'read')
        if role == 'org_executor':
            user = factories.user()
            org.set_object_roles(user, 'execute')
        if role == 'org_read':
            user = factories.user()
            org.set_object_roles(user, 'read')
        if role == 'system_auditor':
            user = factories.user(is_system_auditor=True)
        elif role == 'user_in_org':
            user = factories.user(organization=org)
        else:
            random_org = factories.organization()
            user = factories.user(organization=random_org)
        timeout = 100
        description = 'Mark my words'
        name = 'hellow world'
        approval_node = factories.workflow_job_template_node(
            workflow_job_template=wfjt,
            unified_job_template=None
        ).make_approval_node(timeout=timeout, description=description, name=name)

        wf_job = wfjt.launch()
        wf_job.wait_until_status('running')
        approval_jt = approval_node.related.unified_job_template.get()
        approval_job_node = wf_job.related.workflow_nodes.get(unified_job_template=approval_jt.id).results.pop()
        poll_until(lambda: hasattr(approval_job_node.get().related, 'job'), interval=1, timeout=60)
        wf_approval = approval_job_node.related.job.get()
        poll_until(lambda: wf_approval.get().status == 'pending', interval=1, timeout=60)

        with self.current_user(user.username, user.password):
            with pytest.raises(awxkit.exceptions.Forbidden):
                wf_approval.approve()

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
        poll_until(lambda: hasattr(approval_job_node.get().related, 'job'), interval=1, timeout=60)
        wf_approval = approval_job_node.related.job.get()

        # Assert the workflow approval that was associated with the approval job node is in list of
        # approvals pending (this is what user will get notification about)
        poll_until(lambda: wf_approval.get().status == 'pending', interval=1, timeout=60)
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

        # Confirm that approval JT created for us is what we expect
        approval_jt = approval_node.related.unified_job_template.get()
        assert approval_jt.timeout == 0

        approval_jt.timeout = 1
        approval_jt = approval_node.related.unified_job_template.get()
        assert approval_jt.timeout == 1


        wf_job = wfjt.launch()
        wf_job.wait_until_status('running')
        approval_job_node = wf_job.related.workflow_nodes.get(unified_job_template=approval_jt.id).results.pop()
        poll_until(lambda: hasattr(approval_job_node.get().related, 'job'), interval=1, timeout=60)
        wf_approval = approval_job_node.related.job.get()
        wf_approval.wait_until_status('failed')
        assert wf_approval.status == f'failed', 'Workflow Approval did not fail after timeout passed! \n' \
                                     f'Workflow Approval: {wf_approval}\n' \
                                     f'Approval JT: {approval_jt}\n' \
                                     f'Workflow Job: {wf_job.get()}\n'
        with pytest.raises(awxkit.exceptions.BadRequest):
            wf_approval.approve()
        all_failed_approvals = v2.workflow_approvals.get(status='failed').results
        assert wf_approval.id in [approval.id for approval in all_failed_approvals]
        # also assert reason of failure and timeout variables in workflow approvals
        wf_job.wait_until_completed().assert_status('failed')
        import pdb
        pdb.set_trace()


    @pytest.mark.parametrize('role', ['sysadmin', 'org_admin', 'wf_admin', 'org_wf_admin', 'org_approve', 'wf_approve', 'org_executor', 'wf_executor', 'org_read', 'wf_read','system_auditor', 'user_in_org', 'random_user'])
    def test_workflow_approval_visibility(self, v2, factories, org_admin, role):
        """Verify that Users with no permission cannot view an approval"""
        org = org_admin.related.organizations.get().results.pop()
        wfjt = factories.workflow_job_template(organization=org)

        if role == 'wf_executor':
            user = factories.user()
            wfjt.set_object_roles(user, 'execute')
        if role == 'wf_read':
            user = factories.user()
            wfjt.set_object_roles(user, 'read')
        if role == 'wf_approve':
            user = factories.user()
            wfjt.set_object_roles(user, 'approve')
        if role == 'wf_admin':
            user = factories.user()
            wfjt.set_object_roles(user, 'admin')
        if role == 'org_executor':
            user = factories.user()
            org.set_object_roles(user, 'execute')
        if role == 'org_read':
            user = factories.user()
            org.set_object_roles(user, 'read')
        if role == 'org_approve':
            user = factories.user()
            org.set_object_roles(user, 'approve')
        if role == 'org_wf_admin':
            user = factories.user()
            org.set_object_roles(user, 'workflow admin')
        if role == 'system_auditor':
            user = factories.user(is_system_auditor=True)
        if role == 'org_admin':
            user = org_admin
        elif role == 'user_in_org':
            user = factories.user(organization=org)
        elif role == 'random_user':
            random_org = factories.organization()
            user = factories.user(organization=random_org)
        timeout = 100
        description = 'Mark my words'
        name = 'hellow world'
        approval_node = factories.workflow_job_template_node(
            workflow_job_template=wfjt,
            unified_job_template=None
        ).make_approval_node(timeout=timeout, description=description, name=name)

        wf_job = wfjt.launch()
        wf_job.wait_until_status('running')
        approval_jt = approval_node.related.unified_job_template.get()
        approval_job_node = wf_job.related.workflow_nodes.get(unified_job_template=approval_jt.id).results.pop()
        poll_until(lambda: hasattr(approval_job_node.get().related, 'job'), interval=1, timeout=60)
        wf_approval = approval_job_node.related.job.get()
        poll_until(lambda: wf_approval.get().status == 'pending', interval=1, timeout=60)
        if role == 'user_in_org' or role == 'random_user':
            with self.current_user(user.username, user.password):
                all_pending_approvals = v2.workflow_approvals.get(status='pending').results
                assert wf_approval.id not in [approval.id for approval in all_pending_approvals]
        elif role == 'sysadmin':
            all_pending_approvals = v2.workflow_approvals.get(status='pending').results
            assert wf_approval.id in [approval.id for approval in all_pending_approvals]
        else:
            with self.current_user(user.username, user.password):
                all_pending_approvals = v2.workflow_approvals.get(status='pending').results
                assert wf_approval.id in [approval.id for approval in all_pending_approvals]

        wf_approval.approve()
        wf_job.wait_until_completed().assert_status('successful')
