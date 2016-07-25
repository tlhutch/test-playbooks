import logging
import sys
import time

import pytest

from common.tower.license import generate_license


log = logging.getLogger(__name__)


def install_license(request, api_config_pg, **kwargs):
    # generate license
    license_info = generate_license(**kwargs)
    # install license
    api_config_pg.post(license_info)
    request.addfinalizer(api_config_pg.delete)
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


@pytest.fixture
def no_license(request, api_config_pg):
    """Remove an active license
    """
    log.debug('deleting any active license')
    api_config_pg.delete()
    request.addfinalizer(api_config_pg.delete)


@pytest.fixture
def install_legacy_license(request, api_config_pg):
    """Install legacy license
    """
    log.debug('calling fixture install_legacy_license_unlimited')
    install_license(request,
                    api_config_pg,
                    days=365,
                    instance_count=sys.maxint,
                    license_type='legacy')


@pytest.fixture
def install_basic_license(request, api_config_pg):
    """Install basic license
    """
    log.debug('calling fixture install_basic_license_unlimited')
    install_license(request,
                    api_config_pg,
                    days=365,
                    instance_count=sys.maxint,
                    license_type='basic')


@pytest.fixture
def install_enterprise_license(request, api_config_pg):
    """Install enterprise license
    """
    log.debug('calling fixture install_enterprise_license')
    install_license(request,
                    api_config_pg,
                    days=365,
                    instance_count=sys.maxint,
                    license_type='enterprise')


@pytest.fixture(scope='class')
def install_enterprise_license_unlimited(request, api_config_pg):
    """Install enterprise license at the class fixture scope
    """
    log.debug('calling fixture install_enterprise_license_unlimited')
    install_license(request,
                    api_config_pg,
                    days=365,
                    instance_count=sys.maxint,
                    license_type='enterprise')
    # Pause to allow tower to do it's thing
    request.addfinalizer(lambda: time.sleep(15))


@pytest.fixture(scope='module')
def module_install_enterprise_license(authtoken, request, api_config_pg):
    """Install enterprise license at the module fixture scope
    """
    log.debug('calling fixture module_install_enterprise_license')
    install_license(request,
                    api_config_pg,
                    days=365,
                    instance_count=sys.maxint,
                    license_type='enterprise')
    # Pause to allow tower to do it's thing
    request.addfinalizer(lambda: time.sleep(15))
