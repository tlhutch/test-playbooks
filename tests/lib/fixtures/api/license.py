import logging
import sys
import time

import pytest

from common.tower.license import generate_license


log = logging.getLogger(__name__)


def install_license(api_config_pg, **kwargs):
    # generate license
    license_info = generate_license(**kwargs)
    # install license
    api_config_pg.post(license_info)
    # Confirm that license is present
    conf = api_config_pg.get()
    assert conf.is_valid_license, 'Invalid license found'
    # Confirm license type
    expected_license_type = license_info['license_type']
    assert conf.license_info.license_type == expected_license_type, (
        'expected {0} license, found {1}'.format(
            expected_license_type, conf.license_info.license_type))
    # Confirm license key
    expected_license_key = license_info['license_key']
    assert conf.license_info.license_key == expected_license_key, (
        'License found differs from license applied')


@pytest.yield_fixture
def no_license(api_config_pg):
    """Remove an active license
    """
    log.debug('deleting any active license')
    api_config_pg.delete()
    yield
    api_config_pg.delete()


@pytest.yield_fixture
def install_legacy_license(api_config_pg):
    """Install legacy license
    """
    log.debug('calling fixture install_legacy_license_unlimited')

    def apply_license():
        install_license(api_config_pg,
                        days=365,
                        instance_count=sys.maxint,
                        license_type='legacy')
    apply_license()
    yield apply_license
    api_config_pg.delete()


@pytest.yield_fixture
def install_basic_license(api_config_pg):
    """Install basic license
    """
    log.debug('calling fixture install_basic_license_unlimited')

    def apply_license():
        install_license(api_config_pg,
                        days=365,
                        instance_count=sys.maxint,
                        license_type='basic')
    apply_license()
    yield apply_license
    api_config_pg.delete()


@pytest.yield_fixture
def install_enterprise_license(api_config_pg):
    """Install enterprise license
    """
    log.debug('calling fixture install_enterprise_license')

    def apply_license():
        install_license(api_config_pg,
                        days=365,
                        instance_count=sys.maxint,
                        license_type='enterprise')
    apply_license()
    yield apply_license
    api_config_pg.delete()


@pytest.yield_fixture(scope='class')
def install_enterprise_license_unlimited(api_config_pg):
    """Install enterprise license at the class fixture scope
    """
    log.debug('calling fixture install_enterprise_license_unlimited')

    def apply_license():
        install_license(api_config_pg,
                        days=365,
                        instance_count=sys.maxint,
                        license_type='enterprise')
    apply_license()
    yield apply_license
    api_config_pg.delete()
    # Pause to allow tower to do it's thing
    time.sleep(15)


@pytest.yield_fixture(scope='module')
def module_install_enterprise_license(authtoken, api_config_pg):
    """Install enterprise license at the module fixture scope
    """
    log.debug('calling fixture module_install_enterprise_license')

    def apply_license():
        install_license(api_config_pg,
                        days=365,
                        instance_count=sys.maxint,
                        license_type='enterprise')
    apply_license()
    yield apply_license
    api_config_pg.delete()
    # Pause to allow tower to do it's thing
    time.sleep(15)
