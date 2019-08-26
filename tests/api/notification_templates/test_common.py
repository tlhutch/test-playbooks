#!/usr/bin/env python

from collections import namedtuple

import pytest
import awxkit.exceptions

from tests.api import APITest
from tests.api.test_notifications import associate_notification_template
from tests.lib.notification_services import confirm_notification, can_confirm_notification


@pytest.mark.usefixtures('authtoken')
class Test_Common_NotificationTemplate(APITest):

    def build_supported_messages(self, notification_type):
        SupportedMessages = namedtuple('SupportedMessages', field_names=['has_message', 'has_body'])
        SUPPORT_MESSAGES_MAP = {'email': SupportedMessages(True, True),
                                'grafana': SupportedMessages(True, False),
                                'irc': SupportedMessages(True, False),
                                'mattermost': SupportedMessages(True, False),
                                'pagerduty': SupportedMessages(True, True),
                                'rocketchat': SupportedMessages(True, False),
                                'slack': SupportedMessages(True, False),
                                'twilio': SupportedMessages(True, False),
                                'webhook': SupportedMessages(False, True)}
        supported_messages = SUPPORT_MESSAGES_MAP[notification_type]

        messages = {'started': {}, 'error': {}, 'success': {}}
        for event in messages:
            if supported_messages.has_message:
                messages[event]['message'] = 'message_{}'.format(event)
            if supported_messages.has_body:
                if notification_type == 'webhook':
                    # https://docs.python.org/3/library/string.html#formatstrings
                    # "[For `format()`..] if you need to include a brace character in the literal text,
                    # it can be escaped by doubling: {{ and }}."
                    messages[event]['body'] = '{{"event": "{}"}}'.format(event)
                else:
                    messages[event]['body'] = 'body_{}'.format(event)
        return messages

    def build_messages(self, content):
        return dict(
            started=dict(message=content, body=content),
            success=dict(message=content, body=content),
            error=dict(message=content, body=content)
        )

    def build_errors(self, error):
        errors = []
        NUM_MSGS_IN_NOTIFICATION_TEMPLATE = 6
        for i in range(NUM_MSGS_IN_NOTIFICATION_TEMPLATE):
            errors.append(error)
        return {'messages': errors}

    @pytest.mark.parametrize('valid_message',
        [
            'Message without templating',
            'Message with top-level field: {{ job.job_explanation }}',
            'Message with nested field: {{ job.summary_fields.inventory.total_hosts }}'
        ], ids=(
            'message without templating',
            'message with top-level field',
            'message with nested field',
        )
    )
    def test_valid_notification_messages(self, factories,
                                         slack_notification_template, valid_message):
        messages = self.build_messages(valid_message)
        nt = factories.notification_template(messages=messages)
        assert nt.messages == messages

    @pytest.mark.parametrize('invalid_message, error_msg',
        [
            ('{{ unclosed_tag', "Unable to render message '{{ unclosed_tag': unexpected end of template, expected 'end of print statement'."),
            ('{{ abc.abc }}', "Field 'abc' unavailable"),
            ('{{ job.title | fake_filter }}', "Unable to render message '{{ job.title | fake_filter }}': no filter named 'fake_filter'"),
            ('{{ job.job_env }} is not white-listed', "Field 'job_env' unavailable"),
            ('{{ job.job_args }} is not white-listed, either', "Field 'job_args' unavailable")
        ], ids=(
            'unclosed tag',
            'unavailable field',
            'fake filter',
            'sensitive field (job_env)',
            'sensitive field (job_args)'
        )
    )
    def test_invalid_notification_messages(self, factories,
                                           slack_notification_template, invalid_message,
                                           error_msg):
        messages = self.build_messages(invalid_message)
        with pytest.raises(awxkit.exceptions.BadRequest) as e:
            factories.notification_template(messages=messages)
        assert e.value.msg == self.build_errors(error_msg)

    @pytest.mark.parametrize('message, expected_msg',
        [
            ('Starting {{ job.name }}', 'Starting {job.name}'),
            ('䉪ቒ칸ⱷꯔ噂폄蔆㪗輥', '䉪ቒ칸ⱷꯔ噂폄蔆㪗輥'),
            ('{{ "䉪䉪ቒ칸ⱷꯔ噂폄蔆㪗輥" }}', '䉪䉪ቒ칸ⱷꯔ噂폄蔆㪗輥')
        ], ids=(
            'template with job field',
            'unicode',
            'unicode inside template'
        )
    )
    def test_rendered_message(self, factories, message, expected_msg):
        nt = factories.notification_template(messages={'started': {'message': message}})
        jt = factories.job_template()
        jt.add_notification_template(nt, endpoint='notification_templates_started')
        job = jt.launch()
        assert confirm_notification(nt, expected_msg.format(job=job))

    def test_notification_template_default_contains_no_message(self, notification_template):
        assert 'messages' in notification_template and notification_template['messages'] == {'started': None, 'success': None, 'error': None}

    def test_notification_template_contains_update_all_default_messages(self, notification_template):
        notification_configuration_event = self.build_supported_messages(notification_template.notification_type)
        notification_template.patch(messages=notification_configuration_event)
        notification_template.get()
        for event in ['started', 'success', 'error']:
            assert notification_template['messages'][event] == notification_configuration_event[event]
        assert sorted(['started', 'success', 'error']) == sorted(list(notification_template['messages'].keys()))

    def test_notification_template_contains_update_some_default_messages(self, notification_template):
        full_configuration_event = self.build_supported_messages(notification_template.notification_type)
        for event in ['started', 'success', 'error']:
            partial_configuration_event = {event: full_configuration_event[event]}
            notification_template.patch(messages=partial_configuration_event)
            notification_template.get()
            assert notification_template['messages'][event] == partial_configuration_event[event]
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
        full_configuration_event = self.build_supported_messages(notification_template.notification_type)
        messages_for_error_only = {'error': full_configuration_event['error']}
        notification_template.patch(messages=messages_for_error_only)

        jt = factories.job_template()
        associate_notification_template(notification_template, jt, 'started')
        job = jt.launch().wait_until_completed()
        job.assert_successful()
        notifications = job.get_related('notifications').wait_until_count(1)

        if notification_template.notification_type == 'webhook':
            body = notifications.results.pop()['body']
            assert 'id' in body
            assert str(job.id) == str(body['id'])
        else:
            assert "Job #%s '%s'" % (job.id, job.get_related('job_template').name) in notifications.results.pop()['subject']

    @pytest.mark.parametrize('event', ['started', 'success', 'error'])
    def test_job_template_launch_with_custom_notification_on_event(self, notification_template, factories, event):
        full_configuration_event = self.build_supported_messages(notification_template.notification_type)
        messages_for_event_only = {event: full_configuration_event[event]}
        notification_template.patch(messages=messages_for_event_only)

        playbook = 'fail.yml' if event == 'error' else 'ping.yml'
        jt = factories.job_template(playbook=playbook)
        associate_notification_template(notification_template, jt, event)
        job = jt.launch().wait_until_completed()
        notifications = job.get_related('notifications').wait_until_count(1)

        if notification_template.notification_type == 'webhook':
            key = 'body'
            headers = notification_template.notification_configuration['headers']
            body = messages_for_event_only[event]['body']
            message = (headers, body)
        else:
            key = 'subject'
            message = messages_for_event_only[event]['message']

        assert event in notifications.results.pop()[key]
        if can_confirm_notification(notification_template):
            assert confirm_notification(notification_template, message)

    @pytest.mark.parametrize('event', ['started', 'success', 'error'])
    def test_job_template_launch_with_default_notification_on_event(self, notification_template, factories, event):

        playbook = 'fail.yml' if event == 'error' else 'ping.yml'
        jt = factories.job_template(playbook=playbook)
        associate_notification_template(notification_template, jt, event)
        job = jt.launch().wait_until_completed()
        notifications = job.get_related('notifications').wait_until_count(1)

        if notification_template.notification_type == 'webhook':
            assert str(job.id) in str(notifications.results.pop()['body'])
        else:
            assert "Job #%s '%s'" % (job.id, job.get_related('job_template').name) in notifications.results.pop()['subject']
