import pytest
import yaml

from . import utils


@pytest.fixture(scope='session')
def rekey_data():
    with open('rekey-data.yml') as handler:
        return yaml.safe_load(handler)


@pytest.fixture(scope='module')
def ansible_adhoc(session_ansible_adhoc):
    return session_ansible_adhoc()


def test_secret_key_is_different(ansible_adhoc, is_docker, rekey_data):
    current_secret_key = utils.fetch_secret_key(ansible_adhoc, is_docker)
    previous_secret_key = rekey_data['secret_key']
    if is_docker:
        # On docker we are not running rekey so it should continue to be the
        # same
        assert current_secret_key == previous_secret_key
    else:
        assert current_secret_key != previous_secret_key


def test_settings_readable(ansible_adhoc, rekey_data):
    password = utils.adhoc_cmd(
        ansible_adhoc,
        utils.SETTINGS_CMD,
        setting='REDHAT_PASSWORD'
    )
    assert password == rekey_data['password']


def test_client_secret_readable(ansible_adhoc, rekey_data):
    current = utils.adhoc_cmd(
        ansible_adhoc,
        utils.CLIENT_SECRET_CMD,
        application_id=rekey_data['application']['id']
    )
    assert current == rekey_data['application']['client_secret']


def test_credential_password_readable(ansible_adhoc, rekey_data):
    current = utils.adhoc_cmd(
        ansible_adhoc,
        utils.CREDENTIAL_PASSWORD_CMD,
        credential_id=rekey_data['credential']['id']
    )
    assert current == rekey_data['credential']['password']


@pytest.mark.parametrize(
    'extra_vars_key, cmd',
    (
        ('decrypted_extra_vars', utils.JOB_TEMPLATE_EXTRA_VARS_CMD),
        ('job_decrypted_extra_vars', utils.JOB_TEMPLATE_JOB_EXTRA_VARS_CMD),
    ),
    ids=('decrypted_extra_vars', 'job_decrypted_extra_vars')
)
def test_job_template_extra_vars_readable(ansible_adhoc, cmd, extra_vars_key, rekey_data):
    current = utils.adhoc_cmd(
        ansible_adhoc,
        cmd,
        job_template_id=rekey_data['job_template']['id']
    )
    assert current == rekey_data['job_template'][extra_vars_key]


@pytest.mark.parametrize(
    'extra_vars_key, cmd',
    (
        ('decrypted_extra_vars', utils.WORKFLOW_JOB_TEMPLATE_EXTRA_VARS_CMD),
        ('job_decrypted_extra_vars', utils.WORKFLOW_JOB_TEMPLATE_JOB_EXTRA_VARS_CMD),
    ),
    ids=('decrypted_extra_vars', 'job_decrypted_extra_vars')
)
def test_workflow_job_template_extra_vars_readable(ansible_adhoc, cmd, extra_vars_key, rekey_data):
    current = utils.adhoc_cmd(
        ansible_adhoc,
        cmd,
        workflow_job_template_id=rekey_data['workflow_job_template']['id']
    )
    assert current == rekey_data['job_template'][extra_vars_key]


def test_notification_token_readable(ansible_adhoc, rekey_data):
    current = utils.adhoc_cmd(
        ansible_adhoc,
        utils.NOTIFICATION_TOKEN_CMD,
        notification_id=rekey_data['notification']['id']
    )
    assert current == rekey_data['notification']['token']
