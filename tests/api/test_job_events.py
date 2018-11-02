from collections import Counter
import json

import pytest

from tests.api import APITest


# from https://github.com/ansible/ansible-tower/blob/release_3.1.0/awx/main/models/jobs.py
# note: Doesn't include `verbose`
JOB_EVENT_TYPES = ['playbook_on_start',  # (once for each playbook file)
                   'playbook_on_vars_prompt',  # (for each play, but before play starts, we
                                               #  currently don't handle responding to these prompts)
                   'playbook_on_play_start',   # (once for each play)
                   'playbook_on_import_for_host',  # (not logged, not used for v2)
                   'playbook_on_not_import_for_host',  # (not logged, not used for v2)
                   'playbook_on_no_hosts_matched',
                   'playbook_on_no_hosts_remaining',
                   'playbook_on_include',  # (only v2 - only used for handlers?)
                   'playbook_on_setup',  # (not used for v2)
                   'playbook_on_task_start',  # (once for each task within a play)
                   'runner_on_failed',
                   'runner_on_ok',
                   'runner_on_error',  # (not used for v2)
                   'runner_on_skipped',
                   'runner_on_unreachable',
                   'runner_on_no_hosts',  # (not used for v2)
                   'runner_on_async_poll',  # (not used for v2)
                   'runner_on_async_ok',  # (not used for v2)
                   'runner_on_async_failed',  # (not used for v2)
                   'runner_on_file_diff',  # (v2 event is v2_on_file_diff)
                   'runner_item_on_ok',  # (v2 only)
                   'runner_item_on_failed',  # (v2 only)
                   'runner_item_on_skipped',  # (v2 only)
                   'runner_retry',  # (v2 only)
                   'playbook_on_notify',  # (once for each notification from the play, not used for v2)
                   'playbook_on_stats']


@pytest.mark.api
@pytest.mark.destructive
@pytest.mark.usefixtures('authtoken', 'install_enterprise_license_unlimited')
class Test_Job_Events(APITest):

    def get_job_events(self, job, query=None):
        query = query if query else {}
        query['page_size'] = 200
        events = []
        job_events = job.related.job_events.get(**query)
        while True:
            events.extend(job_events.results)
            if not job_events.next:
                return events
            job_events = job_events.next.get()

    def get_job_events_by_event_type(self, job, event_type):
        return self.get_job_events(job, dict(event__icontains=event_type))

    def verify_desired_tasks(self, job, job_event_type, desired_tasks):
        event_tasks = Counter(map(lambda x: x.task, self.get_job_events_by_event_type(job, job_event_type)))
        assert event_tasks == desired_tasks

    def verify_desired_stdout(self, job, job_event_type, desired_stdout_contents):
        desired_stdout = list(desired_stdout_contents)
        actual_stdout = map(lambda x: x.stdout, self.get_job_events_by_event_type(job, job_event_type))
        for actual in list(actual_stdout):
            for desired in list(desired_stdout):
                if desired in actual:
                    actual_stdout.remove(actual)
                    desired_stdout.remove(desired)
                    break
        assert not actual_stdout, "Not all event stdout was expected."
        assert not desired_stdout, "Not all expected stdout was included."

    pytestmark = pytest.mark.usefixtures('authtoken', 'install_enterprise_license_unlimited')

    @pytest.mark.ansible_integration
    def test_dynamic_inventory(self, factories, ansible_version_cmp):
        """Launch a linear playbook of several plays and confirm desired events are at its related job events"""
        # ensure desired verbose events regarding authentication
        cred = factories.credential(password='passphrase')
        host = factories.v2_host()
        jt = factories.job_template(credential=cred,
                                    inventory=host.ds.inventory,
                                    playbook='dynamic_inventory.yml',
                                    extra_vars=json.dumps(dict(num_hosts=5)))
        job = jt.launch().wait_until_completed(interval=20)

        playbook_on_start = self.get_job_events_by_event_type(job, 'playbook_on_start')
        assert len(playbook_on_start) == 1

        playbook_on_play_start = set(map(lambda x: x.play,
                                         self.get_job_events_by_event_type(job, 'playbook_on_play_start')))
        desired_play_names = set(("add hosts to inventory",
                                  "various task responses on dynamic inventory",
                                  "shrink inventory to 1 host",
                                  "1 host play",
                                  "fail remaining dynamic group",
                                  "add hosts to inventory",
                                  "some unreachable, some changed, some skipped",
                                  "gather facts fail",
                                  "some gather facts fail",
                                  "no tasks, just the facts"))
        # "skipping: no hosts matched" message restored in 2.3:
        # https://github.com/ansible/ansible/issues/17706
        if ansible_version_cmp('2.3') >= 0 or ansible_version_cmp('2.2') < 0:
            desired_play_names.add("no matching hosts")
        assert playbook_on_play_start == desired_play_names

        # playbook_on_task_start incorrectly used 'setup' instead of 'Gathering Facts' before 2.2:
        # https://github.com/ansible/ansible/pull/16168
        if ansible_version_cmp('2.3') >= 0:
            gathering_facts_task_name = "Gathering Facts"
        else:
            gathering_facts_task_name = "setup"

        playbook_on_task_start = set(map(lambda x: (x.play, x.task),
                                         self.get_job_events_by_event_type(job, 'playbook_on_task_start')))
        desired_play_task_tuples = set((("add hosts to inventory", gathering_facts_task_name),
                                        ("add hosts to inventory", "create inventory"),
                                        ("add hosts to inventory", "single host handler"),
                                        ("various task responses on dynamic inventory", gathering_facts_task_name),
                                        ("various task responses on dynamic inventory", "fail even numbered hosts"),
                                        ("various task responses on dynamic inventory", "skip multiples of 3"),
                                        ("various task responses on dynamic inventory", "all skipped"),
                                        ("various task responses on dynamic inventory", "all changed"),
                                        ("various task responses on dynamic inventory", "all ok"),
                                        ("various task responses on dynamic inventory", "changed handler"),
                                        ("various task responses on dynamic inventory", "another changed handler"),
                                        ("shrink inventory to 1 host", gathering_facts_task_name),
                                        ("shrink inventory to 1 host", "fail all but 1"),
                                        ("1 host play", "pass"),
                                        ("1 host play", "ok"),
                                        ("1 host play", "ignored"),
                                        ("fail remaining dynamic group", gathering_facts_task_name),
                                        ("fail remaining dynamic group", "fail"),
                                        ("add hosts to inventory", "add dynamic inventory"),
                                        ("add hosts to inventory", "add unreachable inventory"),
                                        ("add hosts to inventory", "add more_unreachable inventory"),
                                        ("some unreachable, some changed, some skipped", "all changed with items"),
                                        ("gather facts fail", gathering_facts_task_name),
                                        ("some gather facts fail", gathering_facts_task_name),
                                        ("some gather facts fail", "skip this task"),
                                        ("no tasks, just the facts", gathering_facts_task_name),
                                        ("some gather facts fail", "skip this task")))

        assert playbook_on_task_start == desired_play_task_tuples

        task_counts = {"fail even numbered hosts": 2,
                       "fail all but 1": 2,
                       "ignored": 1,
                       "fail": 1}
        self.verify_desired_tasks(job, 'runner_on_failed', task_counts)

        task_counts = {gathering_facts_task_name: 17,
                       "another changed handler": 3,
                       "all changed": 3,
                       "changed handler": 3,
                       "all ok": 3,
                       "skip multiples of 3": 2,
                       "ok": 1,
                       "create inventory": 1,
                       "add unreachable inventory": 1,
                       "add dynamic inventory": 1,
                       "add more_unreachable inventory": 1,
                       "pass": 1,
                       "single host handler": 1}
        self.verify_desired_tasks(job, 'runner_on_ok', task_counts)

        task_counts = {"all changed with items": 4,
                       "fail even numbered hosts": 3,
                       "all skipped": 3,
                       "skip this task": 2,
                       "fail all but 1": 1,
                       "skip multiples of 3": 1,
                       "fail": 1}
        self.verify_desired_tasks(job, 'runner_on_skipped', task_counts)

        task_counts = {gathering_facts_task_name: 5,
                       "all changed with items": 1}
        self.verify_desired_tasks(job, 'runner_on_unreachable', task_counts)

        task_counts = {"create inventory": 5,
                       "add unreachable inventory": 3,
                       "add more_unreachable inventory": 3,
                       "add dynamic inventory": 2}
        self.verify_desired_tasks(job, 'runner_item_on_ok', task_counts)

        desired_stdout_contents = ["SSH password:", "Identity added:", "SUDO password"]
        # https://github.com/ansible/tower/issues/1441
        if ansible_version_cmp('2.5.1') == 0:
            desired_stdout_contents.extend([' [ERROR]:', ''])
        if ansible_version_cmp('2.8.0') >= 0:
            desired_stdout_contents = ["SSH password:", "Identity added:", "BECOME password"]
        self.verify_desired_stdout(job, 'verbose', desired_stdout_contents)

        assert len(self.get_job_events_by_event_type(job, 'playbook_on_stats')) == 1

        events = self.get_job_events(job)
        non_verbose = filter(lambda x: x.event != 'verbose', events)
        assert not filter(lambda x: not x.uuid, non_verbose)
        assert not filter(lambda x: x.playbook != 'dynamic_inventory.yml', non_verbose)

    @pytest.mark.ansible_integration
    def test_async_tasks(self, factories, ansible_version_cmp):
        """Runs a single play with async tasks and confirms desired events at related endpoint"""
        credential = factories.credential(password='passphrase')
        inventory = factories.inventory()
        for _ in range(5):
            factories.host(inventory=inventory)
        jt = factories.job_template(credential=credential,
                                    inventory=inventory,
                                    playbook='async_tasks.yml')
        job = jt.launch().wait_until_completed(interval=20)
        assert job.is_successful

        playbook_on_start = self.get_job_events_by_event_type(job, 'playbook_on_start')
        assert len(playbook_on_start) == 1

        playbook_on_play_start = map(lambda x: x.play, self.get_job_events_by_event_type(job, 'playbook_on_play_start'))
        assert playbook_on_play_start == ['all']

        task_counts = {"debug": 3,
                       "Examine slow command": 1,
                       "Examine slow reversal": 1,
                       "Poll a sleep": 1,
                       "Fire and forget a slow command": 1,
                       "Fire and forget a slow reversal": 1}
        self.verify_desired_tasks(job, 'playbook_on_task_start', task_counts)

        task_counts = {"debug": 15,
                       "Examine slow command": 5,
                       "Examine slow reversal": 5,
                       "Poll a sleep": 5,
                       "Fire and forget a slow command": 5,
                       "Fire and forget a slow reversal": 5}
        self.verify_desired_tasks(job, 'runner_on_ok', task_counts)

        # asserted retry counts are a major source of flake, so just confirm that retries happened
        runner_retry_tasks = set(map(lambda x: x.task, self.get_job_events_by_event_type(job, 'runner_retry')))
        assert runner_retry_tasks == {"Examine slow command", "Examine slow reversal"}

        assert len(self.get_job_events_by_event_type(job, 'playbook_on_stats')) == 1

        desired_stdout_contents = ["SSH password:", "Identity added:", "SUDO password"]
        # https://github.com/ansible/tower/issues/1441
        if ansible_version_cmp('2.5.1') == 0:
            desired_stdout_contents.extend([' [ERROR]:', ''])
        if ansible_version_cmp('2.8.0') >= 0:
            desired_stdout_contents = ["SSH password:", "Identity added:", "BECOME password"]
        self.verify_desired_stdout(job, 'verbose', desired_stdout_contents)

        events = self.get_job_events(job)
        non_verbose = filter(lambda x: x.event != 'verbose', events)
        assert not filter(lambda x: not x.uuid, non_verbose)
        assert not filter(lambda x: x.playbook != 'async_tasks.yml', non_verbose)

    @pytest.mark.ansible_integration
    def test_free_strategy(self, factories, ansible_version_cmp):
        """Runs a single play with free strategy and confirms desired events at related endpoint"""
        credential = factories.credential(password='passphrase')
        inventory = factories.inventory()
        for _ in range(5):
            factories.host(inventory=inventory)
        jt = factories.job_template(credential=credential,
                                    inventory=inventory,
                                    playbook='free_waiter.yml')
        job = jt.launch().wait_until_completed(interval=20)
        assert job.is_successful

        playbook_on_start = self.get_job_events_by_event_type(job, 'playbook_on_start')
        assert len(playbook_on_start) == 1

        playbook_on_play_start = map(lambda x: x.play, self.get_job_events_by_event_type(job, 'playbook_on_play_start'))
        assert playbook_on_play_start == ['all']

        task_counts = {"debug": 11,
                       "wait_for": 10,
                       "set_fact": 10}
        self.verify_desired_tasks(job, 'playbook_on_task_start', task_counts)

        task_counts = {"debug": 55,
                       "wait_for": 50,
                       "set_fact": 50}
        self.verify_desired_tasks(job, 'runner_on_ok', task_counts)

        assert len(self.get_job_events_by_event_type(job, 'playbook_on_stats')) == 1

        desired_stdout_contents = ["SSH password:", "Identity added:", "SUDO password"]
        # https://github.com/ansible/tower/issues/1441
        if ansible_version_cmp('2.5.1') == 0:
            desired_stdout_contents.extend([' [ERROR]:', ''])
        if ansible_version_cmp('2.8.0') >= 0:
            desired_stdout_contents = ["SSH password:", "Identity added:", "BECOME password"]
        self.verify_desired_stdout(job, 'verbose', desired_stdout_contents)

        events = self.get_job_events(job)
        non_verbose = filter(lambda x: x.event != 'verbose', events)
        assert not filter(lambda x: not x.uuid, non_verbose)
        assert not filter(lambda x: x.playbook != 'free_waiter.yml', non_verbose)

    @pytest.mark.ansible_integration
    def test_no_log(self, ansible_version_cmp, factories):
        """Runs Ansible's no_log integration test playbook and confirms Tower's callback receiver offers
        near equivalent censoring.
        """
        if ansible_version_cmp('2.4.0.0') < 0:
            pytest.skip('no_log_local.yml uses loop syntax. Requires ansible >= 2.4')
        host = factories.host(name='testhost')
        project = factories.project(scm_url='https://github.com/ansible/ansible.git')
        jt = factories.job_template(project=project, playbook='test/integration/targets/no_log/no_log_local.yml',
                                    inventory=host.ds.inventory, verbosity=1)

        job = jt.launch().wait_until_completed()
        assert not job.is_successful
        assert job.status == 'failed'

        playbook_on_task_start = self.get_job_events_by_event_type(job, 'playbook_on_task_start')
        task_start_task_args = map(lambda x: x.event_data.get('task_args', ''), playbook_on_task_start)
        assert not filter(lambda task_args: 'DO_NOT_LOG' in task_args, task_start_task_args)

        events = self.get_job_events_by_event_type(job, 'runner')
        assert not filter(lambda event: 'DO_NOT_LOG' in event.stdout, events)
        assert not filter(lambda data: 'DO_NOT_LOG' in data.task_args, map(lambda event: event.event_data, events))

        hidden_prefix = 'the output has been hidden'
        for event in events:
            data = event.event_data
            if 'res' not in data:
                if event.event != 'runner_on_skipped':
                    raise(Exception('Unexpected lack of result in event_data: {0}'.format(event)))
                continue
            if 'results' in data.res:
                results = data.res.results
            else:
                results = [data.res]

            if ansible_version_cmp('2.4.3.0') >= 0:  # should match whitelist at ansible/lib/ansible/executor/task_result.py
                desired_result_keys = {'censored', 'attempts', 'changed', 'retries', 'failed', 'unreachable', 'skipped'}
            else:
                desired_result_keys = {'censored'}

            for result in results:
                # task_args not shown unless DISPLAY_ARGS_TO_STDOUT is True (default is False)
                # https://github.com/ansible/tower/pull/1195/files
                # https://docs.ansible.com/ansible/2.4/intro_configuration.html#display-args-to-stdout
                assert data.task_args == ''
                if result.get('_ansible_no_log') is False:
                    assert 'censored' not in data.res
                    result = data.res.get('result', data.res)
                    assert hidden_prefix not in result.get('cmd', '')
                    assert hidden_prefix not in result.get('stdout', '')
                    assert hidden_prefix not in result.get('stdout_lines', '')
                else:
                    assert set(result.keys()) | desired_result_keys == desired_result_keys
                    assert hidden_prefix in result.censored

    def test_warning_statements_absent_with_include_role_playbook(self, factories, ansible_version_cmp):
        # context: https://github.com/ansible/ansible-tower/issues/7829
        if ansible_version_cmp('2.4.2.0') == 0:
            pytest.skip('Known regression under Ansible-2.4.2.0')

        jt = factories.v2_job_template(playbook='test_include_role.yml')
        job = jt.launch().wait_until_completed()
        assert job.is_successful

        assert job.related.job_events.get(event='warning').count == 0

    def test_playbook_on_notify(self, factories, ansible_version_cmp):
        if ansible_version_cmp('2.5.0.0') < 0:
            pytest.skip('playbook_on_notify does not work _at all_ prior to Ansible 2.5')
        host = factories.v2_host()
        jt = factories.v2_job_template(playbook='handler.yml', inventory=host.ds.inventory)
        job = jt.launch().wait_until_completed()
        assert job.is_successful
        assert job.related.job_events.get(event='playbook_on_notify').count == 1

    def test_long_task_name_is_truncated(self, factories, ansible_version_cmp):
        # Our event models support a max of 1024 characters; we should truncate after that
        host = factories.v2_host()
        jt = factories.v2_job_template(playbook='long_task_name.yml', inventory=host.ds.inventory)
        job = jt.launch().wait_until_completed()
        assert job.is_successful
        on_ok = job.related.job_events.get(event='runner_on_ok')
        assert on_ok.count == 1
        task = on_ok.results.pop()['task']
        assert len(task) == 1024
        assert task.endswith('...')
