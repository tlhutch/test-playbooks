import sys
import json
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

    log.debug("calling fixture install_legacy_license_unlimited")
    license_info = common.tower.license.generate_license(instance_count=sys.maxint, days=365, license_type='legacy')
    api_config_pg.post(license_info)
    request.addfinalizer(api_config_pg.delete)


@pytest.fixture(scope='function')
def install_basic_license(request, api_config_pg, ansible_runner):
    '''Install an basic license where instance_count=unlimited'''

    log.debug("calling fixture install_basic_license_unlimited")
    license_info = common.tower.license.generate_license(instance_count=sys.maxint, days=365, license_type='basic')
    api_config_pg.post(license_info)
    request.addfinalizer(api_config_pg.delete)


@pytest.fixture(scope='function')
def install_enterprise_license(request, api_config_pg, ansible_runner):
    '''Install an enterprise license where instance_count=unlimited'''

    log.debug("calling fixture install_enterprise_license_unlimited")
    license_info = common.tower.license.generate_license(instance_count=sys.maxint, days=365, license_type='enterprise')
    api_config_pg.post(license_info)

    def teardown():
        # Delete the license
        api_config_pg.delete()

        # Wait for Mongo to stop (tower allows 30 seconds before forcing shutdown)
        contacted = ansible_runner.wait_for(port='27017', state='absent')
        result = contacted.values()[0]
        # Mongo did not stop, force shutdown and raise exception
        if 'failed' in result:
            log.warn("mongod failed to stop, forcing shutdown")
            contacted = ansible_runner.command('mongod --dbpath /var/lib/mongo --shutdown')
            result = contacted.values()[0]
            assert result['rc'] == 0, "Failed to shutdown mongod - %s" % json.dump(result, indent=2)
            raise Exception("MongoDB was still running after the license was deleted.")

    request.addfinalizer(teardown)


@pytest.fixture(scope='class')
def install_enterprise_license_unlimited(request, api_config_pg, ansible_runner):
    '''Install an enterprise license where instance_count=unlimited'''

    log.debug("calling fixture install_enterprise_license_unlimited")
    license_info = common.tower.license.generate_license(instance_count=sys.maxint, days=365, license_type='enterprise')
    api_config_pg.post(license_info)

    def teardown():
        # Delete the license
        api_config_pg.delete()

        # Wait for Mongo to stop (tower allows 30 seconds before forcing shutdown)
        contacted = ansible_runner.wait_for(port='27017', state='absent')
        result = contacted.values()[0]
        # Mongo did not stop, force shutdown and raise exception
        if 'failed' in result:
            log.warn("mongod failed to stop, forcing shutdown")
            contacted = ansible_runner.command('mongod --dbpath /var/lib/mongo --shutdown')
            result = contacted.values()[0]
            assert result['rc'] == 0, "Failed to shutdown mongod - %s" % json.dump(result, indent=2)
            raise Exception("MongoDB was still running after the license was deleted.")

    request.addfinalizer(teardown)
