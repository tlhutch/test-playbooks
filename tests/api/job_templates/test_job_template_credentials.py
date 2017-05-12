from distutils.version import LooseVersion
import logging
import json

import towerkit.tower.inventory
import towerkit.exceptions
import pytest

from tests.api import Base_Api_Test


log = logging.getLogger(__name__)


class TestJobTemplateCredentials(Base_Api_Test):

    pytestmark = pytest.mark.usefixtures('authtoken', 'install_enterprise_license')

    def test_launch_without_credential_and_credential_needed_to_start(self, job_template_no_credential):
        """Verify the job launch endpoint disallows launching a job template without a credential."""
        launch = job_template_no_credential.get_related('launch')

        assert not launch.can_start_without_user_input
        assert not launch.ask_variables_on_launch
        assert not launch.passwords_needed_to_start
        assert not launch.variables_needed_to_start
        assert launch.credential_needed_to_start

        # launch the job_template without providing a credential
        with pytest.raises(towerkit.exceptions.BadRequest):
            launch.post()

    def test_launch_with_credential_and_credential_needed_to_start(self, job_template_no_credential, ssh_credential):
        """Verify the job launch endpoint allows launching a job template when providing a credential."""
        launch = job_template_no_credential.get_related('launch')

        assert not launch.can_start_without_user_input
        assert not launch.ask_variables_on_launch
        assert not launch.passwords_needed_to_start
        assert not launch.variables_needed_to_start
        assert launch.credential_needed_to_start

        job = job_template_no_credential.launch(dict(credential=ssh_credential.id)).wait_until_completed()

        assert job.is_successful
        assert job.credential == ssh_credential.id

    def test_launch_with_team_credential(self, job_template_no_credential, team_with_org_admin, team_ssh_credential):
        """Verifies that a team user can use a team credential to launch a job template."""
        team_user = team_with_org_admin.get_related('users').results[0]
        with self.current_user(team_user.username, team_user.password):
            launch = job_template_no_credential.get_related('launch')

            # assert values on launch resource
            assert not launch.can_start_without_user_input
            assert not launch.ask_variables_on_launch
            assert not launch.passwords_needed_to_start
            assert not launch.variables_needed_to_start
            assert launch.credential_needed_to_start

            # launch the job_template providing the credential in the payload
            payload = dict(credential=team_ssh_credential.id)
            job = job_template_no_credential.launch(payload).wait_until_completed()

            # assert success
            assert job.is_successful, "Job unsuccessful - %s" % job

            # assert job is associated with the expected credential
            assert job.credential == team_ssh_credential.id, \
                "A job_template was launched with a credential in the payload, but" \
                "the launched job does not have the same credential " \
                "(%s != %s)" % (job.credential, team_ssh_credential.id)

    def test_launch_with_invalid_credential_in_payload(self, job_template_no_credential):
        """Verify the job->launch endpoint behaves as expected when launched with
        a bogus credential id.
        """
        launch = job_template_no_credential.get_related('launch')

        # assert values on launch resource
        assert not launch.can_start_without_user_input
        assert not launch.ask_variables_on_launch
        assert not launch.passwords_needed_to_start
        assert not launch.variables_needed_to_start
        assert launch.credential_needed_to_start

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
                       become_password=self.credentials['ssh']['become_password'])

        # launch JT and assert successful
        job = job_template_no_credential.launch(payload).wait_until_completed()
        assert job.is_successful, "Job unsuccessful - %s" % job

        assert job.credential == ssh_credential_multi_ask.id

    @pytest.mark.ansible_integration
    def test_launch_with_unencrypted_ssh_credential(self, ansible_runner, job_template,
                                                    unencrypted_ssh_credential_with_ssh_key_data):
        """Launch job template with unencrypted ssh_credential"""
        (credential_type, credential_pg) = unencrypted_ssh_credential_with_ssh_key_data

        job_template.patch(credential=credential_pg.id)

        launch = job_template.get_related('launch')
        assert not launch.passwords_needed_to_start
        job = job_template.launch().wait_until_completed()

        # support for OpenSSH credentials was introduced in OpenSSH 6.5
        if credential_type == "unencrypted_open":
            contacted = ansible_runner.command('ssh -V')
            if LooseVersion(contacted.values()[0]['stderr'].split(" ")[0].split("_")[1]) >= LooseVersion("6.5"):
                assert job.is_successful, "Job unsuccessful - %s" % job
            else:
                assert job.status == 'error', "Job did not error as expected - %s" % job
                assert "RuntimeError: It looks like you're trying to use a private key in OpenSSH format" in job.result_traceback, \
                    "Unexpected job.result_traceback when launching a job with a OpenSSH credential: %s." % job.result_traceback

        # assess job launch behavior with other credential types
        else:
            assert job.is_successful, "Job unsuccessful - %s" % job

    @pytest.mark.ansible_integration
    def test_launch_with_encrypted_ssh_credential(self, ansible_runner, job_template,
                                                  encrypted_ssh_credential_with_ssh_key_data):
        """Launch job template with encrypted ssh_credential"""
        (credential_type, credential_pg) = encrypted_ssh_credential_with_ssh_key_data

        job_template.patch(credential=credential_pg.id)

        launch = job_template.get_related('launch')
        assert launch.passwords_needed_to_start == [u'ssh_key_unlock']
        payload = dict(ssh_key_unlock="fo0m4nchU")
        job = job_template.launch(payload).wait_until_completed()

        # support for OpenSSH credentials was introduced in OpenSSH 6.5
        if credential_type == "encrypted_open":
            contacted = ansible_runner.command('ssh -V')
            if LooseVersion(contacted.values()[0]['stderr'].split(" ")[0].split("_")[1]) >= LooseVersion("6.5"):
                assert job.is_successful, "Job unsuccessful - %s" % job
            else:
                assert job.status == 'error', "Job did not error as expected - %s" % job
                assert "RuntimeError: It looks like you're trying to use a private key in OpenSSH format" in job.result_traceback, \
                    "Unexpected job.result_traceback when launching a job with a OpenSSH credential: %s." % job.result_traceback

        # assess job launch behavior with other credential types
        else:
            assert job.is_successful, "Job unsuccessful - %s" % job

    def test_launch_without_passwords_needed_to_start(self, job_template_passwords_needed_to_start):
        """Verify the job->launch endpoint behaves as expected when passwords are needed to start"""
        launch = job_template_passwords_needed_to_start.get_related('launch')

        # assert values on launch resource
        assert not launch.can_start_without_user_input
        assert not launch.ask_variables_on_launch
        assert launch.passwords_needed_to_start
        assert not launch.variables_needed_to_start
        assert not launch.credential_needed_to_start

        # assert expected values in launch.passwords_needed_to_start
        credential = job_template_passwords_needed_to_start.get_related('credential')
        assert credential.expected_passwords_needed_to_start == launch.passwords_needed_to_start

        # launch the job_template without passwords
        with pytest.raises(towerkit.exceptions.BadRequest):
            launch.post()

        # prepare payload with empty passwords
        payload = dict(ssh_password='', ssh_key_unlock='', become_password='')

        # launch the job_template
        with pytest.raises(towerkit.exceptions.BadRequest):
            launch.post(payload)

    def test_launch_with_passwords_needed_to_start(self, job_template_passwords_needed_to_start):
        """Verify the job->launch endpoint behaves as expected when passwords are needed to start"""
        launch = job_template_passwords_needed_to_start.get_related('launch')

        print json.dumps(launch.json, indent=2)

        # assert values on launch resource
        assert not launch.can_start_without_user_input
        assert not launch.ask_variables_on_launch
        assert launch.passwords_needed_to_start
        assert not launch.variables_needed_to_start
        assert not launch.credential_needed_to_start

        # assert expected passwords_needed_to_start
        credential = job_template_passwords_needed_to_start.get_related('credential')
        assert credential.expected_passwords_needed_to_start == launch.passwords_needed_to_start

        # prepare payload with passwords
        payload = dict(ssh_password=self.credentials['ssh']['password'],
                       ssh_key_unlock=self.credentials['ssh']['encrypted']['ssh_key_unlock'],
                       become_password=self.credentials['ssh']['become_password'])

        # launch the job_template
        job = job_template_passwords_needed_to_start.launch(payload).wait_until_completed()

        # assert success
        assert job.is_successful, "Job unsuccessful - %s" % job
