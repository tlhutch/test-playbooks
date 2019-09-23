import logging
from urllib.parse import urlparse
from awxkit.utils import suppress

from tests.lib.notification_services import (confirm_notification, can_confirm_notification)
from awxkit.config import config
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
        msg = 'The approval node "' + str(approval_node.summary_fields.unified_job_template.name) + status + str(tower_url) + '/#/workflows/' + str(job_pg.id)
    elif nt_type == "slack":
        if status == 'needs review':
            msg = 'The approval node "' + str(approval_node.summary_fields.unified_job_template.name) + '" needs review. This node can be viewed at: <' + str(
                    tower_url) + '/#/workflows/' + str(job_pg.id) + '>'
        else:
            msg = 'The approval node "' + str(approval_node.summary_fields.unified_job_template.name) + status + '<' + str(tower_url) + '/#/workflows/' + str(job_pg.id) + '>'
    elif nt_type == "webhook":
        if status == 'needs review':
            msg = 'The approval node "' + str(
                approval_node.summary_fields.unified_job_template.name) + '"  needs review. This node can be viewed at: ' + str(
                tower_url) + '/#/workflows/' + str(job_pg.id)
        else:
            msg = 'The approval node "' + str(approval_node.summary_fields.unified_job_template.name) + status + str(tower_url) + '/#/workflows/' + str(job_pg.id)
        headers = notification_template_pg.notification_configuration['headers']
        if wf_approval.finished is not None:
            finished = wf_approval.finished.replace('Z', '+00:00')
        else:
            finished = wf_approval.finished
        body = {'id': wf_approval.id,
                'name': approval_node.summary_fields.unified_job_template.name,
                'url': '',
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

    @pytest.fixture(scope='class')
    def tower_baseurl(self, is_docker):
        base_url = urlparse(config.base_url)
        scheme = 'http' if base_url.scheme is None else base_url.scheme
        return '{0}://{1}'.format(scheme, base_url.hostname)

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
        status = '" was approved. '
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
        # Scenario created: approval_node1 will be approved, node2 will be rejected, node3 will timeout, Verify messages for all
        approval_node1 = factories.workflow_job_template_node(
            workflow_job_template=workflow_job_template,
            unified_job_template=None
            ).make_approval_node()
        approval_node2 = factories.workflow_job_template_node(
            workflow_job_template=workflow_job_template,
            unified_job_template=None
            ).make_approval_node()
        approval_node3 = factories.workflow_job_template_node(
            workflow_job_template=workflow_job_template,
            unified_job_template=None
            ).make_approval_node(timeout=1)
        approval_node4 = factories.workflow_job_template_node(
            workflow_job_template=workflow_job_template,
            unified_job_template=None
            ).make_approval_node()
        with pytest.raises(exc.NoContent):
            approval_node2.related.always_nodes.post(dict(id=approval_node4.id))
        with pytest.raises(exc.NoContent):
            approval_node3.related.always_nodes.post(dict(id=approval_node4.id))
        # launch the job and approve/ deny/ let the nodes time out
        wf_job = workflow_job_template.launch()
        wf_job.wait_until_status('running')
        approval_jt1 = approval_node1.related.unified_job_template.get()
        approval_job_node1 = wf_job.related.workflow_nodes.get(unified_job_template=approval_jt1.id).results.pop()
        wf_approval1 = approval_job_node1.wait_for_job().related.job.get().wait_until_status('pending')
        wf_approval1.approve()
        status_approval_node1 = '" was approved. '
        approval_jt2 = approval_node2.related.unified_job_template.get()
        approval_job_node2 = wf_job.related.workflow_nodes.get(unified_job_template=approval_jt2.id).results.pop()
        wf_approval2 = approval_job_node2.wait_for_job().related.job.get().wait_until_status('pending')
        wf_approval2.deny()
        status_approval_node2 = '" was denied. '
        approval_jt3 = approval_node3.related.unified_job_template.get()
        approval_job_node3 = wf_job.related.workflow_nodes.get(unified_job_template=approval_jt3.id).results.pop()
        wf_approval3 = approval_job_node3.wait_for_job().related.job.get()
        status_approval_node3 = '" has timed out. '
        approval_jt4 = approval_node4.related.unified_job_template.get()
        approval_job_node4 = wf_job.related.workflow_nodes.get(unified_job_template=approval_jt4.id).results.pop()
        wf_approval4 = approval_job_node4.wait_for_job().related.job.get().wait_until_status('pending')
        wf_approval4.approve()
        status_approval_node4 = '" was approved. '
        wf_job.wait_until_completed().assert_successful()
        # assert the count
        notifications_expected = 10
        notifications_pg = wf_job.get_related('notifications').wait_until_count(notifications_expected)
        assert notifications_pg.count == notifications_expected
        # assert that notifications are received for all events including needs approval, approved, denied, timed out
        if can_confirm_notification(slack_notification_template):
            for approval_node, status_approval_node, wf_approval in [(approval_node1, status_approval_node1, wf_approval1), (approval_node2, status_approval_node2, wf_approval2), (approval_node3, status_approval_node3, wf_approval3), (approval_node4, status_approval_node4, wf_approval4)]:
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
        # Scenario created: approval_node1 will be approved, node2 will be rejected, node3 will timeout, Verify messages for all
        approval_node1 = factories.workflow_job_template_node(
            workflow_job_template=wfjt1,
            unified_job_template=None
            ).make_approval_node()
        approval_node2 = factories.workflow_job_template_node(
            workflow_job_template=wfjt1,
            unified_job_template=None
            ).make_approval_node()
        approval_node3 = factories.workflow_job_template_node(
            workflow_job_template=wfjt2,
            unified_job_template=None
            ).make_approval_node(timeout=1)
        with pytest.raises(exc.NoContent):
            approval_node1.related.always_nodes.post(dict(id=approval_node2.id))
        wf_job = wfjt1.launch()
        wf_job.wait_until_status('running')
        approval_jt1 = approval_node1.related.unified_job_template.get()
        approval_job_node1 = wf_job.related.workflow_nodes.get(unified_job_template=approval_jt1.id).results.pop()
        wf_approval1 = approval_job_node1.wait_for_job().related.job.get().wait_until_status('pending')
        wf_approval1.deny()
        status_approval_node1 = '" was denied. '
        approval_jt2 = approval_node2.related.unified_job_template.get()
        approval_job_node2 = wf_job.related.workflow_nodes.get(unified_job_template=approval_jt2.id).results.pop()
        wf_approval2 = approval_job_node2.wait_for_job().related.job.get().wait_until_status('pending')
        wf_approval2.approve()
        status_approval_node2 = '" was approved. '
        status_approval_node3 = '" has timed out. '
        wf_job.wait_until_completed().assert_successful()
        wf_job2 = wfjt2.launch()
        approval_jt3 = approval_node3.related.unified_job_template.get()
        approval_job_node3 = wf_job2.related.workflow_nodes.get(unified_job_template=approval_jt3.id).results.pop()
        wf_approval3 = approval_job_node3.wait_for_job().related.job.get()
        wf_job2.wait_until_completed().assert_status('failed')
        # assert the count for both WFJTs
        notifications_expected = 4
        notifications_pg = wf_job.get_related('notifications').wait_until_count(notifications_expected)
        assert notifications_pg.count == notifications_expected
        notifications_expected = 2
        notifications_pg = wf_job2.get_related('notifications').wait_until_count(notifications_expected)
        assert notifications_pg.count == notifications_expected
        # assert that notifications are received for all events including needs approval, approved, denied, timed out
        if can_confirm_notification(slack_notification_template):
            for job, approval_node, status_approval_node, wf_approval in [(wf_job, approval_node1, status_approval_node1, wf_approval1), (wf_job, approval_node2, status_approval_node2, wf_approval2), (wf_job2, approval_node3, status_approval_node3, wf_approval3)]:
                msg = expected_job_notification(tower_baseurl, slack_notification_template, job, approval_node, wf_approval, 'needs review')
                assert confirm_notification(slack_notification_template, msg)
                msg = expected_job_notification(tower_baseurl, slack_notification_template, job, approval_node, wf_approval, status_approval_node)
                assert confirm_notification(slack_notification_template, msg)
