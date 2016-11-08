import os
import tempfile
from time import time
from random import randint
from datetime import datetime, timedelta

import pytest

from towerkit.tower.license import generate_license, generate_license_file

pytestmark = [
    pytest.mark.ui,
    pytest.mark.nondestructive,
    pytest.mark.usefixtures('max_window')
]


def test_license_upload(authtoken, no_license, ui_license):
    """Basic end-to-end verification for uploading a valid license
    """
    license_path = generate_license_file(
        days=randint(30, 999),
        license_type='enterprise')

    ui_license.upload(license_path)

    assert not ui_license.submit.is_enabled()

    ui_license.agree_eula.click()

    assert ui_license.submit.is_enabled()

    ui_license.submit.click()  # redirects to dashboard here
    ui_license.open()

    assert ui_license.license_status.text == 'Valid License'


def test_license_date(authtoken, no_license, api_config_pg, ui_license):
    """Verify the correct time remaining and license expiration date
    """
    license_info = generate_license(
        days=randint(30, 999),
        license_type='enterprise')

    api_config_pg.post(license_info)
    ui_license.driver.refresh()
    ui_license.wait_until_time_remaining_is_displayed()

    license_date = int(license_info['license_date'])
    current_date = int(time())
    time_remaining = timedelta(seconds=license_date - current_date).days

    expires_expected = datetime.utcnow() + timedelta(days=time_remaining)
    expires_actual = datetime.strptime(ui_license.expires_on.text, "%m/%d/%Y")

    assert ui_license.time_remaining.text == "%s Days" % time_remaining
    assert abs(expires_actual - expires_expected).days <= 1


def test_malformed_license(authtoken, install_enterprise_license, ui_license):
    """Verify the alert modal is displayed when an invalid json file is uploaded
    """
    (fd, license_path) = tempfile.mkstemp(suffix='.json')
    os.write(fd, 'this is not valid json')
    os.close(fd)

    ui_license.upload(license_path)
    ui_license.wait_until_alert_modal_is_displayed()

    assert 'invalid' in ui_license.alert_modal.text.lower()


@pytest.mark.skip
def test_missing_license_file(authtoken, ui_license):
    """Verify the submit button is not clickable when a file is attached to
    the upload input but does not exist on disk.
    """
    ui_license.upload('/not_a_real_file.json')
    ui_license.agree_eula.click()

    assert not ui_license.submit.is_enabled()
