import logging
from awxkit.utils import suppress

from tests.lib.notification_services import (confirm_notification, can_confirm_notification)
import awxkit.exceptions as exc
import pytest
from tests.api import APITest
log = logging.getLogger(__name__)


def associate_notification_template(notification_template_pg, resource_pg, event):
    """Associate notification template to tower resource"""
    nt_id = notification_template_pg.id
    resource_nt_pg = resource_pg.get_related('notification_templates_' + event)
    nt_count = resource_nt_pg.get().count

    # Associate notification template
    with pytest.raises(exc.NoContent):
        payload = dict(id=nt_id)
        resource_nt_pg.post(payload)

    # Confirm n.t. count increased by one
    notification_templates = resource_nt_pg.get(order_by='-id')
    updated_nt_count = notification_templates.count
    assert updated_nt_count == nt_count + 1

    # Confirm n.t. associated with resource
    latest_nt = notification_templates.results[0]
    assert latest_nt.id == nt_id


def expected_job_notification(tower_url, notification_template_pg, job_pg, approval_node, wf_approval, status, tower_message=False):
    """Returns notification message expected for given job and state.
    By default, returns message as it would be shown in notification service
    (if tower_message is True, returns message shown on notifications endpoint).
    """
    nt_type = notification_template_pg.notification_type
    if tower_message:
        msg = 'The approval node "' + str(approval_node.summary_fields.unified_job_template.name) + '" ' + status + '. ' + str(tower_url) + '/#/workflows/' + str(job_pg.id)
    elif nt_type == "slack":
        if status == 'needs review':
            msg = 'The approval node "' + str(approval_node.summary_fields.unified_job_template.name) + '" needs review. This node can be viewed at: <' + str(
                    tower_url) + '/#/workflows/' + str(job_pg.id) + '>'
        else:
            msg = 'The approval node "' + str(approval_node.summary_fields.unified_job_template.name) + '" ' + status + '. <' + str(tower_url) + '/#/workflows/' + str(job_pg.id) + '>'
    elif nt_type == "webhook":
        if status == 'needs review':
            msg = 'The approval node "' + str(
                approval_node.summary_fields.unified_job_template.name) + '" needs review. This node can be viewed at: ' + str(
                tower_url) + '/#/workflows/' + str(job_pg.id)
        else:
            msg = 'The approval node "' + str(approval_node.summary_fields.unified_job_template.name) + '" ' + status + '. ' + str(tower_url) + '/#/workflows/' + str(job_pg.id)
        headers = notification_template_pg.notification_configuration['headers']
        if wf_approval.finished is not None:
            finished = wf_approval.finished.replace('Z', '+00:00')
        else:
            finished = wf_approval.finished
        body = {'id': wf_approval.id,
                'name': approval_node.summary_fields.unified_job_template.name,
                'url': str(tower_url) + '/#/workflows/' + str(job_pg.id),
                'created_by': wf_approval.summary_fields['created_by']['username'],
                'started': wf_approval.started,
                'finished': finished,
                'status': wf_approval.status,
                'traceback': wf_approval.result_traceback,
                'body': msg
                }
        msg = (headers, body)
    else:
        raise Exception("notification type %s not supported" % nt_type)
    return msg


@pytest.mark.usefixtures('authtoken')
class Test_Notifications(APITest):
    """Notification tests"""

    @pytest.mark.parametrize("nt_type", ['slack', 'webhook'])
    def test_workflow_approval_notifications(self, factories, workflow_job_template,
                                      slack_notification_template, webhook_notification_template, tower_baseurl, nt_type):
        """Test notifications for Workflow Approval on Slack and Webhooks"""
        # enable notification on approval
        if nt_type == 'slack':
            notification_template = slack_notification_template
        else:
            notification_template = webhook_notification_template
        associate_notification_template(notification_template, workflow_job_template, 'approvals')
        approval_node = factories.workflow_job_template_node(
            workflow_job_template=workflow_job_template,
            unified_job_template=None
            ).make_approval_node()
        # launch the job and take action on the approval nodes
        wf_job = workflow_job_template.launch()
        wf_job.wait_until_status('running')
        approval_jt = approval_node.related.unified_job_template.get()
        approval_job_node = wf_job.related.workflow_nodes.get(unified_job_template=approval_jt.id).results.pop()
        wf_approval = approval_job_node.wait_for_job().related.job.get().wait_until_status('pending')

        # Confirm that notification is received when approval node needs approval
        if can_confirm_notification(notification_template):
            msg = expected_job_notification(tower_baseurl, notification_template, wf_job, approval_node, wf_approval, 'needs review')
            assert confirm_notification(notification_template, msg)
        wf_approval.approve()
        status = 'was approved'
        wf_approval = approval_job_node.wait_for_job().related.job.get()
        wf_job.wait_until_completed().assert_successful()
        # assert that the notification is sent for all enabled events and that the message is correct
        notifications_expected = 2
        notifications_pg = wf_job.get_related('notifications').wait_until_count(notifications_expected)
        notification_pg = notifications_pg.results[-1] if len(notifications_pg.results) else None
        # assert the count
        assert notifications_pg.count == notifications_expected
        assert notification_pg is not None
        notification_pg.wait_until_completed().assert_successful()
        # assert the sent message template
        if nt_type == 'slack':
            assert str(notification_template.notification_configuration.channels) == notification_pg.recipients
        else:
            assert notification_template.notification_configuration.url == notification_pg.recipients
        tower_msg = expected_job_notification(tower_baseurl, notification_template, wf_job, approval_node, wf_approval, status, tower_message=True)
        if nt_type == 'slack':
            assert notification_pg.subject == tower_msg
        else:
            assert notification_pg.body == tower_msg
        # Confirm that notification is received when approval node is approved
        if can_confirm_notification(notification_template):
            msg = expected_job_notification(tower_baseurl, notification_template, wf_job, approval_node, wf_approval, status)
            assert confirm_notification(notification_template, msg)
        # disable notification for approvals
        payload = dict(id=notification_template.id)
        payload['disassociate'] = True
        with suppress(exc.NoContent):
            getattr(workflow_job_template.related, "notification_templates_approvals").post(payload)
        # launch the job
        wf_job = workflow_job_template.launch()
        wf_job.wait_until_status('running')
        approval_jt = approval_node.related.unified_job_template.get()
        approval_job_node = wf_job.related.workflow_nodes.get(unified_job_template=approval_jt.id).results.pop()
        wf_approval = approval_job_node.wait_for_job().related.job.get().wait_until_status('pending')
        wf_approval.approve()
        wf_job.wait_until_completed().assert_successful()
        # assert that notification is not received for the disabled events
        assert wf_job.get_related('notifications').count == 0

    def test_notifications_multiple_approval_nodes_wf_level(self, factories, workflow_job_template, slack_notification_template, tower_baseurl):
        """Test that notifications are received for all approval nodes if enabled at workflow level"""
        # enable notifications
        notification_template = slack_notification_template
        associate_notification_template(notification_template, workflow_job_template, 'started')
        associate_notification_template(notification_template, workflow_job_template, 'success')
        associate_notification_template(notification_template, workflow_job_template, 'error')
        associate_notification_template(notification_template, workflow_job_template, 'approvals')
        approval_node_approve = factories.workflow_job_template_node(
            workflow_job_template=workflow_job_template,
            unified_job_template=None
            ).make_approval_node()
        approval_node_deny = factories.workflow_job_template_node(
            workflow_job_template=workflow_job_template,
            unified_job_template=None
            ).make_approval_node()
        approval_node_timeout = factories.workflow_job_template_node(
            workflow_job_template=workflow_job_template,
            unified_job_template=None
            ).make_approval_node(timeout=1)
        approval_node_approve2 = factories.workflow_job_template_node(
            workflow_job_template=workflow_job_template,
            unified_job_template=None
            ).make_approval_node()
        with pytest.raises(exc.NoContent):
            approval_node_deny.related.always_nodes.post(dict(id=approval_node_approve2.id))
        with pytest.raises(exc.NoContent):
            approval_node_timeout.related.always_nodes.post(dict(id=approval_node_approve2.id))
        # launch the job and approve/ deny/ let the nodes time out
        wf_job = workflow_job_template.launch()
        wf_job.wait_until_status('running')
        approval_jt_approve = approval_node_approve.related.unified_job_template.get()
        approval_job_node_approve = wf_job.related.workflow_nodes.get(unified_job_template=approval_jt_approve.id).results.pop()
        wf_approval_approve = approval_job_node_approve.wait_for_job().related.job.get().wait_until_status('pending')
        wf_approval_approve.approve()
        status_approval_node_approve = 'was approved'
        approval_jt_deny = approval_node_deny.related.unified_job_template.get()
        approval_job_node_deny = wf_job.related.workflow_nodes.get(unified_job_template=approval_jt_deny.id).results.pop()
        wf_approval_deny = approval_job_node_deny.wait_for_job().related.job.get().wait_until_status('pending')
        wf_approval_deny.deny()
        status_approval_node_deny = 'was denied'
        approval_jt_timeout = approval_node_timeout.related.unified_job_template.get()
        approval_job_node_timeout = wf_job.related.workflow_nodes.get(unified_job_template=approval_jt_timeout.id).results.pop()
        wf_approval_timeout = approval_job_node_timeout.wait_for_job().related.job.get()
        status_approval_node_timeout = 'has timed out'
        approval_jt_approve2 = approval_node_approve2.related.unified_job_template.get()
        approval_job_node_approve2 = wf_job.related.workflow_nodes.get(unified_job_template=approval_jt_approve2.id).results.pop()
        wf_approval_approve2 = approval_job_node_approve2.wait_for_job().related.job.get().wait_until_status('pending')
        wf_approval_approve2.approve()
        status_approval_node_approve2 = 'was approved'
        wf_job.wait_until_completed().assert_successful()
        # assert the count
        notifications_expected = 10
        notifications_pg = wf_job.get_related('notifications').wait_until_count(notifications_expected)
        assert notifications_pg.count == notifications_expected
        # assert that notifications are received for all events including needs approval, approved, denied, timed out
        if can_confirm_notification(slack_notification_template):
            for approval_node, status_approval_node, wf_approval in \
                    [(approval_node_approve, status_approval_node_approve, wf_approval_approve),
                     (approval_node_deny, status_approval_node_deny, wf_approval_deny),
                     (approval_node_timeout, status_approval_node_timeout, wf_approval_timeout),
                     (approval_node_approve2, status_approval_node_approve2, wf_approval_approve2)]:
                msg = expected_job_notification(tower_baseurl, slack_notification_template, wf_job, approval_node, wf_approval, 'needs review')
                assert confirm_notification(slack_notification_template, msg)
                msg = expected_job_notification(tower_baseurl, slack_notification_template, wf_job, approval_node, wf_approval, status_approval_node)
                assert confirm_notification(slack_notification_template, msg)

    def test_notifications_multiple_approval_nodes_org_level(self, factories, slack_notification_template, tower_baseurl):
        """Test that notifications are received for all approval nodes for all workflows if enabled at organization level"""
        notification_template = slack_notification_template
        org = factories.organization()
        wfjt1 = factories.workflow_job_template(organization=org)
        wfjt2 = factories.workflow_job_template(organization=org)
        # enable notifications
        associate_notification_template(notification_template, org, 'approvals')
        approval_node_deny = factories.workflow_job_template_node(
            workflow_job_template=wfjt1,
            unified_job_template=None
            ).make_approval_node()
        approval_node_approve = factories.workflow_job_template_node(
            workflow_job_template=wfjt1,
            unified_job_template=None
            ).make_approval_node()
        approval_node_time_out = factories.workflow_job_template_node(
            workflow_job_template=wfjt2,
            unified_job_template=None
            ).make_approval_node(timeout=1)
        with pytest.raises(exc.NoContent):
            approval_node_deny.related.always_nodes.post(dict(id=approval_node_approve.id))
        wf_job = wfjt1.launch()
        wf_job.wait_until_status('running')
        approval_jt_deny = approval_node_deny.related.unified_job_template.get()
        approval_job_node_deny = wf_job.related.workflow_nodes.get(unified_job_template=approval_jt_deny.id).results.pop()
        wf_approval_deny = approval_job_node_deny.wait_for_job().related.job.get().wait_until_status('pending')
        wf_approval_deny.deny()
        status_approval_node_deny = 'was denied'
        approval_jt_approve = approval_node_approve.related.unified_job_template.get()
        approval_job_node_approve = wf_job.related.workflow_nodes.get(unified_job_template=approval_jt_approve.id).results.pop()
        wf_approval_approve = approval_job_node_approve.wait_for_job().related.job.get().wait_until_status('pending')
        wf_approval_approve.approve()
        status_approval_node_approve = 'was approved'
        status_approval_node_time_out = 'has timed out'
        wf_job.wait_until_completed().assert_successful()
        wf_job2 = wfjt2.launch()
        approval_jt_time_out = approval_node_time_out.related.unified_job_template.get()
        approval_job_node_time_out = wf_job2.related.workflow_nodes.get(unified_job_template=approval_jt_time_out.id).results.pop()
        wf_approval_time_out = approval_job_node_time_out.wait_for_job().related.job.get()
        wf_job2.wait_until_completed().assert_status('failed')
        # assert the count for both WFJTs
        notifications_expected = 4
        notifications_pg = wf_job.get_related('notifications').wait_until_count(notifications_expected)
        assert notifications_pg.count == notifications_expected
        notifications_expected = 2
        notifications_pg = wf_job2.get_related('notifications').wait_until_count(notifications_expected)
        assert notifications_pg.count == notifications_expected
        # assert that notifications are received for all events including needs approval, approved, denied, timed out
        for job, approval_node, status_approval_node, wf_approval in \
                [(wf_job, approval_node_deny, status_approval_node_deny, wf_approval_deny),
                 (wf_job, approval_node_approve, status_approval_node_approve, wf_approval_approve),
                 (wf_job2, approval_node_time_out, status_approval_node_time_out, wf_approval_time_out)]:
            msg = expected_job_notification(tower_baseurl, slack_notification_template, job, approval_node, wf_approval, 'needs review')
            assert confirm_notification(slack_notification_template, msg)
            msg = expected_job_notification(tower_baseurl, slack_notification_template, job, approval_node, wf_approval, status_approval_node)
            assert confirm_notification(slack_notification_template, msg)

    @pytest.fixture(scope="class")
    def slack_notification_template_with_org(self, class_factories):
        """Slack notification template"""
        org = class_factories.organization()
        nt = class_factories.notification_template(notification_type="slack", organization=org)
        return nt, org

    @pytest.mark.parametrize("user_role",
                             ["sys_admin", 'org_admin', 'wfjt_admin', 'system_auditor', 'org_auditor', 'org_executor', 'org_not_admin', 'org_member'])
    def test_associate_notification_template_rbac(self, factories,
                                      slack_notification_template_with_org, user_role):
        """Test RBAC for Viewing, Creating and Associating notification template to the workflow"""
        # pytest.skip("figuring out")
        nt, org = slack_notification_template_with_org
        wfjt = factories.workflow_job_template(organization=org)
        user = factories.user(organization=org)
        # Create User with appropriate permissions
        if user_role == 'sys_admin':
            user.is_superuser = True
        if user_role == 'system_auditor':
            user.is_system_auditor = True
        if user_role == 'org_admin':
            org.set_object_roles(user, 'admin')
        if user_role == 'org_executor':
            org.set_object_roles(user, 'execute')
        if user_role == 'org_not_admin':
            org.set_object_roles(user, 'notification admin')
        if user_role == 'org_auditor':
            org.set_object_roles(user, 'auditor')
        if user_role == 'wfjt_admin':
            wfjt.set_object_roles(user, 'admin')
        if user_role == 'org_member':
            org.set_object_roles(user, 'member')
        with self.current_user(user.username, user.password):
            if user_role in ['sys_admin', 'org_admin']:
                # Assert that valid users can create a notification template
                factories.notification_template(organization=org)
                # Assert that valid users can get a notification template
                nt.get()
                # Assert that valid users can associate the notification template to the workflow
                associate_notification_template(nt, wfjt, 'approvals')

            elif user_role in ['system_auditor', 'org_auditor']:
                # Assert that invalid users can not create a notification template
                with pytest.raises(exc.Forbidden):
                    factories.notification_template(organization=org)
                # Assert that the notification admin can get a notification template
                nt.get()
                # Assert that invalid users can not associate the notification template to the workflow
                with pytest.raises(exc.Forbidden):
                    associate_notification_template(nt, wfjt, 'approvals')

            elif user_role in ['org_not_admin']:
                # Assert that the notification admin can create a notification template
                factories.notification_template(organization=org)
                # Assert that the notification admin can get a notification template
                nt.get()
                # Assert that the notification admin can not associate the notification template to the workflow
                with pytest.raises(exc.Forbidden):
                    associate_notification_template(nt, wfjt, 'approvals')

            elif user_role in['wfjt_admin', 'org_executor', 'org_member']:
                # Assert that invalid users can not create a notification template
                with pytest.raises(exc.Forbidden):
                    factories.notification_template(organization=org)
                # Assert that invalid users can not get a notification template
                with pytest.raises(exc.Forbidden):
                    nt.get()
                # Assert that invalid users can not associate the notification template to the workflow
                with pytest.raises(exc.Forbidden):
                    associate_notification_template(nt, wfjt, 'approvals')
