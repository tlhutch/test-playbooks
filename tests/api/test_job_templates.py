import json
import pytest
import common.tower.inventory
import common.utils
from tests.api import Base_Api_Test


@pytest.fixture(scope="function")
def missing_field_survey_specs(request):
    '''
    Returns a list of survey_spec's which should fail to post.
    '''
    return [dict(),
            dict(description=common.utils.random_unicode(),
                 spec=[dict(required=False,
                            question_name="Enter your email &mdash; &euro;",
                            variable="submitter_email",
                            type="text",)]),
            dict(name=common.utils.random_unicode(),
                 spec=[dict(required=False,
                            question_name="Enter your email &mdash; &euro;",
                            variable="submitter_email",
                            type="text",)]),
            dict(name=common.utils.random_unicode(),
                 description=common.utils.random_unicode()),
            dict(name=common.utils.random_unicode(),
                 description=common.utils.random_unicode(),
                 spec=[])]


@pytest.mark.api
@pytest.mark.skip_selenium
@pytest.mark.destructive
class Test_Job_Template(Base_Api_Test):

    pytestmark = pytest.mark.usefixtures('authtoken', 'backup_license', 'install_license_unlimited')

    def test_launch(self, job_template_ping):
        '''
        Verify the job->launch endpoint behaves as expected
        '''
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

    def test_launch_without_credential(self, job_template_no_credential):
        '''
        Verify the job->launch endpoint does not allow launching a job_template
        that has no associated credential.
        '''
        launch_pg = job_template_no_credential.get_related('launch')

        # assert values on launch resource
        assert not launch_pg.can_start_without_user_input
        assert not launch_pg.ask_variables_on_launch
        assert not launch_pg.passwords_needed_to_start
        assert not launch_pg.variables_needed_to_start
        assert launch_pg.credential_needed_to_start

        # launch the job_template without providing a credential
        with pytest.raises(common.exceptions.BadRequest_Exception):
            launch_pg.post()

    def test_launch_with_credential_in_payload(self, job_template_no_credential, ssh_credential):
        '''
        Verify the job->launch endpoint behaves as expected
        '''
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

    @pytest.mark.trello('https://trello.com/c/Iu5H2gHM', 'https://trello.com/c/gcllkAT7')
    def test_launch_with_invalid_credential_in_payload(self, job_template_no_credential):
        '''
        Verify the job->launch endpoint behaves as expected when launched with
        a bogus credential id.
        '''
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
            with pytest.raises(common.exceptions.BadRequest_Exception):
                job_template_no_credential.launch(payload).wait_until_completed()

    def test_launch_with_ask_credential_and_without_passwords_in_payload(self, job_template_no_credential, ssh_credential_multi_ask):
        '''
        Verify that launching a job_template, while providing the credential in
        the payload, behaves as expected.
            * POST with ask credential, but no passwords fails
            * POST with ask credential, and passwords succeeds
        '''
        launch_pg = job_template_no_credential.get_related('launch')

        # assert values on launch resource
        assert not launch_pg.can_start_without_user_input
        assert not launch_pg.ask_variables_on_launch
        assert not launch_pg.passwords_needed_to_start
        assert not launch_pg.variables_needed_to_start
        assert launch_pg.credential_needed_to_start

        # launch the job_template providing the credential in the payload, but no passwords_needed_to_start
        payload = dict(credential=ssh_credential_multi_ask.id)
        exc_info = pytest.raises(common.exceptions.BadRequest_Exception, launch_pg.post, payload)
        result = exc_info.value[1]

        # assert response includes field: passwords_needed_to_start
        assert 'passwords_needed_to_start' in result, \
            "Expecting 'passwords_needed_to_start' in API response when " \
            "launching a job_template, without provided credential " \
            "passwords. %s" % json.dumps(result)

        # assert expected 'passwords_needed_to_start'
        assert ['ssh_password', 'sudo_password', 'ssh_key_unlock',
                'vault_password'] == result['passwords_needed_to_start']

    def test_launch_with_ask_credential_and_with_passwords_in_payload(self, job_template_no_credential, ssh_credential_multi_ask):
        '''
        Verify that launching a job_template, while providing the credential in
        the payload, behaves as expected.
            * POST with ask credential, and passwords succeeds
        '''
        launch_pg = job_template_no_credential.get_related('launch')

        # assert values on launch resource
        assert not launch_pg.can_start_without_user_input
        assert not launch_pg.ask_variables_on_launch
        assert not launch_pg.passwords_needed_to_start
        assert not launch_pg.variables_needed_to_start
        assert launch_pg.credential_needed_to_start

        # build a payload containing the credential and passwords
        payload = dict(credential=ssh_credential_multi_ask.id,
                       ssh_password=self.credentials['ssh']['password'],
                       sudo_password=self.credentials['ssh']['sudo_password'],
                       ssh_key_unlock=self.credentials['ssh']['encrypted']['ssh_key_unlock'],
                       vault_password=self.credentials['ssh']['vault_password'])

        # launch the job_template and wait for completion
        job_pg = job_template_no_credential.launch(payload).wait_until_completed()

        # assert success
        assert job_pg.is_successful, "Job unsuccessful - %s" % job_pg

    def test_launch_without_ask_variables_on_launch(self, job_template_ask_variables_on_launch):
        '''
        Verify the job->launch endpoint behaves as expected when ask_variables_on_launch is enabled
        '''
        launch_pg = job_template_ask_variables_on_launch.get_related('launch')

        # assert values on launch resource
        assert launch_pg.can_start_without_user_input
        assert launch_pg.ask_variables_on_launch
        assert not launch_pg.passwords_needed_to_start
        assert not launch_pg.variables_needed_to_start
        assert not launch_pg.credential_needed_to_start

        # launch the job_template and wait for completion
        job_pg = job_template_ask_variables_on_launch.launch().wait_until_completed()

        # assert job has no extra_vars
        assert job_pg.extra_vars == '', \
            "No extra_vars were provided at launch, " \
            "but the job contains extra_vars (%s)" % (job_pg.extra_vars)

    def test_launch_with_ask_variables_on_launch(self, job_template_ask_variables_on_launch):
        '''
        Verify the job->launch endpoint behaves as expected when ask_variables_on_launch is enabled
        '''
        launch_pg = job_template_ask_variables_on_launch.get_related('launch')

        # assert values on launch resource
        assert launch_pg.can_start_without_user_input
        assert launch_pg.ask_variables_on_launch
        assert not launch_pg.passwords_needed_to_start
        assert not launch_pg.variables_needed_to_start
        assert not launch_pg.credential_needed_to_start

        # launch the job_template
        payload = dict(extra_vars=dict(one=1, two=2, three=3))
        # launch the job_template and wait for completion
        job_pg = job_template_ask_variables_on_launch.launch(payload).wait_until_completed()

        # assert extra_vars contains provided data
        try:
            extra_vars = json.loads(job_pg.extra_vars)
        except ValueError:
            extra_vars = {}
        assert extra_vars == payload['extra_vars'], \
            "The job extra_vars do not match the values provided at launch (%s != %s)" % \
            (extra_vars, payload['extra_vars'])

    def test_launch_without_variables_needed_to_start(self, job_template_variables_needed_to_start):
        '''
        Verify the job->launch endpoint behaves as expected when launching a
        survey without required variables.
        '''
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
        exc_info = pytest.raises(common.exceptions.BadRequest_Exception, launch_pg.post)
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
        '''
        Verify the job->launch endpoint behaves as expected when a survey is enabled
        '''
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

        # TODO - launch the job_template

        # TODO - assert successful launch

        # TODO - assert extra_vars contains provided data

    def test_launch_without_passwords_needed_to_start(self, job_template_passwords_needed_to_start):
        '''
        Verify the job->launch endpoint behaves as expected when passwords are needed to start
        '''
        launch_pg = job_template_passwords_needed_to_start.get_related('launch')

        # assert values on launch resource
        assert not launch_pg.can_start_without_user_input
        assert not launch_pg.ask_variables_on_launch
        assert launch_pg.passwords_needed_to_start
        assert not launch_pg.variables_needed_to_start
        assert not launch_pg.credential_needed_to_start

        # assert expected values in launch_pg.passwords_needed_to_start
        assert ['ssh_password', 'sudo_password', 'ssh_key_unlock',
                'vault_password'] == launch_pg.passwords_needed_to_start

        # launch the job_template without passwords
        with pytest.raises(common.exceptions.BadRequest_Exception):
            launch_pg.post()

        # launch the job_template with empty passwords
        passwords = dict(ssh_password="",
                         sudo_password="",
                         ssh_key_unlock="")
        with pytest.raises(common.exceptions.BadRequest_Exception):
            launch_pg.post(passwords)

    def test_launch_with_passwords_needed_to_start(self, job_template_passwords_needed_to_start):
        '''
        Verify the job->launch endpoint behaves as expected when passwords are needed to start
        '''
        launch_pg = job_template_passwords_needed_to_start.get_related('launch')

        print json.dumps(launch_pg.json, indent=2)

        # assert values on launch resource
        assert not launch_pg.can_start_without_user_input
        assert not launch_pg.ask_variables_on_launch
        assert launch_pg.passwords_needed_to_start
        assert not launch_pg.variables_needed_to_start
        assert not launch_pg.credential_needed_to_start

        # assert expected passwords_needed_to_start
        assert ['ssh_password', 'sudo_password', 'ssh_key_unlock',
                'vault_password'] == launch_pg.passwords_needed_to_start

        # launch the job_template with passwords
        passwords = dict(ssh_password=self.credentials['ssh']['password'],
                         sudo_password=self.credentials['ssh']['sudo_password'],
                         ssh_key_unlock=self.credentials['ssh']['encrypted']['ssh_key_unlock'],
                         vault_password=self.credentials['ssh']['vault_password'])
        job_pg = job_template_passwords_needed_to_start.launch(passwords).wait_until_completed()

        # assert success
        assert job_pg.is_successful, "Job unsuccessful - %s" % job_pg

    def test_delete_template_while_job_is_running(self, job_template_sleep):
        '''
        Verify that tower properly cancels queued jobs when deleting the
        corresponding job_template.
        '''
        # launch the job_template
        job_pg = job_template_sleep.launch().wait_until_started()

        # delete the job_template
        job_template_sleep.delete()

        # wait for completion and assert success
        job_pg = job_pg.wait_until_completed()
        assert job_pg.status == 'canceled', \
            "Unexpected Job status (%s != 'canceled') after deleting job_template" % (job_pg.status)


@pytest.mark.api
@pytest.mark.skip_selenium
@pytest.mark.destructive
class Test_Job_Template_Survey_Spec(Base_Api_Test):
    '''
    Test survey_creation
    '''

    pytestmark = pytest.mark.usefixtures('authtoken', 'backup_license', 'install_license_unlimited')

    def test_post_with_missing_fields(self, job_template_ping, missing_field_survey_specs):
        '''
        Verify the API does not allow survey creation when missing any or all
        of the spec, name, or description fields.
        '''
        job_template_ping.patch(survey_enabled=True)

        # assert failure on post
        for payload in missing_field_survey_specs:
            with pytest.raises(common.exceptions.BadRequest_Exception):
                job_template_ping.get_related('survey_spec').post(payload)

    def test_post_with_empty_name(self, job_template_ping):
        '''
        Verify the API allows a survey_spec with an empty name and description
        '''
        job_template_ping.patch(survey_enabled=True)
        payload = dict(name='',
                       description='',
                       spec=[dict(required=False,
                                  question_name=common.utils.random_unicode(),
                                  question_description=common.utils.random_unicode(),
                                  variable="submitter_email",
                                  type="text",)])

        # assert successful post
        job_template_ping.get_related('survey_spec').post(payload)

    def test_post_multiple(self, job_template_ping, optional_survey_spec, required_survey_spec):
        '''
        Verify the API allows posting survey_spec multiple times.
        '''
        job_template_ping.patch(survey_enabled=True)
        # post a survey
        survey_spec = job_template_ping.get_related('survey_spec')
        survey_spec.post(optional_survey_spec)
        # update resource
        survey_spec.get()
        assert survey_spec.name == optional_survey_spec['name']

        # post another survey
        job_template_ping.get_related('survey_spec').post(required_survey_spec)
        survey_spec.post(required_survey_spec)
        # update resource
        survey_spec.get()
        assert survey_spec.name == required_survey_spec['name']
