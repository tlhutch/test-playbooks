import os
import tempfile
from time import time
from random import randint
from datetime import datetime, timedelta

import pytest

from common.tower.license import generate_license, generate_license_file

pytestmark = [
    pytest.mark.ui,
    pytest.mark.nondestructive,
    pytest.mark.usefixtures(
        'authtoken',
        'maximized_window_size'
    )
]


@pytest.mark.usefixtures('no_license')
def test_license_upload(ui_license):
    """Basic end-to-end verification for uploading a valid license
    """
    license_path = generate_license_file(
        days=randint(30, 999),
        license_type='enterprise')

    ui_license.upload(license_path)

    assert not ui_license.submit.is_clickable()

    ui_license.agree_eula.click()

    assert ui_license.submit.is_clickable()

    ui_license.submit.click()  # redirects to dashboard here

    ui_license.get(ui_license.url)
    ui_license.wait_for_spinny()

    assert ui_license.license_status.text == 'Valid License'


@pytest.mark.usefixtures('no_license')
def test_license_date(api_config_pg, ui_license):
    """Verify the correct time remaining and license expiration date
    """
    license_info = generate_license(
        days=randint(30, 999),
        license_type='enterprise')

    api_config_pg.post(license_info)

    ui_license.get(ui_license.url)
    ui_license.time_remaining.wait_until_displayed()
    ui_license.wait_for_spinny()

    license_date = int(license_info['license_date'])
    current_date = int(time())
    time_remaining = timedelta(seconds=license_date - current_date).days

    expires_expected = datetime.utcnow() + timedelta(days=time_remaining)
    expires_actual = datetime.strptime(ui_license.expires_on.text, "%m/%d/%Y")

    assert ui_license.time_remaining.text == "%s Days" % time_remaining
    assert abs(expires_actual - expires_expected).days <= 1


def test_malformed_license(ui_license):
    """Verify the alert modal is displayed when an invalid json file is uploaded
    """
    (fd, license_path) = tempfile.mkstemp(suffix='.json')
    os.write(fd, 'this is not valid json')
    os.close(fd)

    ui_license.upload(license_path)

    ui_license.alert_modal.wait_until_displayed()

    assert 'invalid' in ui_license.alert_modal.text.lower()


def test_missing_license_file(ui_license):
    """Verify the submit button is not clickable when a file is attached to
    the upload input but does not exist on disk.
    """
    ui_license.upload('/not_a_real_file.json')
    ui_license.agree_eula.click()

    assert not ui_license.submit.is_clickable()
