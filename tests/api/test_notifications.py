import json

import pytest
import logging
import common.exceptions

from tests.api import Base_Api_Test

from common.notification_services import (confirm_notification, can_confirm_notification)

log = logging.getLogger(__name__)


def associate_notification_template(notification_template_pg, resource_pg, job_result="any"):
    '''Associate notification template to tower resource'''
    nt_id = notification_template_pg.id
    resource_nt_pg = resource_pg.get_related('notification_templates_' + job_result)
    nt_count = resource_nt_pg.get().count

    # Associate notification template
    with pytest.raises(common.exceptions.NoContent_Exception):
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
    '''
    Returns test notification message expected for given notification template.
    By default, returns message as it would be shown in notification service
    (if tower_message is True, returns message shown on notifications endpoint).
    '''
    nt_id = notification_template_pg.id
    nt_type = notification_template_pg.notification_type

    if tower_message or nt_type == "hipchat":
        msg = "Tower Notification Test %s %s" % (nt_id, tower_url)
    elif nt_type == "slack":
        msg = "Tower Notification Test %s <%s>" % (nt_id, tower_url)
    elif nt_type == "webhook":
        msg = {"body": "Ansible Tower Test Notification %s %s" % (nt_id, tower_url)}
    else:
        raise Exception("notification type %s not supported" % nt_type)
    return msg


def expected_job_notification(tower_url, notification_template_pg, job_pg, job_result, tower_message=False):
    '''
    Returns notification message expected for given job and state.
    Note that job can be regular job template or system job template.
    By default, returns message as it would be shown in notification service
    (if tower_message is True, returns message shown on notifications endpoint).
    '''
    nt_type = notification_template_pg.notification_type
    job_description = ("System " if job_pg.type == 'system_job' else "") + "Job"

    if tower_message or nt_type == "hipchat":
        msg = (job_description + " #%s '%s' succeeded on Ansible Tower: %s/#/" +
               ("management_" if job_pg.type == 'system_job' else "") + "jobs/%s") % \
              (job_pg.id, job_pg.name, tower_url, job_pg.id)
    elif nt_type == "slack":
        msg = (job_description + " #%s '%s' succeeded on Ansible Tower: <%s/#/" +
               ("management_" if job_pg.type == 'system_job' else "") + "jobs/%s>") % \
              (job_pg.id, job_pg.name, tower_url, job_pg.id)
    elif nt_type == "webhook":
        msg = _expected_webhook_job_notification(tower_url, notification_template_pg, job_pg, job_result)
    else:
        raise Exception("notification type %s not supported" % nt_type)
    return msg


def _expected_webhook_job_notification(tower_url, notification_template_pg, job_pg, job_result):
    '''
    Returns job notification message for webhooks.
    Note that job can be regular job template or system job template.
    '''
    # Get job_host_summaries_pg (used in build_host_results())
    if job_pg.type == 'job':
        job_host_summaries_pg = job_pg.get_related('job_host_summaries')

    def get_friendly_name():
        '''Returns friendly name based on type'''
        if job_pg.type == 'job':
            return 'Job'
        elif job_pg.type == 'system_job':
            return 'System Job'
        msg = "Cannot generate notification for Jobs when job type is not 'job'"
        raise Exception(msg)

    def build_host_results():
        '''Returns mapping of host to host results'''
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
@pytest.mark.skip_selenium
class Test_Notifications(Base_Api_Test):
    '''Notification tests'''

    pytestmark = pytest.mark.usefixtures('authtoken', 'install_enterprise_license')

    @pytest.mark.destructive
    def test_test_notification(self, request, testsetup, notification_template):
        '''Generate test notifications for each notification type'''
        # Trigger test notification
        notification_pg = notification_template.test().wait_until_completed()
        assert notification_pg.is_successful, "Notification was unsuccessful - %s" %\
            notification_pg

        # Confirm test notification delivered
        if can_confirm_notification(notification_template):
            msg = expected_test_notification(testsetup.base_url, notification_template)
            notification_type = notification_template.notification_type
            assert confirm_notification(testsetup, notification_template, msg), \
                "Failed to find %s test notification (%s)" %\
                (notification_type, msg)

    @pytest.mark.destructive
    @pytest.mark.parametrize("job_result", ['any', 'error', 'success'])
    def test_system_job_notifications(self, request, system_job_template, notification_template, job_result,
                                      testsetup):
        '''Test notification templates attached to system job templates'''
        # Associate notification template
        associate_notification_template(notification_template, system_job_template, job_result)

        # Launch job
        job = system_job_template.launch().wait_until_completed()
        assert job.is_successful, "Job unsuccessful - %s" % job

        # Check notification in job
        notifications_pg = job.get_related('notifications')
        if job_result in ('any', 'success'):
            assert notifications_pg.count == 1, \
                "Expected job to have 1 notification, found %s" % notifications_pg.count
            notification_pg = notifications_pg.results[0].wait_until_completed()
            tower_msg = expected_job_notification(testsetup.base_url, notification_template, job, job_result, tower_message=True)
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
        else:
            assert notifications_pg.count == 0, \
                "Expected job to have 0 notifications, found %s" % notifications_pg.count

        # Check notification in notification service
        if can_confirm_notification(notification_template):
            notification_expected = (True if job_result in ('any', 'success') else False)
            msg = expected_job_notification(testsetup.base_url, notification_template, job, job_result)
            assert confirm_notification(testsetup, notification_template, msg) == notification_expected, \
                notification_template.notification_type + " notification " + \
                ("not " if notification_expected else "") + "present (%s)" % msg

    @pytest.mark.destructive
    @pytest.mark.parametrize("job_result", ['any', 'error', 'success'])
    @pytest.mark.parametrize("resource", ['organization', 'project', 'job_template'])
    def test_notification_inheritance(self, request, resource, job_template, notification_template, job_result,
                                      testsetup, api_notifications_pg):
        '''Test inheritance of notifications when notification template attached to various tower resources'''
        # Get initial state
        notifications_count = api_notifications_pg.get().count

        # Get reference to resource
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

        # Check notification in notification stream
        notifications = api_notifications_pg.get(order_by="-id")
        notifications_count_updated = notifications.count
        if job_result in ('any', 'success'):
            assert notifications_count_updated == notifications_count + 1, \
                "Expected %s notifications, found %s" % \
                (notifications_count + 1, notifications_count_updated)

            # Get notification
            last_notif = notifications.results[0].wait_until_completed()

            tower_msg = expected_job_notification(testsetup.base_url, notification_template, job, job_result, True)
            assert last_notif.is_successful, "Notification was unsuccessful - %s" % last_notif
            assert last_notif.subject == tower_msg, \
                "Expected most recent notification to be (%s), found (%s)" % (tower_msg, last_notif.subject)
            assert last_notif.notifications_sent == 1, \
                "notification reports sending %s notifications (only one actually sent)" % last_notif.notifications_sent
            assert last_notif.notification_type == notification_template.notification_type
            assert last_notif.notification_template == notification_template.id, \
                "Expected notification to be associated with notification template %s, found %s" % \
                (notification_template.id, last_notif.notification_template)
            # TODO: Test recipients field
        else:
            assert notifications_count_updated == notifications_count, \
                "Expected %s notifications, found %s" % \
                (notifications_count, notifications_count_updated)

        # Check notification in job
        job_notifications = job.get_related('notifications')
        if job_result == 'any' or job_result == 'success':
            assert job_notifications.count == 1, \
                "Expected job to have 1 notification, found %s" % job_notifications.count
            job_notification = job_notifications.results[0]
            assert job_notification.json == last_notif.json, \
                ("Notification on /notifications endpoint is:\n%s\n\n" +
                 "Notification on job's notification endpoint is:\n%s\n") \
                % (json.dumps(last_notif.json, indent=2), json.dumps(job_notification.json, indent=2))
        else:
            assert job_notifications.count == 0, \
                "Expected job to have 0 notifications, found %s" % job_notifications.count

        # Check notification in 'recent_notifications' (of notification template)
        assert 'recent_notifications' in notification_template.summary_fields, \
            "Could not find 'recent_notifications' in notification template summary fields"
        recent_notifications = notification_template.get().summary_fields['recent_notifications']
        matching_notifications = [notification for notification in recent_notifications if notification['id'] == last_notif.id]
        if job_result == 'any' or job_result == 'success':
            assert len(matching_notifications) == 1, \
                "Expected notification's recent_notifications to list notification once, found it listed %s time(s)." % \
                len(matching_notifications)
        else:
            assert len(matching_notifications) == 0, \
                "Expected notification's recent_notifications not list any notifications, found it listed %s time(s)." % \
                len(matching_notifications)

        # Check notification in notification service
        if can_confirm_notification(notification_template):
            notification_expected = (True if job_result == 'any' or job_result == 'success' else False)
            msg = expected_job_notification(testsetup.base_url, notification_template, job, job_result)
            assert confirm_notification(testsetup, notification_template, msg) == notification_expected, \
                notification_template.notification_type + " notification " + \
                ("not " if notification_expected else "") + "present (%s)" % msg
