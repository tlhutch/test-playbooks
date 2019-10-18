#!/usr/bin/env python

import base64
import pytest
import requests
import awxkit.exceptions

from tests.api import APITest


@pytest.mark.usefixtures('authtoken')
class Test_Webhook_NotificationTemplate(APITest):

    @pytest.mark.parametrize('message, error_message, expect_exception', [
        ['test', 'is not a valid json dictionary (Expecting value: line 1 column 1 (char 0)).', True],
        ['{"foo": "bar"}', '', False],
    ])
    def test_validate_inputs(self, factories, message, error_message, expect_exception):
        notification_configuration = {
            'headers': {},
            'url': 'https://ansible-tower-engineering.appspot.com',
        }
        messages = {
            'error': {'body': None, 'message': None},
            'started': {'body': message, 'message': None},
            'success': {'body': None, 'message': None},
        }

        if expect_exception:
            with pytest.raises(awxkit.exceptions.BadRequest) as e:
                factories.notification_template(
                    notification_type="webhook",
                    notification_configuration=notification_configuration,
                    messages=messages
                )
            assert error_message in str(e.value)
        else:
            factories.notification_template(
                notification_type="webhook",
                notification_configuration=notification_configuration,
                messages=messages
            )

    @pytest.mark.parametrize('method, expect_exception', [
        ['POST', False],
        ['PUT', False],
        ['ANYOTHERTHING', True],
    ])
    def test_supported_http_method_inputs(self, factories, method, expect_exception):
        notification_configuration = {
            'headers': {},
            'url': 'https://ansible-tower-engineering.appspot.com',
            'http_method': method
        }

        if expect_exception:
            with pytest.raises(awxkit.exceptions.BadRequest):
                factories.notification_template(
                    notification_type="webhook",
                    notification_configuration=notification_configuration
                )
        else:
            factories.notification_template(
                notification_type="webhook",
                notification_configuration=notification_configuration
            )

    def test_supported_http_method_inputs_update(self, factories):
        notification_configuration = {
            'headers': {},
            'url': 'https://ansible-tower-engineering.appspot.com',
            'http_method': 'POST'
        }

        nt = factories.notification_template(
            notification_type="webhook",
            notification_configuration=notification_configuration
        )

        notification_configuration_patch = {
            'headers': {},
            'url': 'https://ansible-tower-engineering.appspot.com',
            'http_method': 'ANYOTHERTHING'
        }
        with pytest.raises(awxkit.exceptions.BadRequest):
            nt.patch(notification_configuration=notification_configuration_patch)

    @pytest.mark.parametrize('method', ['POST', 'PUT'])
    def test_supported_http_method_actions(self, factories, webhook_binId, method):
        notification_configuration = {
            'headers': {},
            'url': 'https://postb.in/%s' % webhook_binId,
            'http_method': method
        }

        notification_template = factories.notification_template(
            notification_type="webhook",
            notification_configuration=notification_configuration
        )
        notification_template.test().wait_until_completed(timeout=30)
        notification_result = requests.get('https://postb.in/api/bin/%s/req/shift' % webhook_binId).json()

        assert notification_result['method'] == method

    @pytest.mark.parametrize('username, password', [
        ['foo', 'password'],
        ['foo', ''],
        ['', 'password'],
        ['', ''],
    ])
    def test_supported_basic_auth_inputs(self, factories, username, password):
        notification_configuration = {
            'headers': {},
            'url': 'https://ansible-tower-engineering.appspot.com',
            'http_method': 'POST',
            'username': username,
            'password': password
        }

        factories.notification_template(
            notification_type="webhook",
            notification_configuration=notification_configuration
        )

    @pytest.mark.parametrize('username, password, expect_authorization_header', [
        ['foo', 'password', True],
        ['foo', '', True],
        ['', 'password', True],
        ['', '', False],
    ])
    def test_supported_basic_auth_actions(self, factories, webhook_binId, username, password, expect_authorization_header):
        notification_configuration = {
            'headers': {},
            'url': 'https://postb.in/%s' % webhook_binId,
            'http_method': 'POST',
            'username': username,
            'password': password
        }

        notification_template = factories.notification_template(
            notification_type="webhook",
            notification_configuration=notification_configuration
        )
        notification_template.test().wait_until_completed(timeout=30)
        notification_result = requests.get('https://postb.in/api/bin/%s/req/shift' % webhook_binId).json()

        if expect_authorization_header:
            authorization_header = notification_result['headers'].get('authorization')
            assert base64.b64decode(authorization_header.split(' ')[-1]).decode() == '%s:%s' % (username, password)
        else:
            assert not notification_result['headers'].get('authorization')
