import os.path
import sys
import logging
import pytest
import common.tower.license


log = logging.getLogger(__name__)


@pytest.fixture(scope='session')
def tower_license_path(request, tower_config_dir):
    return os.path.join(tower_config_dir, 'license')


@pytest.fixture(scope='session')
def tower_aws_path(request, tower_config_dir):
    return os.path.join(tower_config_dir, 'aws')


@pytest.fixture(scope='class')
def backup_license(request, ansible_runner, tower_license_path, tower_aws_path):
    '''Backup and existing license files. The files will be restored upon teardown.
    '''
    log.debug("calling fixture backup_license")
    for license_file in (tower_license_path, tower_aws_path):
        ansible_runner.shell('mv {0} {0}.bak'.format(license_file), removes=license_file)

    def teardown():
        log.debug("calling teardown backup_license")
        for license_file in (tower_license_path, tower_aws_path):
            ansible_runner.shell('mv {0}.bak {0}'.format(license_file), removes=license_file + '.bak')
    request.addfinalizer(teardown)


@pytest.fixture(scope='class')
def install_license_1000(request, ansible_runner, tower_license_path):
    '''Install a license where instance_count=1000
    '''

    log.debug("calling fixture install_license_1000")
    fname = common.tower.license.generate_license_file(instance_count=1000, days=365)
    ansible_runner.copy(src=fname, dest=tower_license_path, owner='awx', group='awx', mode='0600')

    def teardown():
        log.debug("calling teardown install_license_1000")
        ansible_runner.file(path=tower_license_path, state='absent')
    request.addfinalizer(teardown)


@pytest.fixture(scope='class')
def install_license_10000(request, ansible_runner, tower_license_path):
    '''Install a license where instance_count=10000
    '''

    log.debug("calling fixture install_license_10000")
    fname = common.tower.license.generate_license_file(instance_count=10000, days=365)
    ansible_runner.copy(src=fname, dest=tower_license_path, owner='awx', group='awx', mode='0600')

    def teardown():
        log.debug("calling teardown install_license_10000")
        ansible_runner.file(path=tower_license_path, state='absent')
    request.addfinalizer(teardown)


@pytest.fixture(scope='class')
def install_license_unlimited(request, ansible_runner, tower_license_path):
    '''Install a license where instance_count=unlimited
    '''

    log.debug("calling fixture install_license_unlimited")
    fname = common.tower.license.generate_license_file(instance_count=sys.maxint, days=365)
    ansible_runner.copy(src=fname, dest=tower_license_path, owner='awx', group='awx', mode='0600')

    def teardown():
        log.debug("calling teardown install_license_unlimited")
        ansible_runner.file(path=tower_license_path, state='absent')
    request.addfinalizer(teardown)
