from distutils.version import LooseVersion
import logging
import json
import yaml

import towerkit.tower.inventory
import towerkit.exceptions
import fauxfactory
import pytest

from tests.api import Base_Api_Test


log = logging.getLogger(__name__)


@pytest.fixture(scope="function")
def missing_field_survey_specs(request):
    """Returns a list of survey_spec's which should fail to post."""
    return [dict(),
            dict(description=fauxfactory.gen_utf8(),
                 spec=[dict(required=False,
                            question_name="Enter your email &mdash; &euro;",
                            variable="submitter_email",
                            type="text",)]),
            dict(name=fauxfactory.gen_utf8(),
                 spec=[dict(required=False,
                            question_name="Enter your email &mdash; &euro;",
                            variable="submitter_email",
                            type="text",)]),
            dict(name=fauxfactory.gen_utf8(),
                 description=fauxfactory.gen_utf8()),
            dict(name=fauxfactory.gen_utf8(),
                 description=fauxfactory.gen_utf8(),
                 spec=[])]


@pytest.fixture(scope="function", params=['project', 'inventory', 'credential'])
def job_template_with_deleted_related(request, job_template):
    """Creates and deletes an object."""
    related_pg = job_template.get_related(request.param)
    related_pg.delete()
    return (request.param, job_template)


@pytest.mark.api
@pytest.mark.skip_selenium
@pytest.mark.destructive
class Test_Job_Template(Base_Api_Test):

    pytestmark = pytest.mark.usefixtures('authtoken', 'install_enterprise_license_unlimited')

    def load_json(self, obj):
        try:
            return json.loads(obj)
        except ValueError:
            return {}

    def load_json_or_yaml(self, obj):
        try:
            return json.loads(obj)
        except ValueError:
            return yaml.load(obj)

    def get_survey_vars(self, survey_spec, **kwargs):
        vars = []
        for question in survey_spec.spec:
            if all(item in question.items() for item in kwargs.items()):
                vars.append(question['variable'])
        return vars

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
        assert job_pg.is_successful, "Job unsuccessful - %s" % job_pg

    @pytest.mark.ansible_integration
    def test_launch_with_extra_vars_from_job_template(self, job_template_with_extra_vars):
        """Verify that when no launch-time extra_vars are provided, job extra_vars consist
        of job_template extra_vars.
        """
        launch = job_template_with_extra_vars.related.launch.get()

        # assert values on launch resource
        assert launch.can_start_without_user_input
        assert not launch.ask_variables_on_launch
        assert not launch.passwords_needed_to_start
        assert not launch.variables_needed_to_start
        assert not launch.credential_needed_to_start

        # assert job successful
        job = job_template_with_extra_vars.launch().wait_until_completed()
        assert job.is_successful, "job unsuccessful - %s" % job

        # assert extra_vars match job_template extra_vars
        loaded_job_template_vars = self.load_json_or_yaml(job_template_with_extra_vars.extra_vars)
        loaded_job_vars = self.load_json(job.extra_vars)
        assert loaded_job_vars == loaded_job_template_vars

    @pytest.mark.ansible_integration
    def test_launch_with_extra_vars_at_launch(self, job_template_with_extra_vars, launch_time_extra_vars):
        """Verify that when launch-time extra_vars are provided, job extra_vars consist
        of a union of the launch-time and JT extra_vars. Launch-time variables should
        take precedence over JT variables with our colliding intersection variable.
        """
        job_template_with_extra_vars.ask_variables_on_launch = True
        launch = job_template_with_extra_vars.related.launch.get()

        # assert values on launch resource
        assert not launch.can_start_without_user_input
        assert launch.ask_variables_on_launch
        assert not launch.passwords_needed_to_start
        assert not launch.variables_needed_to_start
        assert not launch.credential_needed_to_start

        # launch job_template and assert successful completion
        job = job_template_with_extra_vars.launch(dict(extra_vars=launch_time_extra_vars)).wait_until_completed()
        assert job.is_successful, "job unsuccessful - %s" % job

        loaded_jt_vars = self.load_json_or_yaml(job_template_with_extra_vars.extra_vars)
        loaded_launchtime_vars = self.load_json_or_yaml(launch_time_extra_vars)
        loaded_job_vars = self.load_json(job.extra_vars)

        # assert expected job extra_vars
        assert set(loaded_jt_vars) < set(loaded_job_vars)
        assert set(loaded_launchtime_vars) < set(loaded_job_vars)
        assert set(loaded_job_vars) == set(loaded_jt_vars) | set(loaded_job_vars)
        assert loaded_job_vars['intersection'] == loaded_launchtime_vars['intersection'], \
            "A launch-time extra_var did not replace a job_template extra_var."

    def test_launch_with_excluded_variables_in_payload(self, job_template, launch_time_extra_vars):
        """Tests that when ask_variables_at_launch is disabled that launch-time variables get
        ignored.
        """
        assert not job_template.ask_variables_on_launch

        # launch JT with launch-time variables
        job = job_template.launch(dict(extra_vars=launch_time_extra_vars)).wait_until_completed()
        assert job.is_successful, "Job unsuccessful - %s." % job

        # assert launchtime variables excluded
        loaded_job_extra_vars = self.load_json(job.extra_vars)
        assert loaded_job_extra_vars == {}, \
            "Unexpected value for job extra variables - {0}.".format(job.extra_vars)

    @pytest.mark.parametrize("launchtime_vars", [
        '{"non_survey_variable": false, "submitter_email": "sample_email@maffenmox.edu"}',
        "---\nnon_survey_variable: false\nsubmitter_email: sample_email@maffenmox.edu"
    ], ids=['json', 'yaml'])
    def test_launch_with_survey_and_excluded_variables_in_payload(self, job_template, optional_survey_spec_without_defaults,
            launchtime_vars):
        """Tests that when ask_variables_at_launch is disabled that non-survey variables get
        ignored and survey variables make it to our job. Note: "submitter_email" is our only
        survey variable.
        """
        job_template.add_survey(spec=optional_survey_spec_without_defaults)
        assert not job_template.ask_variables_on_launch

        # launch JT with launch-time variables
        payload = dict(extra_vars=launchtime_vars)
        job = job_template.launch(payload).wait_until_completed()
        assert job.is_successful, "Job unsuccessful - %s." % job

        loaded_runtime_vars = self.load_json_or_yaml(launchtime_vars)
        loaded_job_extra_vars = self.load_json(job.extra_vars)

        # assert non-survey variables excluded
        expected_job_vars = dict(submitter_email=loaded_runtime_vars['submitter_email'])
        assert loaded_job_extra_vars == expected_job_vars, \
            "Unexpected job extra_vars returned."

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
        assert job_pg.is_successful, "Job unsuccessful - %s." % job_pg

        # assess job results for limit
        assert job_pg.ask_limit_on_launch
        assert job_pg.limit == "local", "Unexpected value for job_pg.limit. Expected 'local', got %s." % job_pg.limit
        assert '"-l", "local"' in job_pg.job_args, "Limit value not passed to job_args."

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

    @pytest.mark.ansible_integration
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

    def test_launch_without_credential(self, job_template_no_credential):
        """Verify the job->launch endpoint does not allow launching a job_template
        that has no associated credential.
        """
        launch_pg = job_template_no_credential.get_related('launch')

        # assert values on launch resource
        assert not launch_pg.can_start_without_user_input
        assert not launch_pg.ask_variables_on_launch
        assert not launch_pg.passwords_needed_to_start
        assert not launch_pg.variables_needed_to_start
        assert launch_pg.credential_needed_to_start

        # launch the job_template without providing a credential
        with pytest.raises(towerkit.exceptions.BadRequest):
            launch_pg.post()

    def test_launch_with_credential_in_payload(self, job_template_no_credential, ssh_credential):
        """Verify the job->launch endpoint behaves as expected"""
        launch_pg = job_template_no_credential.get_related('launch')

        # assert values on launch resource
        assert not launch_pg.can_start_without_user_input
        assert not launch_pg.ask_variables_on_launch
        assert not launch_pg.passwords_needed_to_start
        assert not launch_pg.variables_needed_to_start
        assert launch_pg.credential_needed_to_start

        # launch the job_template providing the credential in the payload
        payload = dict(credential=ssh_credential.id)
        job_pg = job_template_no_credential.launch(payload).wait_until_completed()

        # assert success
        assert job_pg.is_successful, "Job unsuccessful - %s" % job_pg

        # assert job is associated with the expected credential
        assert job_pg.credential == ssh_credential.id, \
            "A job_template was launched with a credential in the payload, but" \
            "the launched job does not have the same credential " \
            "(%s != %s)" % (job_pg.credential, ssh_credential.id)

    def test_launch_with_team_credential(self, job_template_no_credential, team_with_org_admin, team_ssh_credential, user_password):
        """Verifies that a team user can use a team credential to launch a job template."""
        team_user = team_with_org_admin.get_related('users').results[0]
        with self.current_user(team_user.username, user_password):
            launch_pg = job_template_no_credential.get_related('launch')

            # assert values on launch resource
            assert not launch_pg.can_start_without_user_input
            assert not launch_pg.ask_variables_on_launch
            assert not launch_pg.passwords_needed_to_start
            assert not launch_pg.variables_needed_to_start
            assert launch_pg.credential_needed_to_start

            # launch the job_template providing the credential in the payload
            payload = dict(credential=team_ssh_credential.id)
            job_pg = job_template_no_credential.launch(payload).wait_until_completed()

            # assert success
            assert job_pg.is_successful, "Job unsuccessful - %s" % job_pg

            # assert job is associated with the expected credential
            assert job_pg.credential == team_ssh_credential.id, \
                "A job_template was launched with a credential in the payload, but" \
                "the launched job does not have the same credential " \
                "(%s != %s)" % (job_pg.credential, team_ssh_credential.id)

    def test_launch_with_invalid_credential_in_payload(self, job_template_no_credential):
        """Verify the job->launch endpoint behaves as expected when launched with
        a bogus credential id.
        """
        launch_pg = job_template_no_credential.get_related('launch')

        # assert values on launch resource
        assert not launch_pg.can_start_without_user_input
        assert not launch_pg.ask_variables_on_launch
        assert not launch_pg.passwords_needed_to_start
        assert not launch_pg.variables_needed_to_start
        assert launch_pg.credential_needed_to_start

        # launch the job_template providing a bogus credential in payload
        for bogus in ['', 'one', 0, False, [], {}]:
            payload = dict(credential=bogus)
            with pytest.raises(towerkit.exceptions.BadRequest):
                job_template_no_credential.launch(payload).wait_until_completed()

    def test_launch_with_ask_credential_and_without_passwords_in_payload(self, job_template_no_credential,
                                                                         ssh_credential_multi_ask):
        """Verify that attempts to launch a JT when providing an ask-credential at launch-time without
        providing the required passwords get rejected.
        """
        launch = job_template_no_credential.related.launch.get()

        # assert values on launch resource
        assert not launch.can_start_without_user_input
        assert not launch.ask_variables_on_launch
        assert not launch.passwords_needed_to_start
        assert not launch.variables_needed_to_start
        assert launch.credential_needed_to_start

        # launch the JT providing the credential in the payload, but no passwords_needed_to_start
        payload = dict(credential=ssh_credential_multi_ask.id)
        exc_info = pytest.raises(towerkit.exceptions.BadRequest, launch.post, payload)
        result = exc_info.value[1]

        # assert response includes field: passwords_needed_to_start
        assert 'passwords_needed_to_start' in result, \
            "Unexpected API response: {0}.".format(json.dumps(result))

        # assert expected passwords_needed_to_start value
        assert ssh_credential_multi_ask.expected_passwords_needed_to_start == result['passwords_needed_to_start']

    def test_launch_with_ask_credential_and_with_passwords_in_payload(self, job_template_no_credential,
                                                                      ssh_credential_multi_ask):
        """Verify launching a JT when providing an ask-credential at launch-time with required
        passwords.
        """
        launch = job_template_no_credential.related.launch.get()

        # assert values on launch resource
        assert not launch.can_start_without_user_input
        assert not launch.ask_variables_on_launch
        assert not launch.passwords_needed_to_start
        assert not launch.variables_needed_to_start
        assert launch.credential_needed_to_start

        # build a payload containing the credential and passwords
        payload = dict(credential=ssh_credential_multi_ask.id,
                       ssh_password=self.credentials['ssh']['password'],
                       ssh_key_unlock=self.credentials['ssh']['encrypted']['ssh_key_unlock'],
                       vault_password=self.credentials['ssh']['vault_password'],
                       become_password=self.credentials['ssh']['become_password'])

        # launch JT and assert that the job succeeds
        job = job_template_no_credential.launch(payload).wait_until_completed()
        assert job.is_successful, "Job unsuccessful - %s" % job

    @pytest.mark.ansible_integration
    def test_launch_with_unencrypted_ssh_credential(self, ansible_runner, job_template, unencrypted_ssh_credential_with_ssh_key_data):
        """Launch job template with unencrypted ssh_credential"""
        (credential_type, credential_pg) = unencrypted_ssh_credential_with_ssh_key_data

        job_template.patch(credential=credential_pg.id)

        launch_pg = job_template.get_related('launch')
        assert not launch_pg.passwords_needed_to_start
        job_pg = job_template.launch().wait_until_completed()

        # support for OpenSSH credentials was introduced in OpenSSH 6.5
        if credential_type == "unencrypted_open":
            contacted = ansible_runner.command('ssh -V')
            if LooseVersion(contacted.values()[0]['stderr'].split(" ")[0].split("_")[1]) >= LooseVersion("6.5"):
                assert job_pg.is_successful, "Job unsuccessful - %s" % job_pg
            else:
                assert job_pg.status == 'error', "Job did not error as expected - %s" % job_pg
                assert "RuntimeError: It looks like you're trying to use a private key in OpenSSH format" in job_pg.result_traceback, \
                    "Unexpected job_pg.result_traceback when launching a job with a OpenSSH credential: %s." % job_pg.result_traceback

        # assess job launch behavior with other credential types
        else:
            assert job_pg.is_successful, "Job unsuccessful - %s" % job_pg

    @pytest.mark.ansible_integration
    def test_launch_with_encrypted_ssh_credential(self, ansible_runner, job_template, encrypted_ssh_credential_with_ssh_key_data):
        """Launch job template with encrypted ssh_credential"""
        (credential_type, credential_pg) = encrypted_ssh_credential_with_ssh_key_data

        job_template.patch(credential=credential_pg.id)

        launch_pg = job_template.get_related('launch')
        assert launch_pg.passwords_needed_to_start == [u'ssh_key_unlock']
        payload = dict(ssh_key_unlock="fo0m4nchU")
        job_pg = job_template.launch(payload).wait_until_completed()

        # support for OpenSSH credentials was introduced in OpenSSH 6.5
        if credential_type == "encrypted_open":
            contacted = ansible_runner.command('ssh -V')
            if LooseVersion(contacted.values()[0]['stderr'].split(" ")[0].split("_")[1]) >= LooseVersion("6.5"):
                assert job_pg.is_successful, "Job unsuccessful - %s" % job_pg
            else:
                assert job_pg.status == 'error', "Job did not error as expected - %s" % job_pg
                assert "RuntimeError: It looks like you're trying to use a private key in OpenSSH format" in job_pg.result_traceback, \
                    "Unexpected job_pg.result_traceback when launching a job with a OpenSSH credential: %s." % job_pg.result_traceback

        # assess job launch behavior with other credential types
        else:
            assert job_pg.is_successful, "Job unsuccessful - %s" % job_pg

    def test_launch_without_ask_variables_on_launch(self, job_template_ask_variables_on_launch):
        """Verify behavior when ask_variables_on_launch is enabled but no variables are provided
        at launch-time.
        """
        launch = job_template_ask_variables_on_launch.related.launch.get()

        # assert values on launch resource
        assert not launch.can_start_without_user_input
        assert launch.ask_variables_on_launch
        assert not launch.passwords_needed_to_start
        assert not launch.variables_needed_to_start
        assert not launch.credential_needed_to_start

        # launch the JT and assert successful
        job = job_template_ask_variables_on_launch.launch().wait_until_completed()
        assert job.is_successful, "Job unsuccessful - {0}".format(job)

        loaded_job_vars = self.load_json(job.extra_vars)
        assert loaded_job_vars == {}, \
            "No variables were provided at launch-time " \
            "but our job contains extra variables - {0}.".format(job.extra_vars)

    def test_launch_with_ask_variables_on_launch(self, job_template_ask_variables_on_launch,
            launch_time_extra_vars):
        """Verify behavior when ask_variables_on_launch is enabled and variables are provided
        at launch-time.
        """
        launch = job_template_ask_variables_on_launch.related.launch.get()

        # assert values on launch resource
        assert not launch.can_start_without_user_input
        assert launch.ask_variables_on_launch
        assert not launch.passwords_needed_to_start
        assert not launch.variables_needed_to_start
        assert not launch.credential_needed_to_start

        # launch the JT and assert successful
        payload = dict(extra_vars=launch_time_extra_vars)
        job = job_template_ask_variables_on_launch.launch(payload).wait_until_completed()

        loaded_runtime_vars = self.load_json_or_yaml(launch_time_extra_vars)
        loaded_job_vars = self.load_json(job.extra_vars)
        assert loaded_runtime_vars == loaded_job_vars

    def test_launch_without_variables_needed_to_start(self, job_template_variables_needed_to_start):
        """Verify the job->launch endpoint behaves as expected when launching a
        survey without required variables.
        """
        launch_pg = job_template_variables_needed_to_start.get_related('launch')
        survey_spec = job_template_variables_needed_to_start.get_related('survey_spec')

        print json.dumps(launch_pg.json, indent=2)

        # assert values on launch resource
        assert not launch_pg.can_start_without_user_input
        assert not launch_pg.ask_variables_on_launch
        assert not launch_pg.passwords_needed_to_start
        assert launch_pg.variables_needed_to_start
        assert not launch_pg.credential_needed_to_start

        # assert number of required variables
        required_variables = [question['variable']
                              for question in survey_spec.spec
                              if question.get('required', False)]
        assert len(launch_pg.variables_needed_to_start) == len(required_variables), \
            "Unexpected number of required variables (%s != %s)" % \
            (len(launch_pg.variables_needed_to_start), len(required_variables))

        # assert names of required variables
        for variable in required_variables:
            assert variable in launch_pg.variables_needed_to_start, \
                "Missing required variable: %s" % variable

        # launch the job without provided required variables
        exc_info = pytest.raises(towerkit.exceptions.BadRequest, launch_pg.post)
        result = exc_info.value[1]

        # assert response includes field: passwords_needed_to_start
        assert 'variables_needed_to_start' in result, \
            "Expecting 'variables_needed_to_start' in API response when " \
            "launching a job_template, without required variables. %s " % \
            json.dumps(result)

        # assert number of required variables
        assert len(result['variables_needed_to_start']) == len(required_variables), \
            "Unexpected number of required variables returned when issuing a POST to the /launch endpoint(%s != %s)" % \
            (len(result['variables_needed_to_start']), len(required_variables))

        # assert names of required variables without a default value
        required_variables_without_default = [question['variable']
                                              for question in survey_spec.spec
                                              if question.get('required', False) and
                                              question.get('default') in (None, '')]
        for variable in required_variables_without_default:
            assert variable in launch_pg.variables_needed_to_start, \
                "Missing required variable: %s" % variable

    def test_launch_with_variables_needed_to_start(self, job_template_variables_needed_to_start):
        """Verify the job->launch endpoint behaves as expected when a survey is enabled"""
        launch_pg = job_template_variables_needed_to_start.related.launch.get()
        survey_spec = job_template_variables_needed_to_start.related.survey_spec.get()

        # assert values on launch resource
        assert not launch_pg.can_start_without_user_input
        assert not launch_pg.ask_variables_on_launch
        assert not launch_pg.passwords_needed_to_start
        assert launch_pg.variables_needed_to_start
        assert not launch_pg.credential_needed_to_start

        # assert number of required variables
        required_variables = [question['variable']
                              for question in survey_spec.spec
                              if question.get('required', False)]
        assert len(launch_pg.variables_needed_to_start) == len(required_variables), \
            "Unexpected number of required variables (%s != %s)" % \
            (len(launch_pg.variables_needed_to_start), len(required_variables))

        # assert names of required variables
        for variable in required_variables:
            assert variable in launch_pg.variables_needed_to_start, \
                "Missing required variable: %s" % variable

        # launch the job_template
        payload = dict(extra_vars=dict(likes_chicken=["yes"], favorite_color="green"))
        job = job_template_variables_needed_to_start.launch(payload).wait_until_completed()
        assert job.is_successful, "Job unsuccessful - %s" % job

        # coerce job extra_vars into a dictionary
        try:
            job_extra_vars = json.loads(job.extra_vars)
        except ValueError:
            job_extra_vars = {}

        # find job vars from survey defaults
        survey_default_vars = dict((question['variable'], question['default'])
                                   for question in survey_spec.spec
                                   if question.get('required', False) is False and
                                   question.get('default') not in (None, ''))

        # assert extra_vars contains provided data
        assert set(job_extra_vars) == set(survey_default_vars) | set(payload['extra_vars'])

    def test_launch_with_variables_needed_to_start_and_extra_vars_at_launch(self, job_template_with_extra_vars, required_survey_spec,
                                                                            launch_time_extra_vars, tower_version_cmp):
        """Verify that when launch-time extra_vars are provided, the job
        extra_variables are a union of the job_template variables, survey
        variables, and launch-time variables.
        """
        job_template_with_extra_vars.ask_variables_on_launch = True
        job_template_with_extra_vars.add_survey(spec=required_survey_spec)
        launch = job_template_with_extra_vars.related.launch.get()
        survey_spec = job_template_with_extra_vars.related.survey_spec.get()

        # find future job variables that come exclusively from the survey
        survey_vars = [question['variable']
                       for question in survey_spec.spec
                       if (question.get('required', False) is False and
                       (question.get('default') not in (None, '')))]

        # assert values on launch resource
        assert not launch_pg.can_start_without_user_input
        assert launch_pg.ask_variables_on_launch
        assert not launch_pg.passwords_needed_to_start
        assert launch_pg.variables_needed_to_start
        assert not launch_pg.credential_needed_to_start

        # assert number of required variables
        required_variables = [question['variable']
                              for question in survey_spec.spec
                              if (question.get('required', False) is True)]
        assert len(launch_pg.variables_needed_to_start) == len(required_variables), \
            "Unexpected number of required variables (%s != %s)" % \
            (len(launch_pg.variables_needed_to_start), len(required_variables))

        # assert names of required variables
        for variable in required_variables:
            assert variable in launch_pg.variables_needed_to_start, \
                "Missing required variable: %s" % variable

        # launch job_template and assert successful completion
        launch_time_extra_vars.update(dict(likes_chicken=["yes"], favorite_color="green"))
        job = job_template_with_extra_vars.launch(dict(extra_vars=launch_time_extra_vars)).wait_until_completed()
        assert job.is_successful, "job unsuccessful - %s" % job

        # format job extra_vars
        try:
            job_extra_vars = json.loads(job_pg.extra_vars)
        except ValueError:
            job_extra_vars = {}

        # variable precedence changed in 2.4.0
        if tower_version_cmp('2.4.0') < 0:
            # assert job.extra_vars match the launch-time extra_vars
            assert job_extra_vars == launch_time_extra_vars

        else:
            # coerce extra_vars into a dictionary for a proper comparison
            try:
                job_template_extra_vars = json.loads(job_template_with_extra_vars.extra_vars)
            except ValueError:
                job_template_extra_vars = {}

            # assert the job_template extra_vars are a subset of the job extra_vars
            assert set(job_template_extra_vars) < set(job_extra_vars)

            # assert the survey extra_vars are a subset of the job extra_vars
            assert set(survey_vars) < set(job_extra_vars)

            # assert the launch-time extra_vars are a subset of the job extra_vars
            assert set(launch_time_extra_vars) < set(job_extra_vars)

            # assert the job extra_vars are a union of the job_template, survey, and launch-time extra_vars
            assert set(job_extra_vars) == set(job_template_extra_vars) | set(survey_vars) | set(launch_time_extra_vars)

            # assert that launch-time extra_vars take precedence over job template and survey extra_vars
            assert job_extra_vars['intersection'] == u'job', \
                "A launch-time extra_var did not replace a job_template extra_var and survey extra_var as expected."

    def test_launch_without_passwords_needed_to_start(self, job_template_passwords_needed_to_start):
        """Verify the job->launch endpoint behaves as expected when passwords are needed to start"""
        launch_pg = job_template_passwords_needed_to_start.get_related('launch')

        # assert values on launch resource
        assert not launch_pg.can_start_without_user_input
        assert not launch_pg.ask_variables_on_launch
        assert launch_pg.passwords_needed_to_start
        assert not launch_pg.variables_needed_to_start
        assert not launch_pg.credential_needed_to_start

        # assert expected values in launch_pg.passwords_needed_to_start
        credential = job_template_passwords_needed_to_start.get_related('credential')
        assert credential.expected_passwords_needed_to_start == launch_pg.passwords_needed_to_start

        # launch the job_template without passwords
        with pytest.raises(towerkit.exceptions.BadRequest):
            launch_pg.post()

        # prepare payload with empty passwords
        payload = dict(ssh_password='', ssh_key_unlock='', become_password='')

        # launch the job_template
        with pytest.raises(towerkit.exceptions.BadRequest):
            launch_pg.post(payload)

    def test_launch_with_passwords_needed_to_start(self, job_template_passwords_needed_to_start):
        """Verify the job->launch endpoint behaves as expected when passwords are needed to start"""
        launch_pg = job_template_passwords_needed_to_start.get_related('launch')

        print json.dumps(launch_pg.json, indent=2)

        # assert values on launch resource
        assert not launch_pg.can_start_without_user_input
        assert not launch_pg.ask_variables_on_launch
        assert launch_pg.passwords_needed_to_start
        assert not launch_pg.variables_needed_to_start
        assert not launch_pg.credential_needed_to_start

        # assert expected passwords_needed_to_start
        credential = job_template_passwords_needed_to_start.get_related('credential')
        assert credential.expected_passwords_needed_to_start == launch_pg.passwords_needed_to_start

        # prepare payload with passwords
        payload = dict(ssh_password=self.credentials['ssh']['password'],
                       ssh_key_unlock=self.credentials['ssh']['encrypted']['ssh_key_unlock'],
                       vault_password=self.credentials['ssh']['vault_password'],
                       become_password=self.credentials['ssh']['become_password'])

        # launch the job_template
        job_pg = job_template_passwords_needed_to_start.launch(payload).wait_until_completed()

        # assert success
        assert job_pg.is_successful, "Job unsuccessful - %s" % job_pg

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


@pytest.mark.api
@pytest.mark.skip_selenium
@pytest.mark.destructive
class Test_Job_Template_Survey_Spec(Base_Api_Test):
    """Test job_template surveys"""

    pytestmark = pytest.mark.usefixtures('authtoken', 'install_enterprise_license_unlimited')

    def test_post_with_missing_fields(self, job_template_ping, missing_field_survey_specs):
        """Verify the API does not allow survey creation when missing any or all
        of the spec, name, or description fields.
        """
        job_template_ping.patch(survey_enabled=True)

        # assert failure on post
        for payload in missing_field_survey_specs:
            with pytest.raises(towerkit.exceptions.BadRequest):
                job_template_ping.get_related('survey_spec').post(payload)

    def test_post_with_empty_name(self, job_template_ping):
        """Verify the API allows a survey_spec with an empty name and description"""
        job_template_ping.patch(survey_enabled=True)
        payload = dict(name='',
                       description='',
                       spec=[dict(required=False,
                                  question_name=fauxfactory.gen_utf8(),
                                  question_description=fauxfactory.gen_utf8(),
                                  variable="submitter_email",
                                  type="text",)])

        # assert successful post
        job_template_ping.get_related('survey_spec').post(payload)

    def test_post_multiple(self, job_template_ping, optional_survey_spec, required_survey_spec):
        """Verify the API allows posting survey_spec multiple times."""
        # post a survey
        job_template_ping.add_survey(spec=optional_survey_spec)
        survey_spec = job_template_ping.get_related('survey_spec')
        assert survey_spec.spec == optional_survey_spec

        # post another survey
        job_template_ping.add_survey(spec=required_survey_spec)
        # update resource
        survey_spec.get()
        assert survey_spec.spec == required_survey_spec

    def test_launch_survey_enabled(self, job_template_ping, required_survey_spec):
        """Assess launch_pg.survey_enabled behaves as expected."""
        # check that survey_enabled is false by default
        launch_pg = job_template_ping.get_related("launch")
        assert not launch_pg.survey_enabled, \
            "launch_pg.survey_enabled is True even though JT survey_enabled is False \
            and no survey given."

        # check that survey_enabled is false when enabled on JT but no survey created
        job_template_ping.patch(survey_enabled=True)
        launch_pg = job_template_ping.get_related("launch")
        assert not launch_pg.survey_enabled, \
            "launch_pg.survey_enabled is True with JT survey_enabled as True \
            and no survey given."

        # check that survey_enabled is true when enabled on JT and survey created
        survey_spec = job_template_ping.get_related('survey_spec')
        survey_spec.post(required_survey_spec)
        launch_pg = job_template_ping.get_related("launch")
        assert launch_pg.survey_enabled, \
            "launch_pg.survey_enabled is False even though JT survey_enabled is True \
            and valid survey posted."

    def test_launch_with_optional_survey_spec(self, job_template_ping, optional_survey_spec):
        """Verify launch_pg attributes with an optional survey spec and job extra_vars."""
        # post a survey
        job_template_ping.add_survey(spec=optional_survey_spec)
        survey_pg = job_template_ping.get_related('survey_spec')

        # assess launch_pg values
        launch_pg = job_template_ping.get_related('launch')
        assert launch_pg.can_start_without_user_input
        assert launch_pg.variables_needed_to_start == []

        # launch the job_template and assess results
        job_pg = job_template_ping.launch().wait_until_completed()
        assert job_pg.is_successful, "Job unsuccessful - %s" % job_pg

        # format job extra_vars
        try:
            job_extra_vars = json.loads(job_pg.extra_vars)
        except ValueError:
            job_extra_vars = {}

        # find expected job extra_vars from survey
        survey_extra_vars = dict((question['variable'], question['default'])
                                 for question in survey_pg.spec
                                 if question.get('required', False) is False and
                                 question.get('default') not in (None, ''))

        # assert expected job extra_vars
        assert set(job_extra_vars) == set(survey_extra_vars)
