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

    # Determine if mongo is needed
    contacted = ansible_runner.command("tower-manage uses_mongo --local")
    result = contacted.values()[0]
    assert result['rc'] in [0, 1], "Unexpected exit code from 'tower-manage uses_mongo' command: %s" % result['rc']
    uses_mongo = 'MongoDB required' in result['stdout']

    if uses_mongo:
        # Wait for mongod to start
        contacted = ansible_runner.wait_for(port='27017', state='present', delay=5)
        assert 'failed' not in contacted.values()[0], \
            "MongoDB is not running, but is expected to be running."

    def teardown():
        # Determine if mongo is needed
        contacted = ansible_runner.command("tower-manage uses_mongo --local")
        result = contacted.values()[0]
        assert result['rc'] in [0, 1], "Unexpected exit code from 'tower-manage uses_mongo' command: %s" % result['rc']
        uses_mongo = 'MongoDB required' in result['stdout']

        # Delete the license
        api_config_pg.delete()

        # If mongo was required, be sure it's stopped
        if uses_mongo:
            # Wait for mongo to stop listening over the network
            contacted = ansible_runner.wait_for(port='27017', state='absent', delay=5)
            result = contacted.values()[0]
            # Mongo did not stop, force shutdown and raise exception
            if 'failed' in result:
                log.warn("mongod failed to stop, forcing shutdown")
                contacted = ansible_runner.command('mongod --dbpath /var/lib/mongo --shutdown')
                result = contacted.values()[0]
                assert result['rc'] == 0, "Failed to shutdown mongod - %s" % json.dump(result, indent=2)
                raise Exception("MongoDB was still running after the license was deleted.")

            # Wait for mongod to be absent
            # ansible_runner.shell('while pidof mongod ; do sleep 1 ; done')

    request.addfinalizer(teardown)


@pytest.fixture(scope='class')
def install_enterprise_license_unlimited(request, api_config_pg, ansible_runner):
    '''Install an enterprise license where instance_count=unlimited'''

    log.debug("calling fixture install_enterprise_license_unlimited")

    # Wait for mongod to be absent ... this could unnecesarily delay things,
    # but avoids the scenario where a previous enterprise license teardown()
    # completes prematurely, and the server is processing a mongod stop *and*
    # start request at the time.
    # Workaround for pause module bug (refer
    # https://github.com/ansible/ansible/commit/ca8261ed317fea7415828ab8a80f44c3f3d15d9c).
    # Once fixed after 2.0.0.2, the following should be replaced with the `pause`
    # module.
    contacted = ansible_runner.command('sleep 10')
    # contacted = ansible_runner.pause(seconds='10')
    assert 'failed' not in contacted.values()[0], \
        "Failure occurred while calling ansible pause module. " \
        "Module exception below:\n%s" % \
        contacted.values()[0].get('exception', 'Missing exception')

    # Post the license
    license_info = common.tower.license.generate_license(instance_count=sys.maxint, days=365, license_type='enterprise')
    api_config_pg.post(license_info)

    # Wait for mongod to start
    contacted = ansible_runner.wait_for(port='27017', state='present', delay=5)
    assert 'failed' not in contacted.values()[0], \
        "MongoDB is not running, but is expected to be running."

    def teardown():
        # Delete the license
        api_config_pg.delete()

        # Pause to allow tower to do it's thing
        ansible_runner.pause(seconds=15)

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

        # Wait for mongod to be absent
        # ansible_runner.shell('while pidof mongod ; do sleep 1 ; done')

    request.addfinalizer(teardown)
