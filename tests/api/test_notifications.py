from itertools import ifilter
import logging

from towerkit.notification_services import (confirm_notification, can_confirm_notification)
from towerkit.config import config
import towerkit.exceptions as exc
import pytest

from tests.api import APITest


log = logging.getLogger(__name__)


def associate_notification_template(notification_template_pg, resource_pg, job_result="any"):
    """Associate notification template to tower resource"""
    nt_id = notification_template_pg.id
    resource_nt_pg = resource_pg.get_related('notification_templates_' + job_result)
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

    if tower_message or nt_type == "hipchat":
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

    if tower_message or nt_type == "hipchat":
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


@pytest.mark.api
@pytest.mark.usefixtures('authtoken', 'install_enterprise_license_unlimited')
class Test_Notification_Templates(APITest):

    def test_duplicate_notification_templates_disallowed_by_organization(self, factories):
        nt_a = factories.v2_notification_template(name='SharedName')
        factories.v2_notification_template(name='SharedName')

        shared_org = nt_a.ds.organization
        with pytest.raises(exc.BadRequest) as e:
            factories.v2_notification_template(name='SharedName', organization=shared_org)
        assert e.value.message['__all__'] == ['Notification template with this Organization and Name already exists.']


@pytest.mark.api
@pytest.mark.destructive
@pytest.mark.usefixtures('authtoken', 'install_enterprise_license_unlimited')
class Test_Notifications(APITest):
    """Notification tests"""

    @pytest.mark.github('https://github.com/ansible/tower-qa/issues/2294')
    def test_test_notification(self, request, notification_template):
        """Generate test notifications for each notification type"""
        # Trigger test notification
        notification_pg = notification_template.test().wait_until_completed()
        assert notification_pg.is_successful, "Notification was unsuccessful - %s" %\
            notification_pg

        # Confirm test notification delivered
        if can_confirm_notification(notification_template):
            msg = expected_test_notification(config.base_url, notification_template)
            notification_type = notification_template.notification_type
            assert confirm_notification(notification_template, msg), \
                "Failed to find %s test notification (%s)" %\
                (notification_type, msg)

    @pytest.mark.mp_group('SystemJobNotifications', 'serial')
    @pytest.mark.parametrize("job_result", ['any', 'error', 'success'])
    def test_system_job_notifications(self, request, system_job_template, hipchat_notification_template, job_result):
        """Test notification templates attached to system job templates"""
        notification_template = hipchat_notification_template
        existing_notifications = system_job_template.get_related('notification_templates_any').count + \
            system_job_template.get_related('notification_templates_success').count
        notifications_expected = existing_notifications + (1 if job_result in ('any', 'success') else 0)

        # Associate notification template
        associate_notification_template(notification_template, system_job_template, job_result)

        # Launch job
        job = system_job_template.launch().wait_until_completed()
        assert job.is_successful, "Job unsuccessful - %s" % job

        # Find the notification that matches the expected template
        notifications_pg = job.get_related('notifications').wait_until_count(notifications_expected)
        notification_pg = next(
            ifilter(lambda x: x.notification_template == notification_template.id, notifications_pg.results),
            None
        )

        assert notifications_pg.count == notifications_expected, \
            "Expected job to have %s notifications, found %s" % (notifications_expected, notifications_pg.count)
        if job_result in ('any', 'success'):
            assert notification_pg is not None, \
                "Expected notification to be associated with notification template %s" % notification_template.id
            notification_pg.wait_until_completed()
            tower_msg = expected_job_notification(config.base_url, notification_template, job, job_result, tower_message=True)
            assert notification_pg.subject == tower_msg, \
                "Expected most recent notification to be (%s), found (%s)" % (tower_msg, notification_pg.subject)
            assert notification_pg.is_successful, "Notification was unsuccessful - %s" % notification_pg
            assert notification_pg.notifications_sent == 1, \
                "notification reports sending %s notifications (only one actually sent)" % notification_pg.notifications_sent
            assert notification_pg.notification_type == notification_template.notification_type
            # TODO: Test recipients field

        # Check notification in notification service
        if can_confirm_notification(notification_template):
            notification_expected = (True if job_result in ('any', 'success') else False)
            msg = expected_job_notification(config.base_url, notification_template, job, job_result)
            assert confirm_notification(notification_template, msg, is_present=notification_expected), \
                notification_template.notification_type + " notification " + \
                ("not " if notification_expected else "") + "present (%s)" % msg

    @pytest.mark.parametrize("job_result", ['any', 'error', 'success'])
    @pytest.mark.parametrize("resource", ['organization', 'project', 'job_template'])
    def test_notification_inheritance(self, request, resource, job_template, hipchat_notification_template, job_result):
        """Test inheritance of notifications when notification template attached to various tower resources"""
        # Get reference to resource
        notification_template = hipchat_notification_template
        if resource == "organization":
            resource = job_template.get_related('project').get_related('organization')
        elif resource == "project":
            resource = job_template.get_related('project')
        elif resource == "job_template":
            resource = job_template
        else:
            pytest.fail("Test did not recognize resource: " + resource)

        # Associate notification template
        associate_notification_template(notification_template, resource, job_result)

        # Launch job
        job = job_template.launch().wait_until_completed(timeout=60 * 4)
        assert job.is_successful, "Job unsuccessful - %s" % job

        # Check notification in job
        notifications_expected = 1 if job_result in ('any', 'success') else 0
        notifications_pg = job.get_related('notifications').wait_until_count(notifications_expected)
        assert notifications_pg.count == notifications_expected, \
            "Expected job to have %s notifications, found %s" % (notifications_expected, notifications_pg.count)
        if job_result in ('any', 'success'):
            notification_pg = notifications_pg.results[0].wait_until_completed()
            tower_msg = expected_job_notification(config.base_url, notification_template, job, job_result, tower_message=True)
            assert notification_pg.notification_template == notification_template.id, \
                "Expected notification to be associated with notification template %s, found %s" % \
                (notification_template.id, notification_pg.notification_template)
            assert notification_pg.subject == tower_msg, \
                "Expected most recent notification to be (%s), found (%s)" % (tower_msg, notification_pg.subject)
            assert notification_pg.is_successful, "Notification was unsuccessful - %s" % notification_pg
            assert notification_pg.notifications_sent == 1, \
                "notification reports sending %s notifications (only one actually sent)" % notification_pg.notifications_sent
            assert notification_pg.notification_type == notification_template.notification_type
            # TODO: Test recipients field

        # Check notification in notification service
        if can_confirm_notification(notification_template):
            notification_expected = (True if job_result == 'any' or job_result == 'success' else False)
            msg = expected_job_notification(config.base_url, notification_template, job, job_result)
            assert confirm_notification(notification_template, msg) == notification_expected, \
                notification_template.notification_type + " notification " + \
                ("not " if notification_expected else "") + "present (%s)" % msg
