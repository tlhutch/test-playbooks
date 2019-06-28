import pytest

from towerkit.tower.license import generate_license

from tests.lib.license import apply_license_until_effective


@pytest.fixture(scope='session', autouse=True)
def session_install_enterprise_license_unlimited(session_authtoken, v2_session):
    """Apply an enterprise license to entire session when tests are run in tests/api.

    Locate this fixture in tests/api/conftest.py such that it is only applied when the session
    includes collecting tests in tests/api.

    That means that collecting tests in tests/api is mutually exclusive with collecting tests in
    tests/license.
    """
    instance_count = 9223372036854775807
    days = 365

    # Fetch the current license information to restore later
    config = v2_session.get().config.get()
    license_info = generate_license(instance_count=instance_count, days=days, license_type='enterprise')
    license_info['eula_accepted'] = True
    if 'license_type' in config.license_info and 'instance_count' in config.license_info:
        if config.license_info.license_type == 'enterprise' and config.license_info.instance_count == instance_count:
            if not config.license_info.date_expired:
                # No need to apply license again, allready have a valid one that is sufficient for our needs
                return
    apply_license_until_effective(config, license_info)
