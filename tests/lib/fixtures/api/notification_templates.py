import pytest


@pytest.fixture(scope="function", params=["email", "hipchat", "irc", "mattermost", "pagerduty", "slack", "twilio",
                                          "webhook"])
def notification_template(request):
    """All notification templates"""
    if request.param == 'twilio':
        pytest.xfail('Unable to send twilio notifications will account inactive')
    return request.getfuncargvalue(request.param + "_notification_template")


@pytest.fixture(scope="function")
def email_notification_template(factories):
    """Email notification template"""
    return factories.notification_template(notification_type="email")


@pytest.fixture(scope="function")
def hipchat_notification_template(factories):
    """Hipchat notification template"""
    return factories.notification_template(notification_type="hipchat")


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
    return factories.notification_template(notification_type="twilio")


@pytest.fixture(scope="function")
def webhook_notification_template(factories):
    """Webhook notification template"""
    headers = {'key1': 'value1', 'key2': 'value2'}   # TODO: Use fauxfactory to generate keys / values
    return factories.notification_template(notification_type='webhook', headers=headers)


@pytest.fixture(scope="function")
def mattermost_notification_template(factories):
    """Mattermost notification template"""
    return factories.notification_template(notification_type="mattermost")
