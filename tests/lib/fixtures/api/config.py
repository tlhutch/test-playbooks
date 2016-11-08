import re
import json
import pytest
import logging


log = logging.getLogger(__name__)


@pytest.fixture(scope='session')
def tower_config_dir():
    return '/etc/tower'


# TODO - move this to pytest-ansible
@pytest.fixture(scope="function")
def ansible_os_family(request, ansible_facts):
    '''Return ansible_os_family from the ansible_facts of the system under test.'''
    if len(ansible_facts) > 1:
        log.warning("ansible_facts for %d systems found, but returning "
                    "only the first" % len(ansible_facts))
    return ansible_facts.values()[0]['ansible_facts']['ansible_os_family']


# TODO - move this to pytest-ansible
@pytest.fixture(scope="function")
def ansible_distribution_major_version(request, ansible_facts):
    '''Return ansible_distribution_major_version from the ansible_facts of the system under test.'''
    if len(ansible_facts) > 1:
        log.warning("ansible_facts for %d systems found, but returning "
                    "only the first" % len(ansible_facts))
    return ansible_facts.values()[0]['ansible_facts']['ansible_distribution_major_version']


@pytest.fixture(scope="function")
def restart_tower_on_teardown(request, ansible_runner, ansible_os_family):
    '''Restarts Tower upon teardown.'''
    log.debug("calling fixture restart_tower")

    # FIXME: implement with Ubuntu systems
    if ansible_os_family == "Debian":
        pytest.skip("Only supported on EL distributions")

    def teardown():
        # determine Tower processes
        contacted = ansible_runner.shell('cat /etc/sysconfig/ansible-tower')
        stdout = contacted.values()[0]['stdout']
        match = re.search("TOWER_SERVICES=\"(.*?)\"", stdout)
        processes = match.group(1).split()

        # start Tower processes
        for process in processes:
            contacted = ansible_runner.service(name=process, state='started')
            result = contacted.values()[0]
            assert result['state'] == 'started', "Starting service %s failed." % process
    request.addfinalizer(teardown)


@pytest.fixture
def CUSTOM_CONSOLE_LOGO(request, ansible_runner):
    """Installs a custom console logo on our target host. Files transferred include the image itself
    and a settings file. Files are removed upon teardown.
    """
    # install custom_console_logo.png
    contacted = ansible_runner.copy(
        src='tests/lib/fixtures/api/static/custom_console_logo.png',
        dest='/var/lib/awx/public/static/assets/custom_console_logo.png',
        owner='awx',
        group='awx',
        mode='0755'
    )

    # assert success
    for result in contacted.values():
        assert 'failed' not in result, \
            "Failure installing custom_console_logo.png.\n%s" % json.dumps(result, indent=2)

    # install local_settings.json
    contacted = ansible_runner.copy(
        src='tests/lib/fixtures/api/static/local_settings.json',
        dest='/var/lib/awx/public/static/local_settings.json',
        owner='awx',
        group='awx',
        mode='0755'
    )

    # assert success
    for result in contacted.values():
        assert 'failed' not in result, \
            "Failure installing local_settings.json.\n%s" % json.dumps(result, indent=2)

    def fin():
        # remove custom_console_logo.png
        contacted = ansible_runner.file(
            path='/var/lib/awx/public/static/assets/custom_console_logo.png',
            state='absent'
        )

        # assert success
        for result in contacted.values():
            assert 'failed' not in result, \
                "Failure removing custom_console_logo.png.\n%s" % json.dumps(result, indent=2)

        # remove local_settings.json
        contacted = ansible_runner.file(
            path='/var/lib/awx/public/static/local_settings.json',
            state='absent'
        )

        # assert success
        for result in contacted.values():
            assert 'failed' not in result, \
                "Failure removing local_settings.json.\n%s" % json.dumps(result, indent=2)
    request.addfinalizer(fin)
