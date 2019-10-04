import logging
import re

import pytest
from awxkit.utils import poll_until

from tests.api import APITest


log = logging.getLogger(__name__)


@pytest.mark.usefixtures(
    'skip_if_openshift',
    'authtoken',
)
@pytest.mark.serial
class TestDispatcher(APITest):

    def runner_output(self, result):
        return "stdout:\n\n{0[stdout]}\n\nstderr:\n{0[stderr]}".format(result)

    @pytest.fixture(scope="function")
    def run_remote_command(self, ansible_runner):
        def _run_remote_command(cmd):
            contacted = ansible_runner.command(cmd)
            result = list(contacted.values())[0]
            assert result['rc'] == 0, "{0} failed. {1}".format(cmd, self.runner_output(result))
            return result
        return _run_remote_command

    @pytest.fixture(scope="function")
    def kill_process(self, run_remote_command, process_present):
        def _kill_process(pid):
            if type(pid) != list:
                pid = [pid]
            run_remote_command('kill -9 {}'.format(' '.join([str(p) for p in pid])))
            poll_until(lambda: not process_present(pid), timeout=60)
        return _kill_process

    @pytest.fixture(scope="function")
    def process_present(self, run_remote_command):
        """
        Given a process (or list of processes), returns list of any processes that were found.
        """
        def _process_present(pid):
            if type(pid) != list:
                pid = [pid]
            result = run_remote_command('ps -A -o pid')
            present = []
            for p in pid:
                if str(p) in result['stdout_lines']:
                    present.append(p)
            return present
        return _process_present

    @pytest.fixture(scope="function")
    def get_dispatcher_pids(self, run_remote_command):
        def _get_dispatcher_pids():
            """
            Returns tuple containing:
              * PID of parent process
              * list of PIDs of dispatcher's child processes
            """
            result = run_remote_command('awx-manage run_dispatcher --status')
            for line in result['stdout_lines']:
                matches = re.search(r'\[pid:(\d+)\] workers', line)
                if matches:
                    parent_pid = matches.group(1)
                    break
            else:
                raise Exception('Could not locate parent PID in dispatcher output.\n\n{}'
                                .format(self.runner_output(result)))
            child_pids = []
            for line in result['stdout_lines']:
                matches = re.search(r'worker\[pid:(\d+)\]', line)
                if matches:
                    child_pids.append(matches.group(1))
            return (parent_pid, child_pids)
        return _get_dispatcher_pids

    def test_dispatcher_graceful_restart(self, factories, v2, run_remote_command):
        jt = factories.job_template(playbook='sleep.yml',
                                       extra_vars=dict(sleep_interval=30))
        jt.ds.inventory.add_host()
        self.ensure_jt_runs_on_primary_instance(jt, v2)
        job = jt.launch().wait_until_status('running')

        try:
            run_remote_command('supervisorctl stop tower-processes:awx-dispatcher')
            job.wait_until_status('failed', since_job_created=False, timeout=240)
            assert job.job_explanation == 'Task was marked as running in Tower but was not present in the job queue, so it has been marked as failed.'
        finally:
            run_remote_command('supervisorctl start tower-processes:awx-dispatcher')

        jt.extra_vars = '{"sleep_interval": 1}'
        job = jt.launch().wait_until_completed()
        job.assert_successful()

    def test_dispatcher_hard_restart(self, factories, v2, run_remote_command):
        jt = factories.job_template(playbook='sleep.yml',
                                       extra_vars=dict(sleep_interval=30))
        jt.ds.inventory.add_host()
        self.ensure_jt_runs_on_primary_instance(jt, v2)
        job = jt.launch().wait_until_status('running')

        # kill all dispatcher processes, supervisorctl immediately restarts dispatcher
        run_remote_command("pkill -f --signal 9 run_dispatcher")

        # when dispatcher restarts, it reaps the running job
        job.wait_until_status('failed', since_job_created=False)
        assert job.job_explanation == 'Task was marked as running in Tower but was not present in the job queue, so it has been marked as failed.'

        try:
            result = run_remote_command('supervisorctl status tower-processes:awx-dispatcher')
            assert 'running' in result['stdout'].lower(), "supervisorctl failed to restart dispatcher. {0}".format(self.runner_output(result))
        except:
            # restart dispatcher if necessary
            # do not expect this to be needed; supervisor should automatically restart dispatcher
            run_remote_command('supervisorctl start tower-processes:awx-dispatcher')
            raise

        jt.extra_vars = '{"sleep_interval": 1}'
        job = jt.launch().wait_until_completed()
        job.assert_successful()

    def test_kill_dispatcher_child_process_executing_job(self, factories, v2, run_remote_command, kill_process,
                                                         get_dispatcher_pids):

        def get_worker_running_job(job_id):
            """
            awx-manage run_dispatcher --status returns status of dispatcher child processes. For example:

            .  worker[pid:8688] sent=688 finished=687 qsize=1 rss=109.848MB
                 - running 36ff5e4a-1946-40a5-8770-3b379addb54e RunJob(*[43])

            Find pid of worker running given job.
            """
            result = run_remote_command('awx-manage run_dispatcher --status')

            worker_description = ''
            for i, line in enumerate(result['stdout_lines']):
                if re.search(r'RunJob\([^\)]*{}[^\)]*\)'.format(job.id), line):
                    worker_description = result['stdout_lines'][i - 1]
                    break
            else:
                raise Exception('Unable to find worker running job {0}\n\nawx_manage run_dispatcher --status shows:\n{1}'
                                .format(job.id, result['stdout_lines']))

            matches = re.search(r'\[pid:(\d+)]', worker_description)
            return matches.group(1)

        jt = factories.job_template(playbook='sleep.yml', extra_vars='{"sleep_interval": 120}')
        jt.ds.inventory.add_host()

        self.ensure_jt_runs_on_primary_instance(jt, v2)
        job = jt.launch()

        _, worker_pids_before = get_dispatcher_pids()
        pid = get_worker_running_job(job.id)
        kill_process(pid)
        _, worker_pids_after = get_dispatcher_pids()
        assert pid not in worker_pids_after

        poll_until(lambda: job.get().status == 'failed', timeout=30)

        jt.extra_vars = '{"sleep_interval": 1}'
        job = jt.launch().wait_until_completed()
        job.assert_successful()

    def test_kill_all_dispatcher_child_processes(self, v2, factories, run_remote_command, get_dispatcher_pids, kill_process):
        _, pids_before = get_dispatcher_pids()
        kill_process(pids_before)

        def processes_respawned():
            _, pids = get_dispatcher_pids()
            if len(pids) != 4:
                assert len(pids) < len(pids_before)
                return False
            return True
        poll_until(processes_respawned, timeout=90)

        jt = factories.job_template()
        jt.ds.inventory.add_host()
        self.ensure_jt_runs_on_primary_instance(jt, v2)
        job = jt.launch().wait_until_completed()
        job.assert_successful()

    def test_kill_dispatcher_parent_process(self, factories, v2, get_dispatcher_pids, kill_process, process_present):
        parent_pid, child_pids = get_dispatcher_pids()
        kill_process(parent_pid)
        assert not process_present([parent_pid] + child_pids)

        def processes_respawned():
            _, pids = get_dispatcher_pids()
            if len(pids) != 4:
                assert len(pids) < len(child_pids)
                return False
            return True
        poll_until(processes_respawned, timeout=60)

        jt = factories.job_template()
        jt.ds.inventory.add_host()
        self.ensure_jt_runs_on_primary_instance(jt, v2)
        job = jt.launch().wait_until_completed()
        job.assert_successful()
