import re
import pytest
import logging


log = logging.getLogger(__name__)


@pytest.fixture(scope='session')
def tower_config_dir():
    return '/etc/tower'


# TODO - move this to pytest-ansible
@pytest.fixture(scope="function")
def ansible_os_family(request, ansible_facts):
    """Return ansible_os_family from the ansible_facts of the system under test."""
    if len(ansible_facts) > 1:
        log.warning("ansible_facts for %d systems found, but returning "
                    "only the first" % len(ansible_facts))
    return ansible_facts.values()[0]['ansible_facts']['ansible_os_family']


# TODO - move this to pytest-ansible
@pytest.fixture(scope="function")
def ansible_distribution_major_version(request, ansible_facts):
    """Return ansible_distribution_major_version from the ansible_facts of the system under test."""
    if len(ansible_facts) > 1:
        log.warning("ansible_facts for %d systems found, but returning "
                    "only the first" % len(ansible_facts))
    return ansible_facts.values()[0]['ansible_facts']['ansible_distribution_major_version']


@pytest.fixture(scope="function")
def restart_tower_on_teardown(request, ansible_runner, ansible_os_family, is_docker):
    """Restarts Tower upon teardown."""
    log.debug("calling fixture restart_tower")

    # FIXME: implement with Ubuntu systems
    if ansible_os_family == "Debian" or is_docker:
        pytest.skip("Only supported on production EL distributions")

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
