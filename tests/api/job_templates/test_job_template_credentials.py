from distutils.version import LooseVersion
import logging

from towerkit.config import config
import towerkit.tower.inventory
import towerkit.exceptions
import pytest

from tests.api import Base_Api_Test


log = logging.getLogger(__name__)


class TestJobTemplateCredentials(Base_Api_Test):

    pytestmark = pytest.mark.usefixtures('authtoken', 'install_enterprise_license')

    @pytest.mark.ha_tower
    def test_launch_without_credential_and_credential_needed_to_start(self, job_template_no_credential):
        """Verify the job launch endpoint disallows launching a job template without a credential."""
        launch = job_template_no_credential.related.launch.get()

        assert not launch.can_start_without_user_input
        assert not launch.ask_variables_on_launch
        assert not launch.passwords_needed_to_start
        assert not launch.variables_needed_to_start
        assert launch.credential_needed_to_start

        # launch the job_template without providing a credential
        with pytest.raises(towerkit.exceptions.BadRequest):
            launch.post()

    @pytest.mark.ha_tower
    def test_launch_with_linked_credential(self, job_template_no_credential, ssh_credential):
        """Verify the job template launch endpoint requires user input when using a linked credential and
        `ask_credential_on_launch`.
        """
        job_template_no_credential.credential = ssh_credential.id
        launch = job_template_no_credential.related.launch.get()

        assert not launch.can_start_without_user_input
        assert not launch.ask_variables_on_launch
        assert not launch.passwords_needed_to_start
        assert not launch.variables_needed_to_start
        assert not launch.credential_needed_to_start

        job = job_template_no_credential.launch().wait_until_completed()

        assert job.is_successful
        assert job.credential == ssh_credential.id

    @pytest.mark.ha_tower
    def test_launch_with_payload_credential_and_credential_needed_to_start(self, job_template_no_credential,
                                                                           ssh_credential):
        """Verify the job launch endpoint allows launching a job template when providing a credential."""
        launch = job_template_no_credential.related.launch.get()

        assert not launch.can_start_without_user_input
        assert not launch.ask_variables_on_launch
        assert not launch.passwords_needed_to_start
        assert not launch.variables_needed_to_start
        assert launch.credential_needed_to_start

        job = job_template_no_credential.launch(dict(credential=ssh_credential.id)).wait_until_completed()

        assert job.is_successful
        assert job.credential == ssh_credential.id

    @pytest.mark.ha_tower
    def test_launch_with_invalid_credential_in_payload(self, job_template_no_credential):
        """Verify the job launch endpoint throws 400 error when launching with invalid credential id"""
        for bogus in ['', 'one', 0, False, [], {}]:
            with pytest.raises(towerkit.exceptions.BadRequest):
                job_template_no_credential.launch(dict(credential=bogus))

    @pytest.mark.ha_tower
    def test_launch_with_ask_credential_and_without_passwords_in_payload(self, job_template_no_credential,
                                                                         ssh_credential_ask):
        """Verify that attempts to launch a JT when providing an 'ASK' credential at launch time without
        providing the required passwords raise 400 error.
        """
        launch = job_template_no_credential.related.launch.get()

        # launch the JT providing the credential in the payload, but no passwords_needed_to_start
        with pytest.raises(towerkit.exceptions.BadRequest) as exc_info:
            launch.post(dict(credential=ssh_credential_ask.id))
        result = exc_info.value[1]

        assert 'passwords_needed_to_start' in result
        assert result['passwords_needed_to_start'] == ssh_credential_ask.expected_passwords_needed_to_start

    @pytest.mark.ha_tower
    def test_launch_with_ask_credential_and_passwords_in_payload(self, job_template_no_credential, ssh_credential_ask):
        """Verify launching a JT when providing an 'ASK' credential at launch time with required passwords
        is functional
        """
        job = job_template_no_credential.launch(dict(credential=ssh_credential_ask.id,
                                                     ssh_password=config.credentials.ssh.password,
                                                     ssh_key_unlock=config.credentials.ssh.encrypted.ssh_key_unlock,
                                                     become_password=config.credentials.ssh.become_password))
        assert job.wait_until_completed().is_successful
        assert job.credential == ssh_credential_ask.id

    @pytest.mark.ansible_integration
    @pytest.mark.ha_tower
    def test_launch_with_unencrypted_ssh_credential(self, ansible_runner, job_template,
                                                    unencrypted_ssh_credential_with_ssh_key_data):
        (credential_type, credential) = unencrypted_ssh_credential_with_ssh_key_data

        job_template.credential = credential.id

        launch = job_template.related.launch.get()
        assert not launch.passwords_needed_to_start

        job = job_template.launch().wait_until_completed()

        # support for OpenSSH credentials was introduced in OpenSSH 6.5
        if credential_type == "unencrypted_open":
            contacted = ansible_runner.command('ssh -V')
            if LooseVersion(contacted.values()[0]['stderr'].split(" ")[0].split("_")[1]) >= LooseVersion("6.5"):
                assert job.is_successful
            else:
                assert job.status == 'error'
                runtime_error = "RuntimeError: It looks like you're trying to use a private key in OpenSSH format"
                assert runtime_error in job.result_traceback
        else:
            assert job.is_successful

    @pytest.mark.ansible_integration
    @pytest.mark.ha_tower
    def test_launch_with_encrypted_ssh_credential(self, ansible_runner, job_template,
                                                  encrypted_ssh_credential_with_ssh_key_data):
        (credential_type, credential) = encrypted_ssh_credential_with_ssh_key_data

        job_template.credential = credential.id

        launch = job_template.get_related('launch')
        assert launch.passwords_needed_to_start == [u'ssh_key_unlock']

        job = job_template.launch(dict(ssh_key_unlock='fo0m4nchU'))
        job.wait_until_completed()

        # support for OpenSSH credentials was introduced in OpenSSH 6.5
        if credential_type == "encrypted_open":
            contacted = ansible_runner.command('ssh -V')
            if LooseVersion(contacted.values()[0]['stderr'].split(" ")[0].split("_")[1]) >= LooseVersion("6.5"):
                assert job.is_successful
            else:
                assert job.status == 'error'
                runtime_error = "RuntimeError: It looks like you're trying to use a private key in OpenSSH format"
                assert runtime_error in job.result_traceback
        else:
            assert job.is_successful

    @pytest.mark.ha_tower
    def test_launch_with_team_credential(self, factories, job_template_no_credential, team_with_org_admin,
                                         team_ssh_credential):
        """Verifies that a team user can use a team credential to launch a job template."""
        team_user = factories.user()
        team_with_org_admin.add_user(team_user)
        job_template_no_credential.set_object_roles(team_user, 'execute')

        with self.current_user(team_user.username, team_user.password):
            job = job_template_no_credential.launch(dict(credential=team_ssh_credential.id)).wait_until_completed()
            assert job.is_successful
            assert job.credential == team_ssh_credential.id
