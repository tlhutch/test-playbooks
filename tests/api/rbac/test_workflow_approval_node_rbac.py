import pytest
import awxkit.exceptions

from tests.api import APITest


@pytest.mark.usefixtures('authtoken')
class TestApprovalNodeRBAC(APITest):
    """Test permissions on Who can view, create, approve/deny, grant approval
    """

    @pytest.fixture(params=[
        'sysadmin',
        'org_admin',
        'wf_admin',
        'org_wf_admin',
        'org_approve',
        'wf_approve',
        'org_executor',
        'wf_executor',
        'org_read',
        'wf_read',
        'system_auditor',
        'user_in_org',
        'random_user'
    ])
    def user_with_role_and_workflow(self, request, factories):
        role = request.param

        fixture_args = request.node.get_closest_marker('fixture_args')
        if fixture_args and 'roles' in fixture_args.kwargs:
            only_create = fixture_args.kwargs['roles']
            if role not in only_create:
                pytest.skip()

        org = factories.organization()
        user = factories.user(organization=org)
        wfjt = factories.workflow_job_template(organization=org)
        assert org.id == user.related.organizations.get().results.pop().id
        if role == 'wf_executor':
            wfjt.set_object_roles(user, 'execute')
        if role == 'wf_read':
            wfjt.set_object_roles(user, 'read')
        if role == 'wf_approve':
            wfjt.set_object_roles(user, 'approve')
        if role == 'wf_admin':
            wfjt.set_object_roles(user, 'admin')
        if role == 'org_executor':
            org.set_object_roles(user, 'execute')
        if role == 'org_read':
            org.set_object_roles(user, 'read')
        if role == 'org_approve':
            org.set_object_roles(user, 'approve')
        if role == 'org_wf_admin':
            org.set_object_roles(user, 'workflow admin')
        if role == 'system_auditor':
            user.is_system_auditor = True
        if role == 'sysadmin':
            user.is_superuser = True
        if role == 'org_admin':
            org.set_object_roles(user, 'admin')
        elif role == 'user_in_org':
            # no further changes needed
            pass
        elif role == 'random_user':
            with pytest.raises(awxkit.exceptions.NoContent):
                org.related.users.post(dict(id=user.id, disassociate=True))
            random_org = factories.organization()
            with pytest.raises(awxkit.exceptions.NoContent):
                random_org.related.users.post(dict(id=user.id, associate=True))
        return user, wfjt, role

    def test_workflow_approval_and_activity_stream_visibility(self, v2, factories, user_with_role_and_workflow):
        """Verify that Users with no permission cannot view an approval"""
        # creation of users, workflow job template and workflow approval node
        user, wfjt, role = user_with_role_and_workflow
        approval_node = factories.workflow_job_template_node(
            workflow_job_template=wfjt,
            unified_job_template=None
        ).make_approval_node(timeout=100, description='Mark my words', name='hellow world')

        # launch the job, fetch the workflow approval associated with the approval node
        wf_job = wfjt.launch()
        wf_job.wait_until_status('running')
        approval_jt = approval_node.related.unified_job_template.get()
        approval_job_node = wf_job.related.workflow_nodes.get(unified_job_template=approval_jt.id).results.pop()
        wf_approval = approval_job_node.wait_for_job().related.job.get().wait_until_status('pending')

        # Verify that users with no permission cannot view the workflow approvals and access it's activity stream
        if role in ['user_in_org', 'random_user', 'org_read']:
            with self.current_user(user.username, user.password):
                all_pending_approvals = v2.workflow_approvals.get(status='pending').results
                assert wf_approval.id not in [approval.id for approval in all_pending_approvals]
                with pytest.raises(awxkit.exceptions.Forbidden):
                    wf_job.related.activity_stream.get()
        # Verify that users with permissions can view the workflow approvals and access it's activity stream
        else:
            with self.current_user(user.username, user.password):
                all_pending_approvals = v2.workflow_approvals.get(status='pending').results
                assert wf_approval.id in [approval.id for approval in all_pending_approvals]
                assert wf_job.related.activity_stream.get().count == 1

    def test_workflow_approval_node_creation(self, v2, factories, user_with_role_and_workflow):
        """Verify that Users with no permission cannot view an approval"""
        # creation of users, workflow job template and workflow approval node
        user, wfjt, role = user_with_role_and_workflow
        approval_node = factories.workflow_job_template_node(
            workflow_job_template=wfjt,
            unified_job_template=None
        ).make_approval_node(timeout=100, description='Mark my words', name='hellow world')

        # Verify that only users with permission can create an approval node
        if role in ['org_admin', 'sysadmin', 'wf_admin', 'org_wf_admin']:
            with self.current_user(user.username, user.password):
                approval_node = factories.workflow_job_template_node(
                    workflow_job_template=wfjt,
                    unified_job_template=None
                ).make_approval_node(timeout=100, description='Mark my words', name='hellow world')
                approval_jt = approval_node.related.unified_job_template.get()
                assert approval_jt.name == 'hellow world'
        else:
            with self.current_user(user.username, user.password):
                with pytest.raises(awxkit.exceptions.Forbidden):
                    approval_node = factories.workflow_job_template_node(
                        workflow_job_template=wfjt,
                        unified_job_template=None
                    ).make_approval_node(timeout=100, description='Mark my words', name='hellow world')

    @pytest.mark.yolo
    def test_workflow_approval_node_approve(self, v2, factories,
                                                                   user_with_role_and_workflow):
        """Verify that Users with no permission cannot view an approval"""
        # creation of users, workflow job template and workflow approval node
        user, wfjt, role = user_with_role_and_workflow
        approval_node = factories.workflow_job_template_node(
            workflow_job_template=wfjt,
            unified_job_template=None
        ).make_approval_node(timeout=100, description='Mark my words', name='hellow world')

        # launch the job, fetch the workflow approval associated with the approval node
        wf_job = wfjt.launch()
        wf_job.wait_until_status('running')
        approval_jt = approval_node.related.unified_job_template.get()
        approval_job_node = wf_job.related.workflow_nodes.get(unified_job_template=approval_jt.id).results.pop()
        wf_approval = approval_job_node.wait_for_job().related.job.get().wait_until_status('pending')

        # Verify that users with permission can approve the workflow approval node
        if role in ['sysadmin', 'org_admin', 'wf_admin', 'org_wf_admin', 'org_approve', 'wf_approve']:
            wf_approval.approve()
            all_successful_approvals = v2.workflow_approvals.get(status='successful').results
            assert wf_approval.id in [approval.id for approval in all_successful_approvals]
            wf_job.wait_until_completed().assert_successful()

        # Verify that users with no permission are forbidden to approve the workflow approval node
        else:
            with self.current_user(user.username, user.password):
                with pytest.raises(awxkit.exceptions.Forbidden):
                    wf_approval.approve()

    def test_workflow_approval_node_grant_approval(self, v2, factories, user_with_role_and_workflow):
        """Verify that Users with no permission cannot view an approval"""
        # creation of users, workflow job template and workflow approval node
        user, wfjt, role = user_with_role_and_workflow
        factories.workflow_job_template_node(
            workflow_job_template=wfjt,
            unified_job_template=None
        ).make_approval_node(timeout=100, description='Mark my words', name='hellow world')

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
