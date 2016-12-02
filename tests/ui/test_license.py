import os
import tempfile
from time import time
from random import randint
from datetime import datetime, timedelta

import pytest

from towerkit.tower.license import generate_license, generate_license_file


pytestmark = [pytest.mark.ui]


@pytest.fixture
def unlicensed(v1, ui, default_tower_credentials):
    un = default_tower_credentials['username']
    pw = default_tower_credentials['password']
    v1.config.delete()
    ui.login.logout()
    ui.login.login_username.send_keys(un)
    ui.login.login_password.send_keys(pw)
    ui.login.login_button.click()
    ui.login.logout()
    ui.login.login_username.send_keys(un)
    ui.login.login_password.send_keys(pw)
    ui.login.login_button.click()
    yield
    v1.config.get().install_license()


@pytest.mark.usefixtures('unlicensed')
def test_license_upload(ui):
    """End-to-end functional test for uploading a valid license
    """
    ui_license = ui.license

    license_path = generate_license_file(
        days=randint(30, 999),
        license_type='enterprise')

    ui_license.upload(license_path)

    assert not ui_license.submit.is_enabled()

    ui_license.agree_eula.click()

    assert ui_license.submit.is_enabled()

    ui_license.submit.click()  # redirects to dashboard here
    ui_license.get()

    assert ui_license.license_status.text == 'Valid License'


@pytest.mark.usefixtures('unlicensed')
def test_license_date(v1, ui):
    """Verify the correct time remaining and license expiration date
    """
    ui_license = ui.license

    license_info = generate_license(
        days=randint(30, 999),
        license_type='enterprise')

    v1.config.post(license_info)

    ui_license.get()
    ui_license.wait_until_time_remaining_is_displayed()

    license_date = int(license_info['license_date'])
    current_date = int(time())
    time_remaining = timedelta(seconds=license_date - current_date).days

    expires_expected = datetime.utcnow() + timedelta(days=time_remaining)
    expires_actual = datetime.strptime(ui_license.expires_on.text, "%m/%d/%Y")

    expected_time_remaining = (
        '{0} Days'.format(int(time_remaining) - 1),
        '{0} Days'.format(time_remaining),
        '{0} Days'.format(int(time_remaining) + 1),
    )
    assert ui_license.time_remaining.text in expected_time_remaining
    assert abs(expires_actual - expires_expected).days <= 1


@pytest.mark.usefixtures('unlicensed')
def test_malformed_license(ui):
    """Verify the alert modal is displayed when an invalid json file is uploaded
    """
    (fd, license_path) = tempfile.mkstemp(suffix='.json')
    os.write(fd, 'this is not valid json')
    os.close(fd)

    ui_license = ui.license.get()
    ui_license.upload(license_path)
    ui_license.wait_until_alert_modal_is_displayed()

    assert 'invalid' in ui_license.alert_modal.text.lower()


@pytest.mark.skip
def test_missing_license_file(ui):
    """Verify the submit button is not clickable when a file is attached to
    the upload input but does not exist on disk.
    """
    ui_license = ui.license

    ui_license.upload('/not_a_real_file.json')
    ui_license.agree_eula.click()

    assert not ui_license.submit.is_enabled()
