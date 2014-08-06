import sys
import logging
import pytest
import common.tower.license


log = logging.getLogger(__name__)


@pytest.fixture(scope='class')
def backup_license(request, ansible_runner):
    '''Backup and existing license files. The files will be restored upon teardown.
    '''
    log.debug("calling fixture backup_license")
    ansible_runner.shell('mv /etc/awx/aws /etc/awx/.aws', removes='/etc/awx/aws')
    ansible_runner.shell('mv /etc/awx/license /etc/awx/.license', removes='/etc/awx/license')

    def teardown():
        log.debug("calling teardown backup_license")
        ansible_runner.shell('mv /etc/awx/.aws /etc/awx/aws', removes='/etc/awx/.aws')
        ansible_runner.shell('mv /etc/awx/.license /etc/awx/license', removes='/etc/awx/.license')
    request.addfinalizer(teardown)


@pytest.fixture(scope='class')
def install_license_100(request, ansible_runner):
    '''Install a license where instance_count=100
    '''

    log.debug("calling fixture install_license_100")
    fname = common.tower.license.generate_license_file(instance_count=100, days=365)
    ansible_runner.copy(src=fname, dest='/etc/awx/license', owner='awx', group='awx', mode='0600')

    def teardown():
        log.debug("calling teardown install_license_100")
        ansible_runner.file(path='/etc/awx/license', state='absent')
    request.addfinalizer(teardown)


@pytest.fixture(scope='class')
def install_license_1000(request, ansible_runner):
    '''Install a license where instance_count=1000
    '''

    log.debug("calling fixture install_license_1000")
    fname = common.tower.license.generate_license_file(instance_count=1000, days=365)
    ansible_runner.copy(src=fname, dest='/etc/awx/license', owner='awx', group='awx', mode='0600')

    def teardown():
        log.debug("calling teardown install_license_1000")
        ansible_runner.file(path='/etc/awx/license', state='absent')
    request.addfinalizer(teardown)


@pytest.fixture(scope='class')
def install_license_10000(request, ansible_runner):
    '''Install a license where instance_count=10000
    '''

    log.debug("calling fixture install_license_10000")
    fname = common.tower.license.generate_license_file(instance_count=10000, days=365)
    ansible_runner.copy(src=fname, dest='/etc/awx/license', owner='awx', group='awx', mode='0600')

    def teardown():
        log.debug("calling teardown install_license_10000")
        ansible_runner.file(path='/etc/awx/license', state='absent')
    request.addfinalizer(teardown)


@pytest.fixture(scope='class')
def install_license_unlimited(request, ansible_runner):
    '''Install a license where instance_count=unlimited
    '''

    log.debug("calling fixture install_license_unlimited")
    fname = common.tower.license.generate_license_file(instance_count=sys.maxint, days=365)
    ansible_runner.copy(src=fname, dest='/etc/awx/license', owner='awx', group='awx', mode='0600')

    def teardown():
        log.debug("calling teardown install_license_unlimited")
        ansible_runner.file(path='/etc/awx/license', state='absent')
    request.addfinalizer(teardown)
