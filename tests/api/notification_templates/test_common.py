#!/usr/bin/env python

import pytest
import awxkit.exceptions

from tests.api import APITest
from tests.api.test_notifications import associate_notification_template


@pytest.mark.usefixtures('authtoken')
class Test_Common_NotificationTemplate(APITest):

    def test_notification_template_contains_all_events_default_message(self, notification_template):
        assert 'messages' in notification_template

        messages = notification_template['messages']
        assert sorted(['started', 'success', 'error']) == sorted(list(messages.keys()))

        default_message = {
            'message': "{{ job_friendly_name }} #{{ job.id }} '{{ job.name }}' {{ job.status }}: {{ url }}",
            'body': "",
        }

        for event in ['started', 'success', 'error']:
            assert messages[event] == default_message

    def test_notification_template_contains_update_default_messages(self, notification_template):

        notification_configuration_event = {
            'started': {
                'message': 'message_started',
                'body': 'body_started'
            },
            'error': {
                'message': 'message_error',
                'body': 'body_error'
            },
            'success': {
                'message': 'message_success',
                'body': 'body_success'
            }
        }
        notification_template.patch(messages=notification_configuration_event)
        for event in ['started', 'success', 'error']:
            assert notification_template['messages'][event] == \
                {'message': 'message_%s' % event, 'body': 'body_%s' % event}
        assert sorted(['started', 'success', 'error']) == sorted(list(notification_template['messages'].keys()))

        for event in ['started', 'success', 'error']:

            notification_configuration_event = {
                event: {
                    'message': 'message_%s' % event,
                    'body': 'body_%s' % event
                }
            }
            notification_template.patch(messages=notification_configuration_event)
            assert notification_template['messages'][event] == \
                {'message': 'message_%s' % event, 'body': 'body_%s' % event}
            assert sorted(['started', 'success', 'error']) == sorted(list(notification_template['messages'].keys()))

    def test_notification_template_fails_when_providing_invalid_payload(self, notification_template):
        notification_configuration_shouldfail = {
            'shouldfail': {
                'message': 'message_started',
                'body': 'body_started',
            }
        }
        with pytest.raises(awxkit.exceptions.BadRequest):
            notification_template.patch(messages=notification_configuration_shouldfail)

        notification_configuration_shouldfail = {
            'started': {
                'wrong': 'message_started',
                'wrongagain': 'body_started',
            }
        }
        with pytest.raises(awxkit.exceptions.BadRequest):
            notification_template.patch(messages=notification_configuration_shouldfail)

        notification_configuration_shouldfail = {
            'started': {
                'message': 'message_started',
                'body': 'body_started',
                'shouldfail': 'shouldfail_started'
            }
        }
        with pytest.raises(awxkit.exceptions.BadRequest):
            notification_template.patch(messages=notification_configuration_shouldfail)

    def test_job_template_launch_use_default_message_when_messages_is_missing(self, notification_template, factories):
        notification_configuration_event = {
            'error': {
                'message': 'message_error',
                'body': 'body_error'
            }
        }
        notification_template.patch(messages=notification_configuration_event)

        jt = factories.job_template()
        associate_notification_template(notification_template, jt, 'started')
        job = jt.launch().wait_until_completed()
        job.assert_successful()
        notifications = job.get_related('notifications').wait_until_count(1)
        assert "Job #%s '%s'" % (job.id, job.get_related('job_template').name) in notifications.results.pop()['subject']

    def test_job_template_launch_with_custom_notification_on_start_and_on_success(self, notification_template, factories):

        notification_configuration_event = {
            'started': {
                'message': 'message_started',
                'body': 'body_started'
            },
            'error': {
                'message': 'message_error',
                'body': 'body_error'
            },
            'success': {
                'message': 'message_success',
                'body': 'body_success'
            }
        }
        notification_template.patch(messages=notification_configuration_event)

        jt = factories.job_template()
        associate_notification_template(notification_template, jt, 'started')
        associate_notification_template(notification_template, jt, 'success')
        job = jt.launch().wait_until_completed()
        job.assert_successful()
        notifications = job.get_related('notifications').wait_until_count(2)
        assert 'message_started' in [notification['subject'] for notification in notifications.results]
        assert 'message_success' in [notification['subject'] for notification in notifications.results]

    def test_job_template_launch_with_custom_notification_on_start_and_on_error(self, notification_template, factories):

        notification_configuration_event = {
            'started': {
                'message': 'message_started',
                'body': 'body_started'
            },
            'error': {
                'message': 'message_error',
                'body': 'body_error'
            },
            'success': {
                'message': 'message_success',
                'body': 'body_success'
            }
        }
        notification_template.patch(messages=notification_configuration_event)

        jt = factories.job_template(playbook='fail.yml')
        associate_notification_template(notification_template, jt, 'started')
        associate_notification_template(notification_template, jt, 'error')
        job = jt.launch().wait_until_completed()
        notifications = job.get_related('notifications').wait_until_count(2)
        assert 'message_started' in [notification['subject'] for notification in notifications.results]
        assert 'message_error' in [notification['subject'] for notification in notifications.results]

    @pytest.mark.parametrize('event', ['started', 'success', 'error'])
    def test_job_template_launch_with_notification_on_event(self, notification_template, factories, event):

        playbook = 'ping.yml'
        if event == 'error':
            playbook = 'fail.yml'

        jt = factories.job_template(playbook=playbook)
        associate_notification_template(notification_template, jt, event)
        job = jt.launch().wait_until_completed()
        notifications = job.get_related('notifications').wait_until_count(1)
        assert "Job #%s '%s'" % (job.id, job.get_related('job_template').name) in notifications.results.pop()['subject']
