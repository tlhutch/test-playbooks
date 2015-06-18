import pytest
import sys
import logging
import common.tower.license


log = logging.getLogger(__name__)


@pytest.fixture(scope='function')
def no_license(request, authtoken, api_config_pg):
    '''Remove an active license'''
    log.debug("deleting any active license")
    api_config_pg.delete()
    request.addfinalizer(api_config_pg.delete)


@pytest.fixture(scope='class')
def install_enterprise_license_unlimited(request, api_config_pg, ansible_runner):
    '''Install an enterprise license where instance_count=unlimited'''

    log.debug("calling fixture install_enterprise_license_unlimited")
    license_info = common.tower.license.generate_license(instance_count=sys.maxint, days=365, license_type='enterprise')
    api_config_pg.post(license_info)

    def teardown():
        # Delete the license
        api_config_pg.delete()

        # Wait for Mongo to stop
        contacted = ansible_runner.wait_for(port='27017', delay=5, state='absent')
        result = contacted.values()[0]
        assert 'failed' not in result, "An enterprise license was deleted, but it appears mongod is still running."

    request.addfinalizer(teardown)
