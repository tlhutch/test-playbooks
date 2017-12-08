import pytest
import re
import logging
from tests.api import Base_Api_Test


log = logging.getLogger(__name__)


@pytest.mark.api
@pytest.mark.skip_selenium
@pytest.mark.destructive
@pytest.mark.second_to_last
@pytest.mark.mp_group('AnsibleTowerService', 'isolated_serial')
class Test_Ansible_Tower_Service(Base_Api_Test):
    """Executes ansible-tower-service commands and checks process statuses.
    Note: we check process output with systemctl on EL7 systems and with
    service on EL6 systems. Did not implement with Ubuntu because of the
    following:
    * On Ubuntu systems, ansible-tower-service status sometimes incorrectly
    reports the status of redis-server.
    * On Ubuntu systems, rapidly restarting supervisor can leave your system
    in an indeterminate state.
    """

    pytestmark = pytest.mark.usefixtures('authtoken')

    @pytest.mark.parametrize("command, expected_process_status", [
        ("start", "Active: active (running)"),
        ("stop", "Active: inactive (dead)"),
        ("restart", "Active: active (running)"),
        ("status", "Active: active (running)")
    ], ids=['ansible-tower-service start', 'ansible-tower-service stop', 'ansible-tower-service restart', 'ansible-tower-service status'])
    def test_tower_status_on_el7(self, ansible_runner, ansible_os_family, ansible_distribution_major_version,
                                 restart_tower_on_teardown, command, expected_process_status):
        """Execute ansible-tower-service commands and check process statuses."""
        # check that Tower is running on an EL7 system
        if not (ansible_os_family == 'RedHat' and ansible_distribution_major_version == '7'):
            pytest.skip("Only supported on EL7 distributions")

        # issue ansible-tower-service command
        contacted = ansible_runner.command('ansible-tower-service ' + command)
        result = contacted.values()[0]
        assert result['rc'] == 0, "ansible-tower-service %s failed. Command stderr: \n%s" % (command, result['stderr'])

        # determine expected_processes
        contacted = ansible_runner.shell('cat /etc/sysconfig/ansible-tower')
        stdout = contacted.values()[0]['stdout']
        match = re.search("TOWER_SERVICES=\"(.*?)\"", stdout)
        processes = match.group(1).split()

        # assess process statuses
        for process in processes:
            contacted = ansible_runner.command('systemctl status %s' % process)
            result = contacted.values()[0]
            assert expected_process_status in result['stdout'], \
                "Unexpected process status for process %s after executing ansible-tower-service %s" % (process, command)

    @pytest.mark.parametrize("command, expected_process_status", [
        ("start", "is running"),
        ("stop", "is stopped"),
        ("restart", "is running"),
        ("status", "is running")
    ], ids=['ansible-tower-service start', 'ansible-tower-service stop', 'ansible-tower-service restart', 'ansible-tower-service status'])
    def test_tower_status_on_el6(self, ansible_runner, ansible_os_family, ansible_distribution_major_version,
                                 restart_tower_on_teardown, command, expected_process_status):
        """Execute ansible-tower-service commands and check process statuses."""
        # check that Tower is running on an EL6 system
        if not (ansible_os_family == 'RedHat' and ansible_distribution_major_version == '6'):
            pytest.skip("Only supported on EL6 distributions")

        # issue ansible-tower-service command
        contacted = ansible_runner.command('ansible-tower-service ' + command)
        result = contacted.values()[0]
        assert result['rc'] == 0, "ansible-tower-service %s failed. Command stderr: \n%s" % (command, result['stderr'])

        # determine expected_processes
        contacted = ansible_runner.shell('cat /etc/sysconfig/ansible-tower')
        stdout = contacted.values()[0]['stdout']
        match = re.search("TOWER_SERVICES=\"(.*?)\"", stdout)
        processes = match.group(1).split()

        # assess process statuses
        for process in processes:
            contacted = ansible_runner.command('service %s status' % process)
            result = contacted.values()[0]
            assert expected_process_status in result['stdout'], \
                "Unexpected process status for process %s after executing ansible-tower-service %s" % (process, command)
