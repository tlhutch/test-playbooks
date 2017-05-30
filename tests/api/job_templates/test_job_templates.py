import logging
import json

import towerkit.tower.inventory
import towerkit.exceptions
import fauxfactory
import pytest

from tests.api import Base_Api_Test


log = logging.getLogger(__name__)


@pytest.fixture(scope="function", params=['project', 'inventory', 'credential'])
def job_template_with_deleted_related(request, job_template):
    """Creates and deletes an object."""
    related_pg = job_template.get_related(request.param)
    related_pg.delete()
    return (request.param, job_template)


@pytest.mark.api
@pytest.mark.skip_selenium
@pytest.mark.destructive
class TestJobTemplates(Base_Api_Test):

    pytestmark = pytest.mark.usefixtures('authtoken', 'install_enterprise_license_unlimited')

    @pytest.mark.ansible_integration
    @pytest.mark.ha_tower
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
        assert job_pg.is_successful, "Job unsuccessful - %s" % job_pg

    @pytest.mark.ansible_integration
    @pytest.mark.ha_tower
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
        assert job_pg.is_successful, "Job unsuccessful - %s." % job_pg

        # assess job results for limit
        assert job_pg.ask_limit_on_launch
        assert job_pg.limit == "local", "Unexpected value for job_pg.limit. Expected 'local', got %s." % job_pg.limit
        assert '"-l", "local"' in job_pg.job_args, "Limit value not passed to job_args."

    @pytest.mark.ansible_integration
    @pytest.mark.ha_tower
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
            assert job_pg.is_successful, "Job unsuccessful - %s." % job_pg
        else:
            assert job_pg.status == 'failed', "Job unexpectedly did not fail - %s." % job_pg

        # check job_pg job_tags
        assert job_pg.ask_tags_on_launch == job_template.ask_tags_on_launch, \
            "Job and JT have different value for `ask_tags_on_launch'."
        assert job_pg.job_tags == launch_payload["job_tags"], \
            "Unexpected value for job_pg.job_tags. Expected '%s', got '%s'." % (launch_payload["job_tags"], job_pg.job_tags)

        # check job_pg skip_tags
        assert job_pg.ask_skip_tags_on_launch == job_template.ask_skip_tags_on_launch, \
            "Job and JT have different value for 'ask_skip_tags_on_launch'."
        assert job_pg.skip_tags == launch_payload["skip_tags"], \
            "Unexpected value for job_pg.skip_tags. Expected '%s', got '%s'." % (launch_payload["skip_tags"], job_pg.skip_tags)

        # check job_args
        if launch_payload["job_tags"]:
            assert '\"-t\", \"%s\"' % launch_payload['job_tags'] in job_pg.job_args, \
                "Value for job_tags not represented in job args."
        if launch_payload["skip_tags"]:
            assert '\"--skip-tags=%s\"' % launch_payload['skip_tags'] in job_pg.job_args, \
                "Value for skip_tags not represented in job args."

    @pytest.mark.ha_tower
    def test_launch_with_ignored_payload(self, job_template, another_inventory, another_ssh_credential):
        """Verify that launch-time objects are ignored when their ask flag is set to false."""
        launch_pg = job_template.get_related('launch')

        # assert ask values on launch resource
        assert not launch_pg.ask_variables_on_launch
        assert not launch_pg.ask_tags_on_launch
        assert not launch_pg.ask_skip_tags_on_launch
        assert not launch_pg.ask_job_type_on_launch
        assert not launch_pg.ask_limit_on_launch
        assert not launch_pg.ask_inventory_on_launch
        assert not launch_pg.ask_credential_on_launch

        # launch JT with all possible artifacts in payload
        payload = dict(extra_vars=dict(foo="bar"),
                       job_tags="test job_tag",
                       skip_tags="test skip_tag",
                       job_type="check",
                       inventory=another_inventory.id,
                       credential=another_ssh_credential.id,)
        job_pg = job_template.launch(payload).wait_until_completed()
        assert job_pg.is_successful, "Job unsuccessful - %s." % job_pg

        # assert that payload ignored
        assert job_pg.extra_vars == json.dumps({}), \
            "Unexpected value for job_pg.extra_vars - %s." % job_pg.extra_vars
        assert job_pg.job_tags == job_template.job_tags, \
            "JT job_tags overridden. Expected %s, got %s." % (job_template.job_tags, job_pg.job_tags)
        assert job_pg.skip_tags == job_template.skip_tags, \
            "JT skip_tags overriden. Expected %s, got %s." % (job_template.skip_tags, job_pg.skip_tags)
        assert job_pg.job_type == job_template.job_type, \
            "JT job_type overriden. Expected %s, got %s." % (job_template.job_type, job_pg.job_type)
        assert job_pg.inventory == job_template.inventory, \
            "JT inventory overriden. Expected inventory %s, got %s." % (job_template.inventory, job_pg.inventory)
        assert job_pg.credential == job_template.credential, \
            "JT credential overriden. Expected credential %s, got %s." % (job_template.credential, job_pg.credential)

    @pytest.mark.ansible_integration
    @pytest.mark.ha_tower
    @pytest.mark.parametrize("job_type", ["run", "scan", "check"])
    def test_launch_nonscan_job_template_with_job_type_in_payload(self, nonscan_job_template, job_type):
        """Verifies that "job_type" may be given at launch-time with run/check JTs."""
        nonscan_job_template.patch(ask_job_type_on_launch=True)
        launch_pg = nonscan_job_template.get_related('launch')
        payload = dict(job_type=job_type)

        # assert values on launch resource
        assert not launch_pg.can_start_without_user_input
        assert not launch_pg.ask_variables_on_launch
        assert not launch_pg.passwords_needed_to_start
        assert not launch_pg.variables_needed_to_start
        assert not launch_pg.credential_needed_to_start
        assert launch_pg.ask_job_type_on_launch

        # assert that 'run/check' should result in successful jobs
        if job_type in ['run', 'check']:
            job_pg = nonscan_job_template.launch(payload).wait_until_completed()
            assert job_pg.is_successful, "Job unsuccessful - %s." % job_pg
            assert job_pg.ask_job_type_on_launch
            assert job_pg.job_type == job_type, "Unexpected value for job_type. Expected %s, got %s." % (job_type, job_pg.job_type)

        # assert 'scan' should raise a 400
        else:
            with pytest.raises(towerkit.exceptions.BadRequest):
                nonscan_job_template.launch(payload)

    @pytest.mark.ansible_integration
    @pytest.mark.ha_tower
    @pytest.mark.parametrize("job_type", ["run", "scan", "check"])
    def test_launch_scan_job_template_with_job_type_in_payload(self, scan_job_template, job_type):
        """Verifies that "job_type" may be given at launch-time with scan JTs."""
        scan_job_template.patch(ask_job_type_on_launch=True)
        launch_pg = scan_job_template.get_related('launch')
        payload = dict(job_type=job_type)

        # assert values on launch resource
        assert not launch_pg.can_start_without_user_input
        assert not launch_pg.ask_variables_on_launch
        assert not launch_pg.passwords_needed_to_start
        assert not launch_pg.variables_needed_to_start
        assert not launch_pg.credential_needed_to_start
        assert launch_pg.ask_job_type_on_launch

        # assert that 'run/check' should raise a 400
        if job_type in ['run', 'check']:
            with pytest.raises(towerkit.exceptions.BadRequest):
                scan_job_template.launch(payload)

        # assert that 'scan' should result in a regular scan job
        else:
            job_pg = scan_job_template.launch(payload).wait_until_completed()
            assert job_pg.is_successful, "Job unsuccessful - %s." % job_pg
            assert job_pg.ask_job_type_on_launch
            assert job_pg.job_type == job_type, "Unexpected value for job_type. Expected %s, got %s." % (job_type, job_pg.job_type)

    @pytest.mark.ansible_integration
    @pytest.mark.ha_tower
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
        assert job_pg.is_successful, "Job unsuccessful - %s." % job_pg

        # assess job results for inventory
        assert job_pg.ask_inventory_on_launch
        assert job_pg.inventory == another_inventory.id, \
            "Job ran with incorrect inventory. Expected %s but got %s." % (another_inventory.id, job_template.inventory)

    @pytest.mark.ansible_integration
    @pytest.mark.ha_tower
    def test_ask_inventory_on_launch_with_scan_job_template(self, scan_job_template, api_job_templates_pg):
        """Verifies scan JTs may not have ask_inventory_on_launch."""
        # patch scan JT and assess results
        payload = dict(ask_inventory_on_launch=True)
        exc_info = pytest.raises(towerkit.exceptions.BadRequest, scan_job_template.patch, **payload)
        result = exc_info.value[1]
        assert result == {u'inventory': [u'Scan jobs must be assigned a fixed inventory.']}, \
            "Unexpected API response after attempting to patch a scan JT with ask_inventory_on_launch enabled."

        # FIXME: implement put scan JT check

        # post scan JT and assess results
        payload = dict(name="scan_job_template-%s" % fauxfactory.gen_utf8(),
                       description="Random scan job_template with machine credential - %s" % fauxfactory.gen_utf8(),
                       inventory=scan_job_template.inventory,
                       job_type='scan',
                       project=None,
                       credential=scan_job_template.credential,
                       playbook='Default',
                       ask_inventory_on_launch=True, )
        exc_info = pytest.raises(towerkit.exceptions.BadRequest, api_job_templates_pg.post, payload)
        result = exc_info.value[1]
        assert result == {u'inventory': [u'Scan jobs must be assigned a fixed inventory.']}, \
            "Unexpected API response after attempting to patch a scan JT with ask_inventory_on_launch enabled."

    @pytest.mark.ha_tower
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

        # if a credential was deleted, the API should require one to launch
        if related == 'credential':
            assert launch_pg.credential_needed_to_start
        else:
            assert not launch_pg.credential_needed_to_start

        # assert launch failure
        with pytest.raises(towerkit.exceptions.BadRequest):
            launch_pg.post()

    @pytest.mark.ansible_integration
    @pytest.mark.ha_tower
    @pytest.mark.parametrize("limit_value, expected_count", [
        ("", 12),
        ("all", 12),
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
        inv['_meta']['hostvars'][host] = dict(ansible_ssh_host='127.0.0.1', ansible_connection='local')

print json.dumps(inv, indent=2)
""")
    def test_launch_with_matched_limit_value(
            self, limit_value,
            expected_count,
            custom_inventory_source,
            custom_inventory_update_with_status_completed,
            job_template
    ):
        """Verifies that job_template launches with different values for limit behave as expected."""
        # patch job_template
        job_template.patch(limit=limit_value)
        assert job_template.limit == limit_value, "Unexpected job_template limit with job template - %s." % job_template

        # launch the job template
        job_pg = job_template.launch().wait_until_completed()
        assert job_pg.is_successful, "Job unsuccessful - %s." % job_pg

        # assert that job run on correct number of hosts
        job_host_summaries_pg = job_pg.get_related('job_host_summaries')
        assert job_host_summaries_pg.count == expected_count

    @pytest.mark.ansible_integration
    @pytest.mark.ha_tower
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
        assert "Specified --limit does not match any hosts" in job_pg.result_stdout, \
            "Unexpected job_pg.result_stdout when launching a job_template with an unmatched limit."

    @pytest.mark.ansible_integration
    @pytest.mark.ha_tower
    def test_launch_with_matched_tag_value(self, job_template_with_random_tag):
        """Tests that target tasks are run when launching a job with job_tags."""
        # patch our JT such that its tag value matches a single playbook task
        job_template_with_random_tag.patch(job_tags="tag")
        assert job_template_with_random_tag.job_tags == "tag"

        # launch JT and assess results
        job_pg = job_template_with_random_tag.launch().wait_until_completed()
        assert job_pg.is_successful, "Job unsuccessful - %s." % job_pg
        assert "\"-t\", \"tag\"" in job_pg.job_args, \
            "Launched a tag JT but '-t tag' not found in job_args."

        # check that expected tasks run
        assert job_pg.get_related('job_events', event='playbook_on_task_start').count == 2, \
            "Unexpected number of task_events returned (expected 2)."
        assert job_pg.get_related('job_events', event='runner_on_ok').count == 2, \
            "Unexpected number of task_events returned (expected 2)."

    @pytest.mark.ansible_integration
    @pytest.mark.ha_tower
    def test_launch_with_unmatched_tag_value(self, job_template_with_random_tag, ansible_version_cmp):
        """Tests launching jobs with an unmatched tag value."""
        job_pg = job_template_with_random_tag.launch().wait_until_completed()

        # jobs with unmatched tags failed pre-ansible-v2
        if ansible_version_cmp('2.0.0.0') < 0:
            assert job_pg.status == 'failed', "Unexpected job status for job - %s." % job_pg
            assert "ERROR: tag(s) not found in playbook" in job_pg.result_stdout, \
                "Unexpected job_pg.result_stdout: %s." % job_pg.result_stdout
        else:
            assert job_pg.is_successful, "Job unsuccessful - %s." % job_pg
            assert job_pg.job_tags == job_template_with_random_tag.job_tags, \
                "Value for job_tags inconsistent with job_template value."

    @pytest.mark.ha_tower
    @pytest.mark.parametrize('timeout, status, job_explanation', [
        (0, 'successful', ''),
        (60, 'successful', ''),
        (1, 'failed', 'Job terminated due to timeout'),
    ], ids=['no timeout', 'under timeout', 'over timeout'])
    def test_launch_with_timeout(self, job_template, timeout, status, job_explanation):
        """Tests JTs with timeouts."""
        job_template.patch(timeout=timeout)

        # launch JT and assess spawned job
        job_pg = job_template.launch().wait_until_completed()
        assert job_pg.status == status, \
            "Unexpected job status. Expected '{0}' but received '{1}.'".format(status, job_pg.status)
        assert job_pg.job_explanation == job_explanation, \
            "Unexpected job job_explanation. Expected '{0}' but received '{1}.'".format(job_explanation, job_pg.job_explanation)
        assert job_pg.timeout == job_template.timeout, \
            "Job_pg has a different timeout value ({0}) than its JT ({1}).".format(job_pg.timeout, job_template.timeout)

    @pytest.mark.ha_tower
    def test_conflict_exception_with_running_job(self, job_template_sleep):
        """Verify that a conflict exception is raised when deleting either the JT
        or some of the JT's underlying resources when a job is still running.
        """
        inventory_pg = job_template_sleep.get_related("inventory")
        project_pg = job_template_sleep.get_related("project")

        # launch the job_template
        job_template_sleep.launch().wait_until_started()

        # delete target object and assert 409 raised
        for tower_resource in [job_template_sleep, inventory_pg, project_pg]:
            with pytest.raises(towerkit.exceptions.Conflict):
                tower_resource.delete()

    @pytest.mark.ansible_integration
    @pytest.mark.ha_tower
    def test_launch_check_job_template(self, job_template):
        """Launch check job template and assess results."""
        # patch job template
        job_template.patch(job_type='check', playbook='check.yml')
        assert job_template.job_type == 'check'
        assert job_template.playbook == 'check.yml'

        # launch JT and assess results
        job_pg = job_template.launch().wait_until_completed()
        assert job_pg.is_successful, "Job unsuccessful - %s." % job_pg
        assert job_pg.job_type == "check", "Unexpected job_type after launching check JT."
        assert "\"--check\"" in job_pg.job_args, \
            "Launched a check JT but '--check' not present in job_args."

        # check that target task skipped
        matching_job_events = job_pg.get_related('job_events', event='runner_on_skipped')
        assert matching_job_events.count == 1, \
            "Unexpected number of matching job events (%s != 1)" % matching_job_events.count
