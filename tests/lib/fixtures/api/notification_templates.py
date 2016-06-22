import fauxfactory
import pytest


@pytest.fixture(scope="function", params=["email", "hipchat", "irc", "pagerduty", "slack", "twilio", "webhook"])
def notification_template(request, authtoken, api_notification_templates_pg):
    '''All notification templates'''
    payload = request.getfuncargvalue(request.param + "_notification_template_payload")
    obj = api_notification_templates_pg.post(payload)
    request.addfinalizer(obj.delete)
    return obj


@pytest.fixture(scope="function")
def email_notification_template_payload(request, testsetup, default_organization):
    '''email payload - requires organization id'''
    host = testsetup.credentials['notification_services']['email']['host']
    username = testsetup.credentials['notification_services']['email']['username']
    password = testsetup.credentials['notification_services']['email']['password']
    port = testsetup.credentials['notification_services']['email']['port']
    use_ssl = testsetup.credentials['notification_services']['email']['use_ssl']
    use_tls = testsetup.credentials['notification_services']['email']['use_tls']
    sender = testsetup.credentials['notification_services']['email']['sender']
    # FIXME: Handle list (currently just string)
    recipients = testsetup.credentials['notification_services']['email']['recipients']

    email_configuration = dict(host=host,
                               username=username,
                               password=password,
                               port=port,
                               use_ssl=use_ssl,
                               use_tls=use_tls,
                               sender=sender,
                               recipients=recipients)

    payload = dict(name="email notification template-%s" % fauxfactory.gen_utf8(),
                   description="Random email notification template - %s" % fauxfactory.gen_utf8(),
                   organization=default_organization.id,
                   notification_type='email',
                   notification_configuration=email_configuration)

    return payload


@pytest.fixture(scope="function")
def hipchat_notification_template_payload(request, testsetup, default_organization):
    '''hipchat payload - requires organization id'''
    message_from = testsetup.credentials['notification_services']['hipchat']['message_from']
    api_url = testsetup.credentials['notification_services']['hipchat']['api_url']
    color = testsetup.credentials['notification_services']['hipchat']['color']
    rooms = testsetup.credentials['notification_services']['hipchat']['rooms']
    token = testsetup.credentials['notification_services']['hipchat']['bot_token']
    notify = testsetup.credentials['notification_services']['hipchat']['notify']

    hipchat_configuration = dict(message_from=message_from,
                                 api_url=api_url,
                                 color=color,
                                 rooms=rooms,
                                 token=token,
                                 notify=notify)

    payload = dict(name="hipchat notification template-%s" % fauxfactory.gen_utf8(),
                   description="Random hipchat notification template - %s" % fauxfactory.gen_utf8(),
                   organization=default_organization.id,
                   notification_type='hipchat',
                   notification_configuration=hipchat_configuration)

    return payload


@pytest.fixture(scope="function")
def irc_notification_template_payload(request, testsetup, default_organization):
    '''irc payload - requires organization id'''
    server = testsetup.credentials['notification_services']['irc']['server']
    port = testsetup.credentials['notification_services']['irc']['port']
    use_ssl = testsetup.credentials['notification_services']['irc']['use_ssl']
    password = testsetup.credentials['notification_services']['irc']['password']
    nickname = testsetup.credentials['notification_services']['irc']['nickname']
    targets = testsetup.credentials['notification_services']['irc']['targets']

    irc_configuration = dict(server=server,
                             port=port,
                             use_ssl=use_ssl,
                             password=password,
                             nickname=nickname,
                             targets=targets)

    payload = dict(name="irc notification template-%s" % fauxfactory.gen_utf8(),
                   description="Random irc notification template - %s" % fauxfactory.gen_utf8(),
                   organization=default_organization.id,
                   notification_type='irc',
                   notification_configuration=irc_configuration)

    return payload


@pytest.fixture(scope="function")
def pagerduty_notification_template_payload(request, testsetup, default_organization):
    '''pagerduty payload - requires organization id'''
    client_name = testsetup.credentials['notification_services']['pagerduty']['client_name']
    service_key = testsetup.credentials['notification_services']['pagerduty']['service_key']
    subdomain = testsetup.credentials['notification_services']['pagerduty']['subdomain']
    token = testsetup.credentials['notification_services']['pagerduty']['token']

    pagerduty_configuration = dict(client_name=client_name,
                                   service_key=service_key,
                                   subdomain=subdomain,
                                   token=token)

    payload = dict(name="pagerduty notification template-%s" % fauxfactory.gen_utf8(),
                   description="Random pagerduty notification template - %s" % fauxfactory.gen_utf8(),
                   organization=default_organization.id,
                   notification_type='pagerduty',
                   notification_configuration=pagerduty_configuration)

    return payload


@pytest.fixture(scope="function")
def slack_notification_template_payload(request, testsetup, default_organization):
    '''slack payload - requires organization id'''
    channels = testsetup.credentials['notification_services']['slack']['channels']
    token = testsetup.credentials['notification_services']['slack']['token']

    slack_configuration = dict(channels=channels,
                               token=token)

    payload = dict(name="slack notification template-%s" % fauxfactory.gen_utf8(),
                   description="Random slack notification template - %s" % fauxfactory.gen_utf8(),
                   organization=default_organization.id,
                   notification_type='slack',
                   notification_configuration=slack_configuration)

    return payload


@pytest.fixture(scope="function")
def twilio_notification_template_payload(request, testsetup, default_organization):
    '''twilio payload - requires organization id'''
    account_sid = testsetup.credentials['notification_services']['twilio']['account_sid']
    account_token = testsetup.credentials['notification_services']['twilio']['account_token']
    from_number = testsetup.credentials['notification_services']['twilio']['from_number']
    to_numbers = testsetup.credentials['notification_services']['twilio']['to_numbers']

    twilio_configuration = dict(account_sid=account_sid,
                                account_token=account_token,
                                from_number=from_number,
                                to_numbers=to_numbers)

    payload = dict(name="twilio notification template-%s" % fauxfactory.gen_utf8(),
                   description="Random twilio notification template - %s" % fauxfactory.gen_utf8(),
                   organization=default_organization.id,
                   notification_type='twilio',
                   notification_configuration=twilio_configuration)

    return payload


@pytest.fixture(scope="function")
def webhook_notification_template_payload(request, testsetup, default_organization):
    '''webhook payload - requires organization id'''
    url = testsetup.credentials['notification_services']['webhook']['url']
    headers = testsetup.credentials['notification_services']['webhook']['headers']

    webhook_configuration = dict(url=url, headers=headers)

    payload = dict(name="webhook notification template-%s" % fauxfactory.gen_utf8(),
                   description="Random webhook notification template - %s" % fauxfactory.gen_utf8(),
                   organization=default_organization.id,
                   notification_type='webhook',
                   notification_configuration=webhook_configuration)

    return payload
