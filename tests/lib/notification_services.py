import json
import logging
import requests
import time

import pytest
from slacker import Slacker

from awxkit.config import config

log = logging.getLogger(__name__)

# FIXME: General issue - methods may return true if they find
#        test notification from previous test run.
#        Need way to ensure that searches exclude notifications
#        fired before this test run. (Fire off bookmark notification? Use time?)


def confirm_slack_message(msg, notification_template_pg):
    """Determine if given message is present in slack channel(s). Return True if found."""
    # TODO: Compare slack history before and after firing notification?
    #      (to ensure that no other notifications were created?)

    # Get slack configuration
    token = config.credentials['notification_services']['slack']['token']
    channels = config.credentials['notification_services']['slack']['channels']

    # Connect
    slack = Slacker(token)

    # Get channel information
    channel_list = slack.channels.list().body['channels']
    channel_mapping = dict((channel['name'], channel['id']) for channel in channel_list)

    # Check each channel
    for channel in channels:
        if channel not in channel_mapping:
            assert False, "Failed to locate slack channel '%s'" % channel
        channel_id = channel_mapping[channel]

        # Locate message
        history = slack.channels.history(channel=channel_id).body['messages']
        for line in history:
            if msg == line['text']:
                # Regression test for https://github.com/ansible/tower/issues/3294
                assert not line.get('username', '') == 'bot'
                assert 'bot_profile' in line
                return True
    return False


def confirm_webhook_message(msg, notification_template_pg):
    """Determine if given message was sent to webservice.

    Both the headers and body of webhook notifications are formatted as json.
    This method takes `msg`, a tuple containing the headers and body expected
    from the webhook payload.
    """
    bin_id = notification_template_pg.notification_configuration.url.replace('https://postb.in/', '')
    notification_result = requests.get('https://postb.in/api/bin/%s/req/shift' % bin_id).json()  # returns dict

    expected_body = msg[1]
    if not isinstance(notification_result, dict) or 'body' not in notification_result:
        return False
    body = notification_result['body']

    # Both body and expected body should be dictionaries - convert to actual dictionaries
    if not isinstance(expected_body, dict):
        try:
            expected_body = json.loads(expected_body)
        except json.JSONDecodeError:
            pytest.fail('Unable to convert webhook expected body to dictionary (must be in json dict format)')

    return body == expected_body


# TODO: Bit odd to be defining dictionary here
CONFIRM_METHOD = {
    "slack": confirm_slack_message,
    "webhook": confirm_webhook_message
}


def can_confirm_notification(notification_template_pg):
    """Determines if notification can be confirmed by this module"""
    return notification_template_pg.notification_type in CONFIRM_METHOD


def confirm_notification(notification_template_pg, msg, is_present=True, interval=5, min_polls=2,
                         max_polls=12):
    """Confirms presence (or absence) of given message in appropriate notification service. Returns True if message
    is in expected state.
    """
    nt_type = notification_template_pg.notification_type
    if not can_confirm_notification(notification_template_pg):
        raise Exception("notification type %s not supported" % nt_type)

    # Poll notification service
    i = 0
    while i < max_polls:
        present = CONFIRM_METHOD[nt_type](msg, notification_template_pg)
        if present:
            break
        i += 1
        if not is_present and i > min_polls:
            break
        log.debug("Sleeping for {}".format(interval))
        time.sleep(interval)
    return present == is_present
