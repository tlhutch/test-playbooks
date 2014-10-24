import json
import pytest
import common.tower.inventory
import common.utils
from tests.api import Base_Api_Test


@pytest.fixture(scope="function")
def job_template_no_credential(request, job_template_ping):
    return job_template_ping.patch(credential=None)


@pytest.fixture(scope="function")
def job_template_ask_variables_on_launch(request, job_template_ping):
    return job_template_ping.patch(ask_variables_on_launch=True)


@pytest.fixture(scope="function")
def optional_survey_spec(request):
    payload = dict(name=common.utils.random_unicode(),
                   description=common.utils.random_unicode(),
                   spec=[dict(required=False,
                              question_name="Enter your email &mdash; &euro;",
                              variable="submitter_email",
                              type="text",),
                         dict(required=False,
                              question_name="Enter your employee number email &mdash; &euro;",
                              variable="submitter_email",
                              type="integer",)])
    return payload


@pytest.fixture(scope="function")
def required_survey_spec(request):
    payload = dict(name=common.utils.random_unicode(),
                   description=common.utils.random_unicode(),
                   spec=[dict(required=True,
                              question_name="Do you like chicken?",
                              question_description="Please indicate your chicken preference:",
                              variable="likes_chicken",
                              type="multiselect",
                              choices="yes"),
                         dict(required=True,
                              question_name="Favorite color?",
                              question_description="Pick a color darnit!",
                              variable="favorite_color",
                              type="multiplechoice",
                              choices="red\ngreen\nblue",
                              default="green"),
                         dict(required=False,
                              question_name="Enter your email &mdash; &euro;",
                              variable="submitter_email",
                              type="text")])
    return payload


@pytest.fixture(scope="function")
def job_template_variables_needed_to_start(request, job_template_ping, required_survey_spec):
    obj = job_template_ping.patch(survey_enabled=True)
    obj.get_related('survey_spec').post(required_survey_spec)
    return obj


@pytest.fixture(scope="function")
def job_template_passwords_needed_to_start(request, job_template_ping, ssh_credential_multi_ask):
    return job_template_ping.patch(credential=ssh_credential_multi_ask.id)


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

        # launch the job_template
        result = launch_pg.post()

        # assert successful launch
        jobs_pg = job_template_ping.get_related('jobs', id=result.json['job'])
        assert jobs_pg.count == 1, "Unexpected number of jobs returned (%s != 1)" % jobs_pg.count

        # wait for completion and assert success
        job_pg = jobs_pg.results[0].wait_until_completed()
        assert job_pg.is_successful, job_pg

    def test_launch_no_credential(self, job_template_no_credential):
        '''
        Verify the job->launch endpoint behaves as expected
        '''
        launch_pg = job_template_no_credential.get_related('launch')

        # assert values on launch resource
        assert not launch_pg.can_start_without_user_input
        assert not launch_pg.ask_variables_on_launch
        assert not launch_pg.passwords_needed_to_start
        assert not launch_pg.variables_needed_to_start

    def test_launch_ask_variables_on_launch(self, job_template_ask_variables_on_launch):
        '''
        Verify the job->launch endpoint behaves as expected when ask_variables_on_launch is enabled
        '''
        launch_pg = job_template_ask_variables_on_launch.get_related('launch')

        # assert values on launch resource
        assert launch_pg.can_start_without_user_input
        assert launch_pg.ask_variables_on_launch
        assert not launch_pg.passwords_needed_to_start
        assert not launch_pg.variables_needed_to_start

    def test_launch_variables_needed_to_start(self, job_template_variables_needed_to_start):
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

        # assert 'ssh_password' in launch_pg.passwords_needed_to_start
        # assert 'ssh_key_unlock' in launch_pg.passwords_needed_to_start
        # assert 'sudo_password' in launch_pg.passwords_needed_to_start
        assert ['ssh_password', 'sudo_password', 'ssh_key_unlock'] == launch_pg.passwords_needed_to_start

        # launch the job_template without passwords
        with pytest.raises(common.exceptions.BadRequest_Exception):
            launch_pg.post()

        # launch the job_template with empty passwords
        passwords = dict(ssh_password="",
                         sudo_password="",
                         ssh_key_unlock="")
        with pytest.raises(common.exceptions.BadRequest_Exception):
            launch_pg.post(passwords)

    def test_launch_passwords_needed_to_start(self, job_template_passwords_needed_to_start):
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

        # assert 'ssh_password' in launch_pg.passwords_needed_to_start
        # assert 'ssh_key_unlock' in launch_pg.passwords_needed_to_start
        # assert 'sudo_password' in launch_pg.passwords_needed_to_start
        assert ['ssh_password', 'sudo_password', 'ssh_key_unlock'] == launch_pg.passwords_needed_to_start

        # launch the job_template with passwords
        passwords = dict(ssh_password=self.credentials['ssh']['password'],
                         sudo_password=self.credentials['ssh']['sudo_password'],
                         ssh_key_unlock=self.credentials['ssh']['encrypted']['ssh_key_unlock'])
        result = launch_pg.post(passwords)

        # assert successful launch
        jobs_pg = job_template_passwords_needed_to_start.get_related('jobs', id=result.json['job'])
        assert jobs_pg.count == 1, "Unexpected number of jobs returned (%s != 1)" % jobs_pg.count

        # wait for completion and assert success
        job_pg = jobs_pg.results[0].wait_until_completed()
        assert job_pg.is_successful, job_pg

    def test_delete_with_running_job(self, job_template_sleep, api_jobs_pg):
        '''
        Verify that tower properly cancels active jobs when deleting the
        corresponding job_template.
        '''
        launch_pg = job_template_sleep.get_related('launch')

        # launch the job_template
        result = launch_pg.post()

        # delete the job_template
        job_template_sleep.delete()

        # locate the launched job
        jobs_pg = api_jobs_pg.get(id=result.json['job'])
        assert jobs_pg.count == 1, "Unexpected number of jobs returned (%s != 1)" % jobs_pg.count

        # wait for completion and assert success
        job_pg = jobs_pg.results[0].wait_until_completed()
        assert job_pg.status == 'canceled', \
            "Unexpected Job status (%s != 'canceled') after deleting job_template" % (job_pg.status)
