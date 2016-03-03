import sys
import logging
import pytest
import common.tower.license


log = logging.getLogger(__name__)


@pytest.fixture(scope='function')
def no_license(request, authtoken, api_config_pg):
    '''Remove an active license'''
    log.debug("deleting any active license")
    api_config_pg.delete()
    request.addfinalizer(api_config_pg.delete)


@pytest.fixture(scope='function')
def install_legacy_license(request, api_config_pg, ansible_runner):
    '''Install an legacy license where instance_count=unlimited'''
    # Apply license
    log.debug("calling fixture install_legacy_license_unlimited")
    license_info = common.tower.license.generate_license(instance_count=sys.maxint, days=365, license_type='legacy')
    api_config_pg.post(license_info)
    request.addfinalizer(api_config_pg.delete)

    # Confirm that license is present
    conf = api_config_pg.get()
    assert conf.is_valid_license, 'Expected valid license, invalid license found'

    # Confirm license type, license_key have expected values
    assert conf.is_legacy_license, \
        "Expected legacy license, found %s." % conf.license_info.license_type
    assert conf.license_info.license_key == license_info['license_key'], \
        "License found differs from license applied"


@pytest.fixture(scope='function')
def install_basic_license(request, api_config_pg, ansible_runner):
    '''Install an basic license where instance_count=unlimited'''
    # Apply license
    log.debug("calling fixture install_basic_license_unlimited")
    license_info = common.tower.license.generate_license(instance_count=sys.maxint, days=365, license_type='basic')
    api_config_pg.post(license_info)
    request.addfinalizer(api_config_pg.delete)

    # Confirm that license is present
    conf = api_config_pg.get()
    assert conf.is_valid_license, 'Expected valid license, invalid license found'

    # Confirm license type, license_key have expected values
    assert conf.is_basic_license, \
        "Expected basic license, found %s." % conf.license_info.license_type
    assert conf.license_info.license_key == license_info['license_key'], \
        "License found differs from license applied"


@pytest.fixture(scope='function')
def install_enterprise_license(request, api_config_pg, ansible_runner):
    '''Install an enterprise license where instance_count=unlimited'''
    log.debug("calling fixture install_enterprise_license")

    # Post the license
    license_info = common.tower.license.generate_license(instance_count=sys.maxint, days=365, license_type='enterprise')
    api_config_pg.post(license_info)

    # Confirm that license is present
    conf = api_config_pg.get()
    assert conf.is_valid_license, 'Expected valid license, invalid license found'

    # Confirm license type, license_key have expected values
    assert conf.is_enterprise_license, \
        "Expected enterprise license, found %s." % conf.license_info.license_type
    assert conf.license_info.license_key == license_info['license_key'], \
        "License found differs from license applied"

    def teardown():
        # Delete the license
        api_config_pg.delete()

    request.addfinalizer(teardown)


@pytest.fixture(scope='class')
def install_enterprise_license_unlimited(request, api_config_pg, ansible_runner):
    '''Install an enterprise license where instance_count=unlimited'''

    log.debug("calling fixture install_enterprise_license_unlimited")

    # Post the license
    license_info = common.tower.license.generate_license(instance_count=sys.maxint, days=365, license_type='enterprise')
    api_config_pg.post(license_info)

    def teardown():
        # Delete the license
        api_config_pg.delete()

        # Pause to allow tower to do it's thing
        ansible_runner.pause(seconds=15)

    request.addfinalizer(teardown)
