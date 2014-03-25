import logging
import pytest
import common.tower.license

# The following fixture runs once for this entire module
@pytest.fixture(scope='module')
def backup_license(request, ansible_runner):
    '''Backup and existing license files. The files will be restored upon teardown.
    '''
    logging.debug("calling fixture backup_license")
    ansible_runner.shell('test -f /etc/awx/aws && mv /etc/awx/aws /etc/awx/.aws', creates='/etc/awx/.aws', removes='/etc/awx/aws')
    ansible_runner.shell('test -f /etc/awx/license && mv /etc/awx/license /etc/awx/.license', creates='/etc/awx/.license', removes='/etc/awx/license')

    def teardown():
        ansible_runner.shell('test -f /etc/awx/.aws && mv /etc/awx/.aws /etc/awx/aws', creates='/etc/awx/aws', removes='/etc/awx/.aws')
        ansible_runner.shell('test -f /etc/awx/.license && mv /etc/awx/.license /etc/awx/license', creates='/etc/awx/license', removes='/etc/awx/.license')
    request.addfinalizer(teardown)

@pytest.fixture(scope='module')
def install_license_1000(request, ansible_runner):
    '''Install a license where instance_count=1000
    '''

    logging.debug("calling fixture install_license_1000")
    fname = common.tower.license.generate_license_file(instance_count=1000, days=365)
    ansible_runner.copy(src=fname, dest='/etc/awx/license', owner='awx', group='awx', mode='0600')

    def teardown():
        ansible_runner.file(path='/etc/awx/license', state='absent')
    request.addfinalizer(teardown)

@pytest.fixture(scope='module')
def install_license_10000(request, ansible_runner):
    '''Install a license where instance_count=1000
    '''

    logging.debug("calling fixture install_license_10000")
    fname = common.tower.license.generate_license_file(instance_count=10000, days=365)
    ansible_runner.copy(src=fname, dest='/etc/awx/license', owner='awx', group='awx', mode='0600')

    def teardown():
        ansible_runner.file(path='/etc/awx/license', state='absent')
    request.addfinalizer(teardown)
