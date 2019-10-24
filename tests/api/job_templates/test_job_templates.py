import logging
import json
import re
import threading
import time

from awxkit import config, utils
import awxkit.awx.inventory
import awxkit.exceptions
import pytest

from tests.api import APITest


log = logging.getLogger(__name__)


@pytest.fixture(scope="function", params=['project', 'inventory'])
def job_template_with_deleted_related(request, job_template):
    """Creates and deletes an object."""
    related_pg = job_template.get_related(request.param)
    related_pg.delete()
    return (request.param, job_template)


@pytest.mark.usefixtures('authtoken')
class TestJobTemplates(APITest):

    @pytest.mark.ansible_integration
    def test_launch(self, job_template_ping):
        """Verify the job->launch endpoint behaves as expected"""
        launch_pg = job_template_ping.get_related('launch')

        # assert values on launch resource
        assert launch_pg.can_start_without_user_input
        assert not launch_pg.ask_variables_on_launch
        assert not launch_pg.passwords_needed_to_start
        assert not launch_pg.variables_needed_to_start
        assert not launch_pg.credential_needed_to_start

        # launch the job_template and wait for completion
        job_pg = job_template_ping.launch().wait_until_completed()

        # assert success
        job_pg.assert_successful()

    def test_modified_by_unaffected_by_launch(self, v2, factories, job_template_ping):
        admin_user = factories.user(first_name='Joe', last_name='Admin', is_superuser=True)
        assert job_template_ping.summary_fields.modified_by['username'] == config.credentials.users.admin.username
        with self.current_user(admin_user):
            job = job_template_ping.launch()
            assert job.summary_fields.created_by.username == admin_user.username
        tmpl = v2.job_templates.get(id=job_template_ping.id).results.pop()
        assert tmpl.summary_fields.get('modified_by', {}).get('username') == config.credentials.users.admin.username

    @pytest.mark.yolo
    @pytest.mark.ansible_integration
    def test_launch_with_limit_in_payload(self, job_template_with_random_limit):
        """Verifies that a value for 'limit' may be passed at launch-time."""
        job_template_with_random_limit.patch(ask_limit_on_launch=True)
        launch_pg = job_template_with_random_limit.get_related('launch')

        # assert values on launch resource
        assert not launch_pg.can_start_without_user_input
        assert not launch_pg.ask_variables_on_launch
        assert not launch_pg.passwords_needed_to_start
        assert not launch_pg.variables_needed_to_start
        assert not launch_pg.credential_needed_to_start
        assert launch_pg.ask_limit_on_launch

        # launch JT with limit
        payload = dict(limit="local")
        job_pg = job_template_with_random_limit.launch(payload).wait_until_completed()
        job_pg.assert_successful()

        # assess job results for limit
        assert job_pg.limit == "local", "Unexpected value for job_pg.limit. Expected 'local', got %s." % job_pg.limit
        limit_index = job_pg.job_args.index('-l') + 1
        assert job_pg.job_args[limit_index] == "local", "Limit value not passed to job_args."

    @pytest.mark.yolo
    @pytest.mark.ansible_integration
    @pytest.mark.parametrize("patch_payload, launch_payload", [
        (
            {"ask_tags_on_launch": True, "ask_skip_tags_on_launch": False},
            {"job_tags": "test job_tag", "skip_tags": ""},
        ),
        (
            {"ask_tags_on_launch": False, "ask_skip_tags_on_launch": True},
            {"job_tags": "", "skip_tags": "test skip_tag"},
        ),
    ], ids=["job_tags", "skip_tags"])
    def test_launch_with_tags_in_payload(self, job_template, ansible_version_cmp, patch_payload, launch_payload):
        """Verifies that values for 'job_tags' and 'skip_tags' may be passed at launch-time."""
        job_template.patch(**patch_payload)
        launch_pg = job_template.get_related('launch')

        # assert values on launch resource
        assert not launch_pg.can_start_without_user_input
        assert not launch_pg.ask_variables_on_launch
        assert not launch_pg.passwords_needed_to_start
        assert not launch_pg.variables_needed_to_start
        assert not launch_pg.credential_needed_to_start
        for key in patch_payload:
            assert getattr(launch_pg, key) == patch_payload[key]

        # launch JT with values for job_tag and skip_tag in payload
        job_pg = job_template.launch(launch_payload).wait_until_completed()
        if ansible_version_cmp("2.0.0.0") >= 0:
            job_pg.assert_successful()
        else:
            assert job_pg.status == 'failed', "Job unexpectedly did not fail - %s." % job_pg

        # check job_pg job_tags
        assert job_pg.job_tags == launch_payload["job_tags"], ("Unexpected value for job_pg.job_tags. Expected"
                                                               " '%s', got '%s'." % (launch_payload["job_tags"],
                                                                                     job_pg.job_tags))

        # check job_pg skip_tags
        assert job_pg.skip_tags == launch_payload["skip_tags"], (
            "Unexpected value for job_pg.skip_tags. Expected '%s', got '%s'." % (launch_payload["skip_tags"], job_pg.skip_tags))

        # check job_args
        if launch_payload["job_tags"]:
            tag_index = job_pg.job_args.index('-t') + 1
            assert job_pg.job_args[tag_index] == launch_payload['job_tags'], \
                "Value for job_tags not represented in job args."
        if launch_payload["skip_tags"]:
            assert '--skip-tags=%s' % launch_payload['skip_tags'] in job_pg.job_args, \
                "Value for skip_tags not represented in job args."

    @pytest.mark.yolo
    @pytest.mark.parametrize('diff_mode', [True, False])
    def test_launch_with_diff_mode_in_payload(self, factories, diff_mode):
        host = factories.host()
        jt = factories.job_template(inventory=host.ds.inventory, playbook='file.yml', ask_diff_mode_on_launch=True)
        job = jt.launch(dict(diff_mode=diff_mode)).wait_until_completed()

        job.assert_successful()
        assert job.diff_mode is diff_mode
        assert ('--- before' in job.result_stdout) is diff_mode
        assert ('+++ after' in job.result_stdout) is diff_mode

    @pytest.mark.parametrize('verbosity, stdout_lines',
        [(0, ['TASK [ping]', 'PLAY RECAP']),
         # NOTE: the changed status is inside ansible_facts dict, which could include "discovered_interpreter_python"
         # keys are alphabetical, so this still works because "d" < "p", but it is brittle
         (1, ['TASK [ping]', 'PLAY RECAP', '"changed": false, "ping": "pong"']),
         (2, ['TASK [ping]', 'PLAY RECAP', '"changed": false, "ping": "pong"', 'PLAYBOOK: ping.yml',
              'META: ran handlers']),
         (3, ['TASK [ping]', 'PLAY RECAP', 'PLAYBOOK: ping.yml', 'META: ran handlers',
              re.compile("EXEC /bin/sh -c 'echo ~(awx)? && sleep 0'")]),
         (4, ['TASK [ping]', 'PLAY RECAP', 'PLAYBOOK: ping.yml', 'META: ran handlers',
              re.compile("EXEC /bin/sh -c 'echo ~(awx)? && sleep 0'"), 'Loading callback plugin awx_display']),
         (5, ['TASK [ping]', 'PLAY RECAP', 'PLAYBOOK: ping.yml', 'META: ran handlers',
              re.compile("EXEC /bin/sh -c 'echo ~(awx)? && sleep 0'"), 'Loading callback plugin awx_display'])],
         ids=['0-normal', '1-verbose', '2-more verbose', '3-debug', '4-connection debug', '5-winrm debug'])
    def test_launch_with_verbosity_in_payload(self, factories, verbosity, stdout_lines):
        host = factories.host()
        jt = factories.job_template(inventory=host.ds.inventory, ask_verbosity_on_launch=True)
        job = jt.launch(dict(verbosity=verbosity)).wait_until_completed()
        job.assert_successful()

        assert jt.verbosity == 0
        assert jt.ask_verbosity_on_launch
        assert job.verbosity == verbosity
        for line in stdout_lines:
            if isinstance(line, re._pattern_type):
                assert re.search(line, job.result_stdout) is not None
            else:
                assert line in job.result_stdout

    def test_launch_with_ignored_payload(self, job_template, another_inventory, another_ssh_credential):
        """Verify that launch-time objects are ignored when their ask flag is set to false."""
        launch = job_template.get_related('launch')

        # assert ask values on launch resource
        assert not launch.ask_variables_on_launch
        assert not launch.ask_tags_on_launch
        assert not launch.ask_skip_tags_on_launch
        assert not launch.ask_job_type_on_launch
        assert not launch.ask_limit_on_launch
        assert not launch.ask_inventory_on_launch
        assert not launch.ask_credential_on_launch
        assert not launch.ask_diff_mode_on_launch
        assert not launch.ask_verbosity_on_launch

        # launch JT with all possible artifacts in payload
        payload = dict(extra_vars=dict(foo="bar"),
                       job_tags="test job_tag",
                       skip_tags="test skip_tag",
                       job_type="check",
                       inventory=another_inventory.id,
                       credential=another_ssh_credential.id,
                       diff_mode=True,
                       verbosity=5)
        job = job_template.launch(payload).wait_until_completed()
        job.assert_successful()

        # assert that payload ignored
        assert job.extra_vars == json.dumps({}), \
            "Unexpected value for job_pg.extra_vars - %s." % job.extra_vars
        assert job.job_tags == job_template.job_tags, \
            "JT job_tags overridden. Expected %s, got %s." % (job_template.job_tags, job.job_tags)
        assert job.skip_tags == job_template.skip_tags, \
            "JT skip_tags overriden. Expected %s, got %s." % (job_template.skip_tags, job.skip_tags)
        assert job.job_type == job_template.job_type, \
            "JT job_type overridden. Expected %s, got %s." % (job_template.job_type, job.job_type)
        assert job.inventory == job_template.inventory, \
            "JT inventory overridden. Expected inventory %s, got %s." % (job_template.inventory, job.inventory)
        job_credentials = [c.id for c in job.related.credentials.get().results]
        jt_credentials = [c.id for c in job_template.related.credentials.get().results]
        assert job_credentials == jt_credentials, "JT credential overridden. Expected credential {jt_credentials}, got {job_credentials}."
        assert job.diff_mode == job_template.diff_mode, \
            "JT diff_mode overridden. Expected %s, got %s." % (job_template.diff_mode, job.diff_mode)
        assert job.verbosity == job_template.verbosity, \
            "JT verbosity overridden. Expected verbosity {0}, received {1}.".format(job_template.verbosity, job.verbosity)

    @pytest.mark.ansible_integration
    @pytest.mark.parametrize("job_type", ["run", "check"])
    def test_launch_with_job_type_in_payload(self, factories, job_type):
        """Verifies that "job_type" may be given at launch-time with run/check JTs."""
        jt = factories.job_template(ask_job_type_on_launch=True)
        launch = jt.get_related('launch')

        # assert values on launch resource
        assert not launch.can_start_without_user_input
        assert not launch.ask_variables_on_launch
        assert not launch.passwords_needed_to_start
        assert not launch.variables_needed_to_start
        assert not launch.credential_needed_to_start
        assert launch.ask_job_type_on_launch

        job = jt.launch(dict(job_type=job_type)).wait_until_completed()
        job.assert_successful()

        assert jt.ask_job_type_on_launch
        assert job.job_type == job_type

    @pytest.mark.ansible_integration
    def test_launch_with_inventory_in_payload(self, job_template, another_inventory):
        """Verifies that 'inventory' may be given at launch-time."""
        job_template.patch(ask_inventory_on_launch=True)
        launch_pg = job_template.get_related('launch')

        # assert values on launch resource
        assert not launch_pg.can_start_without_user_input
        assert not launch_pg.ask_variables_on_launch
        assert not launch_pg.passwords_needed_to_start
        assert not launch_pg.variables_needed_to_start
        assert not launch_pg.credential_needed_to_start
        assert launch_pg.ask_inventory_on_launch
        assert not launch_pg.inventory_needed_to_start

        # launch JT with inventory in payload
        payload = dict(inventory=another_inventory.id)
        job_pg = job_template.launch(payload).wait_until_completed()
        job_pg.assert_successful()

        # assess job results for inventory
        assert job_template.ask_inventory_on_launch
        assert job_pg.inventory == another_inventory.id, \
            "Job ran with incorrect inventory. Expected %s but got %s." % (another_inventory.id, job_template.inventory)

    def test_launch_template_with_deleted_related(self, job_template_with_deleted_related):
        """Verify that the job->launch endpoint does not allow launching a
        job_template whose related endpoints have been deleted.
        """
        (related, job_template_with_deleted_related) = job_template_with_deleted_related
        launch_pg = job_template_with_deleted_related.get_related('launch')

        # assert values on launch resource
        assert launch_pg.can_start_without_user_input
        assert not launch_pg.ask_variables_on_launch
        assert not launch_pg.passwords_needed_to_start
        assert not launch_pg.variables_needed_to_start
        assert not launch_pg.credential_needed_to_start

        # assert launch failure
        with pytest.raises(awxkit.exceptions.BadRequest):
            launch_pg.post()

    @pytest.mark.ansible_integration
    @pytest.mark.parametrize("limit_value, expected_count", [
        ("", 11),
        ("all", 11),
        ("host-6", 1),
        ("group-1", 4),
        ("group*:&group-1:!duplicate_host", 3),  # All groups intersect with "group-1" and not "duplicate_host"
        ("duplicate_host", 1),
    ])
    @pytest.mark.fixture_args(source_script="""#!/usr/bin/env python
import json

# Create hosts and groups
inv = dict(_meta=dict(hostvars={}), hosts=[])
inv['group-0'] = [
   "duplicate_host",
   "host with spaces in name",
   "host-1",
   "host-2",
   "host-3",
]
inv['group-1'] = [
   "duplicate_host",
   "host-4",
   "host-5",
   "host-6",
]
inv['group-2'] = [
   "duplicate_host",
   "host-7",
   "host-8",
   "host-9",
]

# Add _meta hostvars
for grp, hosts in inv.items():
    for host in hosts:
        inv['_meta']['hostvars'][host] = dict(ansible_host='127.0.0.1', ansible_connection='local')

print(json.dumps(inv, indent=2))
""")
    def test_launch_with_matched_limit_value(
            self, job_template,
            limit_value,
            expected_count,
            custom_inventory_source,
            custom_inventory_update_with_status_completed
    ):
        """Verifies that job_template launches with different values for limit behave as expected."""
        # patch job_template
        job_template.inventory = custom_inventory_source.inventory
        job_template.patch(limit=limit_value)
        assert job_template.limit == limit_value, "Unexpected job_template limit with job template - %s." % job_template

        # launch the job template
        job_pg = job_template.launch().wait_until_completed()
        job_pg.assert_successful()

        # assert that job run on correct number of hosts
        job_host_summaries_pg = job_pg.get_related('job_host_summaries')
        assert job_host_summaries_pg.count == expected_count

    @pytest.mark.ansible_integration
    def test_launch_with_unmatched_limit_value(self, job_template_with_random_limit):
        """Verify that launching a job template without matching hosts fails appropriately."""
        # check that our job_template limit is unmatched
        hosts_pg = job_template_with_random_limit.get_related("inventory").get_related("hosts")
        host_names = [host.name for host in hosts_pg.results]
        for host_name in host_names:
            assert host_name != job_template_with_random_limit.limit, "Matching host unexpectedly found - %s." % host_name

        # launch the job template and check the results
        job_pg = job_template_with_random_limit.launch().wait_until_completed()
        assert job_pg.status == "failed", "Unexpected job_pg.status - %s." % job_pg
        assert "--limit does not match any hosts" in job_pg.result_stdout, f'stdout: {job_pg.result_stdout}\n traceback: {job_pg.result_traceback}'

    @pytest.mark.ansible_integration
    def test_launch_with_matched_tag_value(self, job_template_with_random_tag):
        """Tests that target tasks are run when launching a job with job_tags."""
        # patch our JT such that its tag value matches a single playbook task
        job_template_with_random_tag.patch(job_tags="tag")
        assert job_template_with_random_tag.job_tags == "tag"

        # launch JT and assess results
        job_pg = job_template_with_random_tag.launch().wait_until_completed()
        job_pg.assert_successful()
        tag_index = job_pg.job_args.index('-t') + 1
        assert job_pg.job_args[tag_index] == "tag", "Launched a tag JT but '-t tag' not found in job_args."

        # check that expected tasks run
        assert job_pg.get_related('job_events', event='playbook_on_task_start').count == 2, \
            "Unexpected number of task_events returned (expected 2)."
        assert job_pg.get_related('job_events', event='runner_on_ok').count == 2, \
            "Unexpected number of task_events returned (expected 2)."

    @pytest.mark.ansible_integration
    def test_launch_with_unmatched_tag_value(self, job_template_with_random_tag, ansible_version_cmp):
        """Tests launching jobs with an unmatched tag value."""
        job_pg = job_template_with_random_tag.launch().wait_until_completed()

        # jobs with unmatched tags failed pre-ansible-v2
        if ansible_version_cmp('2.0.0.0') < 0:
            assert job_pg.status == 'failed', "Unexpected job status for job - %s." % job_pg
            assert "ERROR: tag(s) not found in playbook" in job_pg.result_stdout, \
                "Unexpected job_pg.result_stdout: %s." % job_pg.result_stdout
        else:
            job_pg.assert_successful()
            assert job_pg.job_tags == job_template_with_random_tag.job_tags, \
                "Value for job_tags inconsistent with job_template value."

    @pytest.mark.parametrize('timeout, status, job_explanation', [
        (0, 'successful', ''),
        (60, 'successful', ''),
        (1, 'failed', 'Job terminated due to timeout'),
    ], ids=['no timeout', 'under timeout', 'over timeout'])
    def test_launch_with_timeout(self, factories, timeout, status, job_explanation):
        """Tests JTs with timeouts."""
        job_template = factories.job_template(timeout=timeout, playbook='sleep.yml', extra_vars='sleep_interval: 10')
        factories.host(inventory=job_template.ds.inventory)

        # launch JT and assess spawned job
        job_pg = job_template.launch().wait_until_completed()
        assert job_pg.status == status, \
            "Unexpected job status. Expected '{0}' but received '{1}.'".format(status, job_pg.status)
        assert job_pg.job_explanation == job_explanation, \
            "Unexpected job job_explanation. Expected '{0}' but received '{1}.'".format(job_explanation, job_pg.job_explanation)
        assert job_pg.timeout == job_template.timeout, \
            "Job_pg has a different timeout value ({0}) than its JT ({1}).".format(job_pg.timeout, job_template.timeout)

    def test_conflict_exception_with_running_job(self, job_template_sleep):
        """Verify that a conflict exception is raised when deleting either the JT
        or some of the JT's underlying resources when a job is still running.
        """
        inventory = job_template_sleep.ds.inventory
        project = job_template_sleep.ds.project

        # launch the job_template
        job = job_template_sleep.launch().wait_until_started()

        # delete target object and assert 409 raised
        for tower_resource in [job_template_sleep, inventory, project]:
            with pytest.raises(awxkit.exceptions.Conflict):
                tower_resource.delete()

        job.wait_until_completed().assert_successful()

    @pytest.mark.github('https://github.com/ansible/tower/issues/789', skip=True)
    def test_job_listing_after_delete_does_not_500(self, factories, v2):
        num_jobs = 2
        host = factories.host()
        jt = factories.job_template(inventory=host.ds.inventory, allow_simultaneous=True)
        [jt.launch() for i in range(num_jobs)]

        utils.poll_until(lambda: jt.related.jobs.get(status='successful').count == num_jobs, timeout=300)

        def delete_job_template(jt_id, delay):
            time.sleep(delay)
            v2.job_templates.get(id=jt_id).results[0].delete()

        def do_get_jobs(loops, failed, index):
            failed[index] = False
            for i in range(loops):
                try:
                    v2.unified_jobs.get(page_size=num_jobs, order_by='-finished', not__launch_type='sync')
                except awxkit.exceptions.InternalServerError:
                    failed[index] = True
                    break

        thread_count = 5
        failed = [False] * thread_count
        threads = [threading.Thread(target=do_get_jobs, args=(100, failed, i)) for i in range(thread_count)]
        t_delete = threading.Thread(target=delete_job_template, args=(jt.id, 2))
        all_threads = threads + [t_delete]
        [t.start() for t in all_threads]
        [t.join() for t in all_threads]

        for failure in failed:
            assert False is failure, \
                    "Getting list of jobs shortly after deleting related job" \
                    "template resulted in a 500 error"

    def test_launch_with_diff_mode(self, factories):
        host = factories.host()
        jt = factories.job_template(inventory=host.ds.inventory, playbook='file.yml', diff_mode=True)
        job = jt.launch().wait_until_completed()

        job.assert_successful()
        assert job.diff_mode
        assert '--- before' in job.result_stdout
        assert '+++ after' in job.result_stdout

    @pytest.mark.ansible_integration
    def test_launch_check_job_template(self, job_template):
        """Launch check job template and assess results."""
        # patch job template
        job_template.patch(job_type='check', playbook='check.yml')
        assert job_template.job_type == 'check'
        assert job_template.playbook == 'check.yml'

        # launch JT and assess results
        job_pg = job_template.launch().wait_until_completed()
        job_pg.assert_successful()
        assert job_pg.job_type == "check", "Unexpected job_type after launching check JT."
        assert "--check" in job_pg.job_args, \
            "Launched a check JT but '--check' not present in job_args."

        # check that target task skipped
        matching_job_events = job_pg.get_related('job_events', event='runner_on_skipped')
        assert matching_job_events.count == 1, \
            "Unexpected number of matching job events (%s != 1)" % matching_job_events.count

    def test_tower_host_undefined_for_job(self, v2, factories):
        # AWX_HOST should still work
        jt = factories.job_template(
            playbook='environ_test.yml',
            extra_vars='env_variable: AWX_HOST\nenv_value: {}'.format(
                v2.settings.get().get_endpoint('system').TOWER_URL_BASE
            )
        )
        factories.host(inventory=jt.ds.inventory)
        job = jt.launch().wait_until_completed()
        job.assert_successful()

        # TOWER_HOST should be undefined
        jt.extra_vars = jt.extra_vars.replace('AWX_HOST', 'TOWER_HOST')
        job = jt.launch().wait_until_completed()
        assert job.status == 'failed'

    @pytest.mark.parametrize('extra_var, attr', [
        ['name', 'username'],
        ['id', 'id'],
        ['first_name', 'first_name'],
        ['last_name', 'last_name'],
        ['email', 'email'],
    ])
    @pytest.mark.parametrize('prefix', ['awx', 'tower'])
    def test_awx_metavars_for_jobs(self, v2, factories, update_setting_pg, extra_var, attr, prefix):
        admin_user = factories.user(first_name='Joe', last_name='Admin', is_superuser=True)
        value = str(getattr(admin_user, attr))
        var_name = '{}_user_{}'.format(prefix, extra_var)
        update_setting_pg(
            v2.settings.get().get_endpoint('jobs'),
            dict(ALLOW_JINJA_IN_EXTRA_VARS='always')
        )
        with self.current_user(admin_user):
            jt = factories.job_template(playbook='debug_extra_vars.yml',
                                           extra_vars='var1: "{{ %s }}"' % var_name)
            factories.host(inventory=jt.ds.inventory)
            job = jt.launch().wait_until_completed()
        job.assert_successful()
        assert '"var1": "{}"'.format(value) in job.result_stdout

    @pytest.mark.ansible_integration
    def test_playbook_calling_ansible_with_shell_and_inventory_file(self, factories):
        jt = factories.job_template(playbook='test_ansible_shell.yml')
        factories.host(inventory=jt.ds.inventory)
        job = jt.launch().wait_until_completed()

        playbook_event = job.related.job_events.get(
            task='Run Playbook', event__startswith='runner_on_ok').results.pop()
        job.assert_successful()
        assert 'ok=1' in playbook_event.event_data.res.stdout
