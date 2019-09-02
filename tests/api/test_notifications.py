import logging
from urllib.parse import urlparse

from tests.lib.notification_services import (confirm_notification, can_confirm_notification)
from awxkit.config import config
import awxkit.exceptions as exc
import pytest

from tests.api import APITest


log = logging.getLogger(__name__)


def associate_notification_template(notification_template_pg, resource_pg, event='success'):
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
    assert updated_nt_count == nt_count + 1, \
        ("Expected %s notification templates associated with resource, found %s.") % \
        (nt_count + 1, updated_nt_count)

    # Confirm n.t. associated with resource
    latest_nt = notification_templates.results[0]
    assert latest_nt.id == nt_id, \
        "Failed to associate notification template (%s) with tower resource" % \
        nt_id


def expected_test_notification(tower_url, notification_template_pg, tower_message=False):
    """Returns test notification message expected for given notification template.
    By default, returns message as it would be shown in notification service
    (if tower_message is True, returns message shown on notifications endpoint).
    """
    nt_id = notification_template_pg.id
    nt_type = notification_template_pg.notification_type

    if tower_message:
        msg = "Tower Notification Test %s %s" % (nt_id, tower_url)
    elif nt_type == "slack":
        msg = "Tower Notification Test %s <%s>" % (nt_id, tower_url)
    elif nt_type == "webhook":
        headers = notification_template_pg.notification_configuration['headers']
        body = {"body": "Ansible Tower Test Notification %s %s" % (nt_id, tower_url)}
        msg = (headers, body)
    else:
        raise Exception("notification type %s not supported" % nt_type)
    return msg


def expected_job_notification(tower_url, notification_template_pg, job_pg, job_result, tower_message=False):
    """Returns notification message expected for given job and state.
    Note that job can be regular job template or system job template.
    By default, returns message as it would be shown in notification service
    (if tower_message is True, returns message shown on notifications endpoint).
    """
    nt_type = notification_template_pg.notification_type
    job_description = ("System " if job_pg.type == 'system_job' else "") + "Job"
    if tower_message:
        msg = (job_description + " #%s '%s' succeeded: %s/#/jobs/" +
               ("system" if job_pg.type == "system_job" else "playbook") + "/%s") % \
              (job_pg.id, job_pg.name, tower_url, job_pg.id)

    elif nt_type == "slack":
        msg = (job_description + " #%s '%s' succeeded: <%s/#/jobs/" +
               ("system" if job_pg.type == "system_job" else "playbook") + "/%s>") % \
              (job_pg.id, job_pg.name, tower_url, job_pg.id)
    elif nt_type == "webhook":
        headers = notification_template_pg.notification_configuration['headers']
        body = _expected_webhook_job_notification(tower_url, notification_template_pg, job_pg, job_result)
        msg = (headers, body)
    else:
        raise Exception("notification type %s not supported" % nt_type)
    return msg


def _expected_webhook_job_notification(tower_url, notification_template_pg, job_pg, job_result):
    """Returns job notification message for webhooks.
    Note that job can be regular job template or system job template.
    """
    # Get job_host_summaries_pg (used in build_host_results())
    if job_pg.type == 'job':
        job_host_summaries_pg = job_pg.get_related('job_host_summaries')

    def get_friendly_name():
        """Returns friendly name based on type"""
        if job_pg.type == 'job':
            return 'Job'
        elif job_pg.type == 'system_job':
            return 'System Job'
        msg = "Cannot generate notification for Jobs when job type is not 'job'"
        raise Exception(msg)

    def build_host_results():
        """Returns mapping of host to host results"""
        host_results = dict()
        host_stats = ['skipped', 'ok', 'changed', 'dark', 'failed', 'processed', 'failures']

        for host_summary_pg in job_host_summaries_pg.results:
            host_name = host_summary_pg.host_name
            host_results[host_name] = \
                dict((stat, getattr(host_summary_pg, stat)) for stat in host_stats)
        return host_results

    url = tower_url + '/#/' + ('management_' if job_pg.type == 'system_job' else '') + 'jobs/' + str(job_pg.id)

    # All supported job types have these fields
    job_msg = {'status': job_pg.status,
               'name': job_pg.name,
               'started': job_pg.started,
               'traceback': job_pg.result_traceback,
               'friendly_name': get_friendly_name(),
               'created_by': job_pg.summary_fields['created_by']['username'],
               'url': url,
               'finished': job_pg.finished,
               'id': job_pg.id}
    # Regular jobs have these fields, too
    if job_pg.type == 'job':
        job_msg.update({'credential': job_pg.get_related('credential').name,
                        'extra_vars': job_pg.extra_vars,
                        'project': job_pg.summary_fields['project']['name'],
                        'hosts': build_host_results(),
                        'playbook': job_pg.playbook,
                        'limit': job_pg.limit,
                        'inventory': job_pg.summary_fields['inventory']['name']})
    return job_msg


@pytest.mark.usefixtures('authtoken')
class Test_Notification_Templates(APITest):

    def test_duplicate_notification_templates_disallowed_by_organization(self, factories):
        nt_a = factories.notification_template(name='SharedName')
        factories.notification_template(name='SharedName')

        shared_org = nt_a.ds.organization
        with pytest.raises(exc.Duplicate) as e:
            factories.notification_template(name='SharedName', organization=shared_org)
        assert e.value.msg['__all__'] == ['Notification template with this Organization and Name already exists.']


@pytest.mark.usefixtures('authtoken')
class Test_Notifications(APITest):
    """Notification tests"""

    @pytest.fixture(scope='class')
    def tower_baseurl(self, is_docker):
        base_url = urlparse(config.base_url)
        scheme = 'http' if base_url.scheme is None else base_url.scheme
        return '{0}://{1}'.format(scheme, base_url.hostname)

    def test_test_notification(self, request, notification_template, tower_baseurl):
        """Generate test notifications for each notification type"""
        # Trigger test notification
        notification_pg = notification_template.test().wait_until_completed(timeout=30)
        notification_pg.assert_successful()

        # Confirm test notification delivered
        if can_confirm_notification(notification_template):
            msg = expected_test_notification(tower_baseurl, notification_template)
            notification_type = notification_template.notification_type
            assert confirm_notification(notification_template, msg), \
                "Failed to find %s test notification (%s)" %\
                (notification_type, msg)

    @pytest.mark.parametrize(
        "notify_on_start,job_result",
        [(True, 'success'), (True, 'error'), (False, 'success'), (False, 'error')]
    )
    def test_system_job_notifications(self, system_job_template, slack_notification_template,
                                      notify_on_start, job_result, tower_baseurl):
        """Test notification templates attached to system job templates"""

        notification_template = slack_notification_template
        notifications_expected = \
            system_job_template.get_related('notification_templates_success').count + \
            system_job_template.get_related('notification_templates_error').count + \
            system_job_template.get_related('notification_templates_started').count

        if notify_on_start:
            notifications_expected += 1

        if job_result == 'success':
            notifications_expected += 1

        if notify_on_start:
            associate_notification_template(notification_template, system_job_template, 'started')
        associate_notification_template(notification_template, system_job_template, job_result)

        job = system_job_template.launch().wait_until_completed()
        job.assert_successful()

        # Find the notification that matches the expected template
        notifications_pg = job.get_related('notifications').wait_until_count(notifications_expected)
        notification_pg = notifications_pg.results[-1] if len(notifications_pg.results) else None

        assert notifications_pg.count == notifications_expected, \
            "Expected job to have %s notifications, found %s" % (notifications_expected, notifications_pg.count)
        if job_result == 'success':
            assert notification_pg is not None, \
                "Expected notification to be associated with notification template %s" % notification_template.id
            notification_pg.wait_until_completed()
            tower_msg = expected_job_notification(tower_baseurl, notification_template, job, job_result, tower_message=True)
            assert notification_pg.subject == tower_msg, \
                "Expected most recent notification to be (%s), found (%s)" % (tower_msg, notification_pg.subject)
            notification_pg.assert_successful()
            assert notification_pg.notifications_sent == 1, \
                "notification reports sending %s notifications (only one actually sent)" % notification_pg.notifications_sent
            assert notification_pg.notification_type == notification_template.notification_type
            # TODO: Test recipients field

        # Check notification in notification service
        if can_confirm_notification(notification_template):
            notification_expected = (True if job_result == 'success' else False)
            msg = expected_job_notification(tower_baseurl, notification_template, job, job_result)
            assert confirm_notification(notification_template, msg, is_present=notification_expected), \
                notification_template.notification_type + " notification " + \
                ("not " if notification_expected else "") + "present (%s)" % msg

    @pytest.mark.parametrize(
        "notify_on_start,job_result",
        [(True, 'success'), (True, 'error'), (False, 'success'), (False, 'error')]
    )
    @pytest.mark.parametrize("resource", ['organization', 'project', 'job_template'])
    def test_notification_inheritance(self, request, resource, job_template, slack_notification_template, notify_on_start, job_result, tower_baseurl):
        """Test inheritance of notifications when notification template attached to various tower resources"""
        # Get reference to resource
        notification_template = slack_notification_template
        if resource == "organization":
            resource = job_template.get_related('project').get_related('organization')
        elif resource == "project":
            resource = job_template.get_related('project')
        elif resource == "job_template":
            resource = job_template
        else:
            pytest.fail("Test did not recognize resource: " + resource)

        if notify_on_start:
            associate_notification_template(notification_template, resource, 'started')
        associate_notification_template(notification_template, resource, job_result)

        job = job_template.launch().wait_until_completed(timeout=60 * 4)
        job.assert_successful()

        notifications_expected = 0
        if notify_on_start:
            notifications_expected += 1

        if job_result == 'success':
            notifications_expected += 1

        notifications_pg = job.get_related('notifications').wait_until_count(notifications_expected)
        assert notifications_pg.count == notifications_expected, \
            "Expected job to have %s notifications, found %s" % (notifications_expected, notifications_pg.count)
        if job_result == 'success':
            notification_pg = notifications_pg.results[-1] if len(notifications_pg.results) else None
            tower_msg = expected_job_notification(tower_baseurl, notification_template, job, job_result, tower_message=True)
            assert notification_pg.notification_template == notification_template.id, \
                "Expected notification to be associated with notification template %s, found %s" % \
                (notification_template.id, notification_pg.notification_template)
            assert notification_pg.subject == tower_msg, \
                "Expected most recent notification to be (%s), found (%s)" % (tower_msg, notification_pg.subject)
            notification_pg.assert_successful()
            assert notification_pg.notifications_sent == 1, \
                "notification reports sending %s notifications (only one actually sent)" % notification_pg.notifications_sent
            assert notification_pg.notification_type == notification_template.notification_type
            # TODO: Test recipients field

        # Check notification in notification service
        if can_confirm_notification(notification_template):
            notification_expected = (True if job_result == 'success' else False)
            msg = expected_job_notification(tower_baseurl, notification_template, job, job_result)
            assert confirm_notification(notification_template, msg) == notification_expected, \
                notification_template.notification_type + " notification " + \
                ("not " if notification_expected else "") + "present (%s)" % msg
