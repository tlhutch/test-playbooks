import pytest
import sys
import logging
import common.tower.license


log = logging.getLogger(__name__)


@pytest.fixture(scope='function')
def no_license(request, api_config_pg):
    '''Remove an active license'''
    log.debug("deleting any active license")
    api_config_pg.delete()


@pytest.fixture(scope='class')
def install_enterprise_license_unlimited(request, api_config_pg):
    '''Install an enterprise license where instance_count=unlimited'''

    log.debug("calling fixture install_enterprise_license_unlimited")
    license_info = common.tower.license.generate_license(instance_count=sys.maxint, days=365, license_type='enterprise')
    api_config_pg.post(license_info)
    request.addfinalizer(api_config_pg.delete)

    # FIXME - no way to teardown a license from the API
