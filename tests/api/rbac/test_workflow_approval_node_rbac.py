import pytest
import awxkit.exceptions

from tests.api import APITest


@pytest.mark.usefixtures('authtoken')
class TestApprovalNodeRBAC(APITest):
    """Test permissions on who can view, create the approval node and it's activity stream, approve/deny, grant approval
    """
    def test_workflow_approval_and_activity_stream_visibility(self, v2, factories, user_with_role_and_workflow_with_approval_node):
        # creation of users, workflow job template and workflow approval node
        user, wfjt, role, approval_node = user_with_role_and_workflow_with_approval_node

        # launch the job, fetch the workflow approval associated with the approval node
        wf_job = wfjt.launch()
        wf_job.wait_until_status('running')
        approval_jt = approval_node.related.unified_job_template.get()
        approval_job_node = wf_job.related.workflow_nodes.get(unified_job_template=approval_jt.id).results.pop()
        wf_approval = approval_job_node.wait_for_job().related.job.get().wait_until_status('pending')

        # Verify that users with no permission cannot view the workflow approvals and access it's activity stream
        if role in ['user_in_org', 'random_user', 'org_read']:
            with self.current_user(user.username, user.password):
                approvals = v2.workflow_approvals.get(order_by='-created').results
                assert wf_approval.id not in [approval.id for approval in approvals]
                with pytest.raises(awxkit.exceptions.Forbidden):
                    wf_job.related.activity_stream.get()
        # Verify that users with permissions can view the workflow approvals and access it's activity stream
        else:
            with self.current_user(user.username, user.password):
                approvals = v2.workflow_approvals.get(order_by='-created').results
                assert wf_approval.id in [approval.id for approval in approvals]
                assert wf_job.related.activity_stream.get().count == 1

    def test_workflow_approval_node_creation(self, v2, factories, user_with_role_and_workflow_with_approval_node):
        # creation of users, workflow job template and workflow approval node
        user, wfjt, role, approval_node = user_with_role_and_workflow_with_approval_node
        approval_jt = approval_node.related.unified_job_template.get()

        # Verify users without permission cannot create an approval node
        if role in ['org_admin', 'sysadmin', 'wf_admin', 'org_wf_admin']:
            with self.current_user(user.username, user.password):
                factories.workflow_job_template_node(
                    workflow_job_template=wfjt,
                    unified_job_template=None
                ).make_approval_node()
                assert approval_jt.timeout == 0
        else:
            with self.current_user(user.username, user.password):
                with pytest.raises(awxkit.exceptions.Forbidden):
                    factories.workflow_job_template_node(
                        workflow_job_template=wfjt,
                        unified_job_template=None
                    ).make_approval_node()

    def test_workflow_approval_node_approve(self, v2, factories, user_with_role_and_workflow_with_approval_node):
        # creation of users, workflow job template and workflow approval node
        user, wfjt, role, approval_node = user_with_role_and_workflow_with_approval_node

        # launch the job, fetch the workflow approval associated with the approval node
        wf_job = wfjt.launch()
        wf_job.wait_until_status('running')
        approval_jt = approval_node.related.unified_job_template.get()
        approval_job_node = wf_job.related.workflow_nodes.get(unified_job_template=approval_jt.id).results.pop()
        wf_approval = approval_job_node.wait_for_job().related.job.get().wait_until_status('pending')

        # Verify that users with permission can approve the workflow approval node
        if role in ['sysadmin', 'org_admin', 'wf_admin', 'org_wf_admin', 'org_approve', 'wf_approve']:
            with self.current_user(user.username, user.password):
                wf_approval.approve()
            all_successful_approvals = v2.workflow_approvals.get(status='successful', order_by='-created').results
            assert wf_approval.id in [approval.id for approval in all_successful_approvals]
            wf_job.wait_until_completed().assert_successful()

        # Verify that users with no permission are forbidden to approve the workflow approval node
        else:
            with self.current_user(user.username, user.password):
                with pytest.raises(awxkit.exceptions.Forbidden):
                    wf_approval.approve()

    def test_workflow_approval_node_grant_approval(self, v2, factories, user_with_role_and_workflow_with_approval_node):
        # creation of users, workflow job template and workflow approval node
        user, wfjt, role, approval_node = user_with_role_and_workflow_with_approval_node

        # Verify that only users with permission can grant approval
        if role == 'wf_admin':
            # wf_admin can't see temp_user if they are not in the same org
            temp_user = factories.user(organization=user.related.organizations.get().results.pop())
        else:
            temp_user = factories.user()

        if role in ['org_admin', 'sysadmin', 'wf_admin']:
            with self.current_user(user.username, user.password):
                wfjt.set_object_roles(temp_user, 'approve')
            approve_roles = [role for role in temp_user.related.roles.get().results if role.name == 'Approve']
            assert len(approve_roles) == 1
            approve_role = approve_roles.pop()
            assert approve_role.related.workflow_job_template.get().id == wfjt.id
        else:
            with self.current_user(user.username, user.password):
                with pytest.raises(awxkit.exceptions.Forbidden):
                    wfjt.set_object_roles(temp_user, 'approve')
            approve_roles = [role for role in temp_user.related.roles.get().results if role.name == 'Approve']
            assert len(approve_roles) == 0

