from collections import Counter
import json

import pytest

from tests.api import Base_Api_Test


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
@pytest.mark.skip_selenium
@pytest.mark.destructive
class Test_Job_Events(Base_Api_Test):

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
        return self.get_job_events(job, dict(event=event_type))

    def verify_desired_tasks(self, job, job_event_type, desired_tasks):
        event_tasks = Counter(map(lambda x: x.task, self.get_job_events_by_event_type(job, job_event_type)))
        assert(event_tasks == desired_tasks)

    def verify_desired_stdout(self, job, job_event_type, desired_stdout_contents):
        desired_stdout = list(desired_stdout_contents)
        actual_stdout = map(lambda x: x.stdout, self.get_job_events_by_event_type(job, job_event_type))
        for actual in list(actual_stdout):
            for desired in list(desired_stdout):
                if desired in actual:
                    actual_stdout.remove(actual)
                    desired_stdout.remove(desired)
                    break
        assert(not actual_stdout), "Not all event stdout was expected."
        assert(not desired_stdout), "Not all expected stdout was included."

    pytestmark = pytest.mark.usefixtures('authtoken', 'install_enterprise_license_unlimited')

    def test_dynamic_inventory(self, factories):
        """Launch a linear playbook of several plays and confirm desired events are at its related job events"""
        # ensure desired verbose events regarding authentication
        cred = factories.credential(password='passphrase', vault_password='vault')
        jt = factories.job_template(credential=cred,
                                    playbook='dynamic_inventory.yml',
                                    extra_vars=json.dumps(dict(num_hosts=5)))
        job = jt.launch().wait_until_completed(interval=20)

        playbook_on_start = self.get_job_events_by_event_type(job, 'playbook_on_start')
        assert(len(playbook_on_start) == 1)

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
        assert(playbook_on_play_start == desired_play_names)

        playbook_on_task_start = set(map(lambda x: (x.play, x.task),
                                         self.get_job_events_by_event_type(job, 'playbook_on_task_start')))
        desired_play_task_tuples = set((("add hosts to inventory", "setup"),
                                        ("add hosts to inventory", "create inventory"),
                                        ("add hosts to inventory", "single host handler"),
                                        ("various task responses on dynamic inventory", "setup"),
                                        ("various task responses on dynamic inventory", "fail even numbered hosts"),
                                        ("various task responses on dynamic inventory", "skip multiples of 3"),
                                        ("various task responses on dynamic inventory", "all skipped"),
                                        ("various task responses on dynamic inventory", "all changed"),
                                        ("various task responses on dynamic inventory", "all ok"),
                                        ("various task responses on dynamic inventory", "changed handler"),
                                        ("various task responses on dynamic inventory", "another changed handler"),
                                        ("shrink inventory to 1 host", "setup"),
                                        ("shrink inventory to 1 host", "fail all but 1"),
                                        ("1 host play", "pass"),
                                        ("1 host play", "ok"),
                                        ("1 host play", "ignored"),
                                        ("fail remaining dynamic group", "setup"),
                                        ("fail remaining dynamic group", "fail"),
                                        ("add hosts to inventory", "add dynamic inventory"),
                                        ("add hosts to inventory", "add unreachable inventory"),
                                        ("add hosts to inventory", "add more_unreachable inventory"),
                                        ("some unreachable, some changed, some skipped", "all changed with items"),
                                        ("gather facts fail", "setup"),
                                        ("some gather facts fail", "setup"),
                                        ("some gather facts fail", "skip this task"),
                                        ("no tasks, just the facts", "setup")))
        assert(playbook_on_task_start == desired_play_task_tuples)

        task_counts = {"fail even numbered hosts": 2,
                       "fail all but 1": 2,
                       "ignored": 1,
                       "fail": 1}
        self.verify_desired_tasks(job, 'runner_on_failed', task_counts)

        task_counts = {"setup": 17,
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

        task_counts = {"setup": 5,
                       "all changed with items": 1}
        self.verify_desired_tasks(job, 'runner_on_unreachable', task_counts)

        task_counts = {"create inventory": 5,
                       "add unreachable inventory": 3,
                       "add more_unreachable inventory": 3,
                       "add dynamic inventory": 2}
        self.verify_desired_tasks(job, 'runner_item_on_ok', task_counts)

        desired_stdout_contents = ["SSH password:", "Identity added:", "Vault password:", "SUDO password"]
        self.verify_desired_stdout(job, 'verbose', desired_stdout_contents)

        assert(len(self.get_job_events_by_event_type(job, 'playbook_on_stats')) == 1)

        events = self.get_job_events(job)
        assert(len(events) == 121)

        non_verbose = filter(lambda x: x.event != 'verbose', events)
        assert(not filter(lambda x: not x.uuid, non_verbose))
        assert(not filter(lambda x: x.playbook != 'dynamic_inventory.yml', non_verbose))

    def test_async_tasks(self, factories):
        """Runs a single play with async tasks and confirms desired events at related endpoint"""
        credential = factories.credential(password='passphrase', vault_password='vault')
        inventory = factories.inventory()
        for _ in range(4):
            factories.host(inventory=inventory)
        jt = factories.job_template(credential=credential,
                                    inventory=inventory,
                                    playbook='async_tasks.yml')
        job = jt.launch().wait_until_completed(interval=20)
        assert(job.is_successful)

        playbook_on_start = self.get_job_events_by_event_type(job, 'playbook_on_start')
        assert(len(playbook_on_start) == 1)

        playbook_on_play_start = map(lambda x: x.play, self.get_job_events_by_event_type(job, 'playbook_on_play_start'))
        assert(playbook_on_play_start == ['all'])

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

        task_counts = {"Examine slow command": 15,
                       "Examine slow reversal": 10}
        self.verify_desired_tasks(job, 'runner_retry', task_counts)

        assert(len(self.get_job_events_by_event_type(job, 'playbook_on_stats')) == 1)

        desired_stdout_contents = ["SSH password:", "Identity added:", "Vault password:", "SUDO password"]
        self.verify_desired_stdout(job, 'verbose', desired_stdout_contents)

        events = self.get_job_events(job)
        assert(len(events) == 80)

        non_verbose = filter(lambda x: x.event != 'verbose', events)
        assert(not filter(lambda x: not x.uuid, non_verbose))
        assert(not filter(lambda x: x.playbook != 'async_tasks.yml', non_verbose))

    def test_free_strategy(self, factories):
        """Runs a single play with free strategy and confirms desired events at related endpoint"""
        credential = factories.credential(password='passphrase', vault_password='vault')
        inventory = factories.inventory()
        for _ in range(4):
            factories.host(inventory=inventory)
        jt = factories.job_template(credential=credential,
                                    inventory=inventory,
                                    playbook='free_waiter.yml')
        job = jt.launch().wait_until_completed(interval=20)
        assert(job.is_successful)

        playbook_on_start = self.get_job_events_by_event_type(job, 'playbook_on_start')
        assert(len(playbook_on_start) == 1)

        playbook_on_play_start = map(lambda x: x.play, self.get_job_events_by_event_type(job, 'playbook_on_play_start'))
        assert(playbook_on_play_start == ['all'])

        task_counts = {"debug": 11,
                       "wait_for": 10,
                       "set_fact": 10}
        self.verify_desired_tasks(job, 'playbook_on_task_start', task_counts)

        task_counts = {"debug": 55,
                       "wait_for": 50,
                       "set_fact": 50}
        self.verify_desired_tasks(job, 'runner_on_ok', task_counts)

        assert(len(self.get_job_events_by_event_type(job, 'playbook_on_stats')) == 1)

        desired_stdout_contents = ["SSH password:", "Identity added:", "Vault password:", "SUDO password"]
        self.verify_desired_stdout(job, 'verbose', desired_stdout_contents)

        events = self.get_job_events(job)
        assert(len(events) == 193)

        non_verbose = filter(lambda x: x.event != 'verbose', events)
        assert(not filter(lambda x: not x.uuid, non_verbose))
        assert(not filter(lambda x: x.playbook != 'free_waiter.yml', non_verbose))
