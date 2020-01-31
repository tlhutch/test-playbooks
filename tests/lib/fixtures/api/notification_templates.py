import pytest

from tests.lib.helpers.http_requests import session_retry


@pytest.fixture
def webhook_binId():
    # Rely on https://postb.in to really test our webhooks
    response = session_retry().post('https://postb.in/api/bin')
    return response.json()['binId']


@pytest.fixture(scope="function", params=[
    "email",
    "irc",
    "mattermost",
    "pagerduty",
    "slack",
    "webhook",
    ])
def notification_template(request):
    """All notification templates."""
    return request.getfixturevalue(request.param + "_notification_template")


@pytest.fixture(scope="function")
def email_notification_template(factories):
    """Email notification template"""
    return factories.notification_template(notification_type="email")


@pytest.fixture(scope="function")
def irc_notification_template(factories):
    """IRC notification template"""
    return factories.notification_template(notification_type="irc")


@pytest.fixture(scope="function")
def pagerduty_notification_template(factories):
    """Pagerduty notification template"""
    return factories.notification_template(notification_type="pagerduty")


@pytest.fixture(scope="function")
def slack_notification_template(factories):
    """Slack notification template"""
    return factories.notification_template(notification_type="slack")


@pytest.fixture(scope="function")
def twilio_notification_template(factories):
    """Twilio notification template"""
    raise NotImplementedError("We don't have the backend setup for twilio")


@pytest.fixture(scope="function")
def webhook_notification_template(factories, webhook_binId):
    """Webhook notification template"""
    return factories.notification_template(
        notification_type="webhook", url='https://postb.in/%s' % webhook_binId, headers={}
    )


@pytest.fixture(scope="function")
def mattermost_notification_template(factories):
    """Mattermost notification template"""
    return factories.notification_template(notification_type="mattermost")
