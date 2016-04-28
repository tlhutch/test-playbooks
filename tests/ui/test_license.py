import json
from time import time
from random import randint
from datetime import datetime, timedelta

import pytest

from common.tower.license import generate_license_file

pytestmark = [
    pytest.mark.ui,
    pytest.mark.nondestructive,
    pytest.mark.usefixtures(
        'authtoken',
        'maximized_window_size'
    )
]


@pytest.mark.github('https://github.com/ansible/ansible-tower/issues/1250')
@pytest.mark.usefixtures('no_license')
def test_expiration_date(ui_license):
    """Check that the correct expiration date and time remaining are
    displayed on the license page.
    """
    license_path = generate_license_file(
        days=randint(30, 999),
        license_type='enterprise')

    with open(license_path) as license:
        license = json.load(license)

    ui_license.upload(license_path)
    ui_license.agree_eula.click()

    ui_license.submit.click()

    license_date = int(license['license_date'])
    current_date = int(time())
    time_remaining = timedelta(seconds=license_date - current_date).days
    expires_on = datetime.utcnow() + timedelta(days=time_remaining)

    assert ui_license.time_remaining.text == "%s Days" % time_remaining
    assert ui_license.expires_on.text == expires_on.strftime("%m/%d/%Y")
