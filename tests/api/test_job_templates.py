import json
import pytest
import fauxfactory
import common.tower.inventory
from tests.api import Base_Api_Test


@pytest.fixture(scope="function")
def missing_field_survey_specs(request):
    '''
    Returns a list of survey_spec's which should fail to post.
    '''
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
    '''Creates and deletes an object.'''
    related_pg = job_template.get_related(request.param)
    related_pg.delete()
    return (request.param, job_template)


@pytest.mark.api
@pytest.mark.skip_selenium
@pytest.mark.destructive
class Test_Job_Template(Base_Api_Test):

    pytestmark = pytest.mark.usefixtures('authtoken', 'install_license_unlimited')

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

    def test_launch_with_extra_vars_from_job_template(self, job_template_with_extra_vars):
        '''
        Verify that when no launch-time extra_vars are provided, variables from
        the job_template are used.
        '''
        launch_pg = job_template_with_extra_vars.get_related('launch')

        # assert values on launch resource
        assert launch_pg.can_start_without_user_input
        assert not launch_pg.ask_variables_on_launch
        assert not launch_pg.passwords_needed_to_start
        assert not launch_pg.variables_needed_to_start
        assert not launch_pg.credential_needed_to_start

        # assert job successful
        job_pg = job_template_with_extra_vars.launch().wait_until_completed()
        assert job_pg.is_successful, "job unsuccessful - %s" % job_pg

        # coerce extra_vars into a dictionary for a proper comparison
        try:
            job_extra_vars = json.loads(job_pg.extra_vars)
        except ValueError:
            job_extra_vars = {}
        try:
            job_template_extra_vars = json.loads(job_template_with_extra_vars.extra_vars)
        except ValueError:
            job_template_extra_vars = {}

        # assert extra_vars match job_template extra_vars
        assert job_extra_vars == job_template_extra_vars

    def test_launch_with_extra_vars_at_launch(self, job_template_with_extra_vars, job_extra_vars_dict, tower_version_cmp):
        '''
        Verify that when launch-time extra_vars are provided, the job
        extra_variables are a union of the launch-time variables and the
        job_template variables.
        '''
        launch_pg = job_template_with_extra_vars.get_related('launch')

        # assert values on launch resource
        assert launch_pg.can_start_without_user_input
        assert not launch_pg.ask_variables_on_launch
        assert not launch_pg.passwords_needed_to_start
        assert not launch_pg.variables_needed_to_start
        assert not launch_pg.credential_needed_to_start

        # launch job_template and assert successful completion
        job_pg = job_template_with_extra_vars.launch(dict(extra_vars=job_extra_vars_dict)).wait_until_completed()
        assert job_pg.is_successful, "job unsuccessful - %s" % job_pg

        # format job extra_vars
        try:
            job_extra_vars = json.loads(job_pg.extra_vars)
        except ValueError:
            job_extra_vars = {}

        # variable precedence changed in 2.4.0
        if tower_version_cmp('2.4.0') < 0:
            # assert job.extra_vars match the launch-time extra_vars
            assert job_extra_vars == job_extra_vars_dict

        else:
            # coerce extra_vars into a dictionary for a proper comparison
            try:
                job_template_extra_vars = json.loads(job_template_with_extra_vars.extra_vars)
            except ValueError:
                job_template_extra_vars = {}

            # assert the job_template extra_vars are a subset of the job extra_vars
            assert set(job_template_extra_vars) < set(job_extra_vars)

            # assert the launch-time extra_vars are a subset of the job extra_vars
            assert set(job_extra_vars_dict) < set(job_extra_vars)

            # assert the job extra_vars are a union of the job_template and launch-time extra_vars
            assert set(job_extra_vars) == set(job_template_extra_vars) | set(job_extra_vars_dict)

            # assert that run-time extra_vars take precedence over job template extra_vars
            assert job_extra_vars['intersection'] == u'job', \
                "A launch-time extra_var did not replace a job_template extra_var as expected."

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

    def test_launch_without_credential_permission(self, job_template, org_user, user_password, current_user):
        launch_pg = job_template.get_related('launch')

        # assert values on launch resource
        assert launch_pg.can_start_without_user_input
        assert not launch_pg.ask_variables_on_launch
        assert not launch_pg.passwords_needed_to_start
        assert not launch_pg.variables_needed_to_start
        assert not launch_pg.credential_needed_to_start

        # add inventory read permission
        org_user.add_permission('read', inventory=job_template.inventory)

        # add job_template run permission
        org_user.add_permission('run', project=job_template.project, inventory=job_template.inventory)

        # launch the job_template providing the credential in the payload
        with current_user(username=org_user.username, password=user_password):
            exc_info = pytest.raises(common.exceptions.Forbidden_Exception, launch_pg.post)
            result = exc_info.value[1]

        assert 'detail' in result and result['detail'] == \
            'You do not have permission to perform this action.', \
            "Unexpected 403 response detail - %s" % json.dumps(result, indent=2)

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

    def test_launch_with_team_credential(self, job_template_no_credential, team_with_org_admin, team_ssh_credential, user_password):
        '''Verifies that a team user can use a team credential to launch a job template.'''
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

    def test_launch_with_ask_credential_and_without_passwords_in_payload(self, job_template_no_credential,
                                                                         ssh_credential_multi_ask):
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
        assert ssh_credential_multi_ask.expected_passwords_needed_to_start == result['passwords_needed_to_start']

    def test_launch_with_ask_credential_and_with_passwords_in_payload(self, job_template_no_credential,
                                                                      ssh_credential_multi_ask):
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
                       ssh_key_unlock=self.credentials['ssh']['encrypted']['ssh_key_unlock'],
                       vault_password=self.credentials['ssh']['vault_password'],
                       become_password=self.credentials['ssh']['become_password'])

        # launch the job_template and wait for completion
        job_pg = job_template_no_credential.launch(payload).wait_until_completed()

        # assert success
        assert job_pg.is_successful, "Job unsuccessful - %s" % job_pg

    def test_launch_without_ask_variables_on_launch(self, job_template_ask_variables_on_launch, tower_version_cmp):
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

        # extra_vars handling changed in 2.4
        if tower_version_cmp('2.4.0') < 0:
            expected_result = ''
        else:
            expected_result = '{}'

        # assert job has no extra_vars
        assert job_pg.extra_vars == expected_result, \
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
        credential = job_template_passwords_needed_to_start.get_related('credential')
        assert credential.expected_passwords_needed_to_start == launch_pg.passwords_needed_to_start

        # launch the job_template without passwords
        with pytest.raises(common.exceptions.BadRequest_Exception):
            launch_pg.post()

        # prepare payload with empty passwords
        payload = dict(ssh_password='', ssh_key_unlock='', become_password='')

        # launch the job_template
        with pytest.raises(common.exceptions.BadRequest_Exception):
            launch_pg.post(payload)

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

    def test_launch_template_with_deleted_related(self, job_template_with_deleted_related):
        '''
        Verify that the job->launch endpoint does not allow launching a
        job_template whose related endpoints have been deleted.
        '''
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
        with pytest.raises(common.exceptions.BadRequest_Exception):
            launch_pg.post()


@pytest.mark.api
@pytest.mark.skip_selenium
@pytest.mark.destructive
class Test_Job_Template_Survey_Spec(Base_Api_Test):
    '''
    Test survey_creation
    '''

    pytestmark = pytest.mark.usefixtures('authtoken', 'install_license_unlimited')

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
                                  question_name=fauxfactory.gen_utf8(),
                                  question_description=fauxfactory.gen_utf8(),
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

    def test_launch_survey_enabled(self, job_template_ping, required_survey_spec):
        '''
        Tests that launch_pg.survey_enabled operates as expected.
        '''
        # check that launch_pg.survey_enabled is False by default
        launch_pg = job_template_ping.get_related("launch")
        assert not launch_pg.survey_enabled, \
            "launch_pg.survey_enabled is True even though JT survey_enabled is False \
            and no survey given."

        # check that launch_pg.survey_enabled is False when enabled on JT but no survey given
        job_template_ping.patch(survey_enabled=True)
        launch_pg = job_template_ping.get_related("launch")
        assert not launch_pg.survey_enabled, \
            "launch_pg.survey_enabled is True with JT survey_enabled as True \
            and no survey given."

        # check that launch_pg survey_enabled is True when enabled on JT and survey given
        survey_spec = job_template_ping.get_related('survey_spec')
        survey_spec.post(required_survey_spec)
        launch_pg = job_template_ping.get_related("launch")
        assert launch_pg.survey_enabled, \
            "launch_pg.survey_enabled is False even though JT survey_enabled is True \
            and valid survey posted."


@pytest.mark.api
@pytest.mark.skip_selenium
@pytest.mark.destructive
class Test_Job_Template_Permissions(Base_Api_Test):
    '''
    Tests job template permissions.
    '''

    pytestmark = pytest.mark.usefixtures('authtoken', 'install_license_1000')

    def test_unprivileged_user_with_no_permissions(self, api_job_templates_pg, job_template, org_user, user_password):
        '''
        Tests that an unprivileged user with no permissions:
        - Cannot issue PUT and PATCH requests to an existing job template.
        - Cannot launch existing job templates.
        - Cannot create new job templates.
        Inventory-read permission is present.
        '''
        # create payload
        payload = job_template.json
        payload.update(dict(name="Additional test job template - %s" % fauxfactory.gen_utf8()))

        org_user.add_permission("read", inventory=job_template.inventory)
        credential = job_template.get_related("credential")
        credential.patch(user=org_user.id)

        # test http methods
        with self.current_user(org_user.username, user_password):
            with pytest.raises(common.exceptions.Forbidden_Exception):
                job_template.get()
            with pytest.raises(common.exceptions.Forbidden_Exception):
                job_template.patch()
            with pytest.raises(common.exceptions.Forbidden_Exception):
                job_template.put()
            with pytest.raises(common.exceptions.Forbidden_Exception):
                job_template.launch()

            # test creating new job template
            with pytest.raises(common.exceptions.Forbidden_Exception):
                api_job_templates_pg.post(payload)

    def test_unprivileged_user_with_create_permission(self, api_job_templates_pg, job_template, org_user, user_password):
        '''
        Tests that an unprivileged user with create permissions:
        - Can issue PATCH and PUT requests to an existing job template.
        - Can launch existing job templates.
        - Can create new job templates.
        Inventory-read permission is present.
        '''
        # create payload
        payload = job_template.json
        payload.update(dict(name="Additional test job template - %s" % fauxfactory.gen_utf8()))

        org_user.add_permission("read", inventory=job_template.inventory)
        org_user.add_permission("create", inventory=job_template.inventory, project=job_template.project)
        credential = job_template.get_related("credential")
        credential.patch(user=org_user.id)

        # test http methods
        with self.current_user(org_user.username, user_password):
            job_template.get()
            job_template.patch()
            job_template.put()

            job_pg = job_template.launch().wait_until_completed()
            assert job_pg.is_successful, "Job template launched by org_user with create permission unexpectedly unsuccessful - %s" % job_pg

            # test creating new job template
            job_template_pg = api_job_templates_pg.post(payload)
            job_template_pg.delete()

    def test_unprivileged_user_with_run_permissions(self, api_job_templates_pg, job_template, org_user, user_password):
        '''
        Tests that an unprivileged user with no permissions:
        - Can not issue PUT and PATCH requests to an existing job template.
        - Can launch existing job templates.
        - Cannot create new job templates.
        Inventory-read permission is present.
        '''
        # create payload
        payload = job_template.json
        payload.update(dict(name="Additional test job template - %s" % fauxfactory.gen_utf8()))

        org_user.add_permission("read", inventory=job_template.inventory)
        org_user.add_permission("run", inventory=job_template.inventory, project=job_template.project)
        credential = job_template.get_related("credential")
        credential.patch(user=org_user.id)

        # test http methods
        with self.current_user(org_user.username, user_password):
            job_template.get()
            with pytest.raises(common.exceptions.Forbidden_Exception):
                job_template.patch()
            with pytest.raises(common.exceptions.Forbidden_Exception):
                job_template.put()

            job_pg = job_template.launch().wait_until_completed()
            assert job_pg.is_successful, "Job template launched by org user with run permission unexpectedly unsuccessful - %s" % job_pg

            # test creating new job template
            with pytest.raises(common.exceptions.Forbidden_Exception):
                api_job_templates_pg.post(payload)

    def test_unprivileged_user_with_check_permissions(self, api_job_templates_pg, another_job_template, check_job_template,
                                                      org_user, user_password):
        '''
        Tests that an unprivileged user with no permissions:
        - Can not issue PUT and PATCH requests to an existing job template.
        - Can launch check job templates.
        - Cannot launch regular job templates.
        - Cannot create new job templates.
        Inventory-read permission is present.
        '''
        # create payload
        payload = another_job_template.json
        payload.update(dict(name="Additional test job template - %s" % fauxfactory.gen_utf8()))

        org_user.add_permission("read", inventory=check_job_template.inventory)
        org_user.add_permission("check", inventory=check_job_template.inventory, project=check_job_template.project)
        credential = check_job_template.get_related("credential")
        credential.patch(user=org_user.id)

        # test http methods
        with self.current_user(org_user.username, user_password):
            check_job_template.get()
            with pytest.raises(common.exceptions.Forbidden_Exception):
                check_job_template.patch()
            with pytest.raises(common.exceptions.Forbidden_Exception):
                check_job_template.put()
            job_pg = check_job_template.launch().wait_until_completed()
            assert job_pg.is_successful, "Check job template launched by org user with check permission unexpectedly unsuccessful - %s" % job_pg

            # test creating new job template
            with pytest.raises(common.exceptions.Forbidden_Exception):
                api_job_templates_pg.post(payload)

            # attempt to launch a run-type job template
            credential = another_job_template.get_related("credential")
            credential.patch(user=org_user.id)
            with pytest.raises(common.exceptions.Forbidden_Exception):
                another_job_template.launch()

    def test_privileged_user_with_no_permissions(self, api_job_templates_pg, job_template, privileged_users, user_password):
        '''
        Tests that privileged users without permissions can:
        - Edit existing job templates
        - Create new job templates
        - Launch existing job templates
        '''
        payload = job_template.json

        for privileged_user in privileged_users:
            # create payload
            payload.update(dict(name="Additional test job template - %s" % fauxfactory.gen_utf8()))

            credential = job_template.get_related("credential")
            credential.patch(user=privileged_user.id)

            # test http methods
            with self.current_user(privileged_user.username, user_password):
                job_template.get()
                job_template.patch()
                job_template.put()

                job_pg = job_template.launch().wait_until_completed()
                assert job_pg.is_successful, "Job template launched by privileged user unexpectedly unsuccessful - %s" % job_pg

                # test creating new job template
                job_template_pg = api_job_templates_pg.post(payload)
                job_template_pg.delete()
