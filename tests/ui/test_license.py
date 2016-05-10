import json
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

    ui_license.submit.click() # redirects to dashboard here

    ui_license.get(ui_license.url)
    ui_license.wait_for_spinny()

    assert ui_license.license_status.text == 'Valid'


@pytest.mark.github('https://github.com/ansible/ansible-tower/issues/1250')
@pytest.mark.usefixtures('no_license')
def test_license_date(api_config_pg, ui_license):
    """Verify the correct time remaining and license expiration date
    """
    license_info = generate_license(
        days=randint(30, 999),
        license_type='enterprise')

    api_config_pg.post(license_info)

    ui_license.get(ui_license.url)
    ui_license.wait_for_spinny()

    license_date = int(license_info['license_date'])
    current_date = int(time())
    time_remaining = timedelta(seconds=license_date - current_date).days
    expires_on = datetime.utcnow() + timedelta(days=time_remaining)

    assert ui_license.time_remaining.text == "%s Days" % time_remaining
    assert ui_license.expires_on.text == expires_on.strftime("%m/%d/%Y")
