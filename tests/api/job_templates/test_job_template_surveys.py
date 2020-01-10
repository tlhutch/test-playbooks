import logging
import json

import awxkit.exceptions as exc
from awxkit import utils
import fauxfactory
import pytest

from tests.api import APITest


log = logging.getLogger(__name__)


@pytest.mark.usefixtures('authtoken')
class TestJobTemplateSurveys(APITest):

    @pytest.mark.parametrize("launch_time_vars",
                             ["{'non_survey_variable': false, 'submitter_email': 'sample_email@maffenmox.edu'}",
                              "---\nnon_survey_variable: false\nsubmitter_email: sample_email@maffenmox.edu"],
                              ids=['json', 'yaml'])
    def test_launch_with_survey_and_excluded_variables_in_payload(self, job_template,
                                                                  optional_survey_spec_without_defaults,
                                                                  launch_time_vars):
        """Tests that when ask_variables_at_launch is disabled that only survey variables are
        received and make it to our job. Here, "submitter_email" is our only survey variable.
        """
        job_template.add_survey(spec=optional_survey_spec_without_defaults)
        assert not job_template.ask_variables_on_launch

        job = job_template.launch(dict(extra_vars=launch_time_vars)).wait_until_completed()
        job.assert_successful()

        launch_time_vars = utils.load_json_or_yaml(launch_time_vars)
        job_extra_vars = json.loads(job.extra_vars)

        expected_job_vars = dict(submitter_email=launch_time_vars['submitter_email'])
        assert job_extra_vars == expected_job_vars

    def test_jt_survey_password_defaults_passed_to_jobs(self, factories):
        host = factories.host()
        jt = factories.job_template(inventory=host.ds.inventory, playbook='debug_extra_vars.yml')

        survey = [dict(required=False,
                       question_name='Test-1',
                       variable='var1',
                       type='password',
                       default='var1_default'),
                  dict(required=False,
                       question_name='Test-2',
                       variable='var2',
                       type='password',
                       default='var2_default')]
        jt.add_survey(spec=survey)

        job = jt.launch().wait_until_completed()
        job.assert_successful()
        assert '"var1": "var1_default"' in job.result_stdout
        assert '"var2": "var2_default"' in job.result_stdout

        relaunched_job = job.relaunch().wait_until_completed()
        relaunched_job.assert_successful()
        assert '"var1": "var1_default"' in relaunched_job.result_stdout
        assert '"var2": "var2_default"' in relaunched_job.result_stdout

    def test_jt_survey_defaults_and_additional_variables_passed_to_jobs(self, factories):
        host = factories.host()
        jt = factories.job_template(inventory=host.ds.inventory, playbook='debug_extra_vars.yml', ask_variables_on_launch=True)

        survey = [dict(required=False,
                       question_name='Test-1',
                       variable='var1',
                       type='password',
                       default='var1_default'),
                  dict(required=False,
                       question_name='Test-2',
                       variable='var2',
                       type='text',
                       default='var2_default')]
        jt.add_survey(spec=survey)

        job = jt.launch(dict(extra_vars=dict(var3='launch'))).wait_until_completed()
        job.assert_successful()
        assert '"var1": "var1_default"' in job.result_stdout
        assert '"var2": "var2_default"' in job.result_stdout
        assert json.loads(job.extra_vars) == dict(var1='$encrypted$', var2='var2_default', var3='launch')

    def test_jt_survey_with_required_and_optional_fields(self, factories):
        host = factories.host()
        jt = factories.job_template(inventory=host.ds.inventory, playbook='debug_extra_vars.yml')

        survey = [dict(required=True,
                       question_name='Test-1',
                       variable='var1',
                       type='password',
                       default='var1_default'),
                  dict(required=False,
                       question_name='Test-2',
                       variable='var2',
                       type='password',
                       default='var2_default')]
        jt.add_survey(spec=survey)

        job = jt.launch(dict(extra_vars=dict(var1='launch'))).wait_until_completed()
        job.assert_successful()
        assert '"var1": "launch"' in job.result_stdout
        assert '"var2": "var2_default"' in job.result_stdout
        assert json.loads(job.extra_vars) == dict(var1='$encrypted$', var2='$encrypted$')

    def test_null_jt_survey_defaults_passed_to_jobs(self, factories):
        host = factories.host()
        jt = factories.job_template(inventory=host.ds.inventory, playbook='debug_extra_vars.yml')
        survey = [dict(required=False,
                       question_name='Q1',
                       variable='var1',
                       type='password',
                       default=""),
                  dict(required=False,
                       question_name='Q2',
                       variable='var2',
                       type='text',
                       default="")]
        jt.add_survey(spec=survey)

        job = jt.launch().wait_until_completed()
        job.assert_successful()
        assert '"var1": ""' in job.result_stdout
        assert '"var2": ""' in job.result_stdout

    def test_post_spec_with_missing_fields(self, job_template_ping):
        """Verify the API does not allow survey creation when missing any or all
        of the spec, name, or description fields.
        """
        job_template_ping.survey_enabled = True

        missing_field_survey_specs = [dict(),
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

        for spec in missing_field_survey_specs:
            with pytest.raises(exc.BadRequest):
                job_template_ping.related.survey_spec.post(spec)

    def test_post_spec_with_empty_name(self, job_template_ping):
        """Verify the API allows a survey_spec with an empty name and description"""
        job_template_ping.survey_enabled = True
        job_template_ping.related.survey_spec.post(dict(name='',
                                                        description='',
                                                        spec=[dict(required=False,
                                                                   question_name=fauxfactory.gen_utf8(),
                                                                   question_description=fauxfactory.gen_utf8(),
                                                                   variable="submitter_email",
                                                                   type="text")]))

    def test_bad_survey_post_returns_400(self, job_template_ping):
        """Verify the API allows a survey_spec with an empty name and description"""
        job_template_ping.survey_enabled = True
        with pytest.raises(exc.BadRequest) as e:
            job_template_ping.related.survey_spec.post(dict(name='',
                                                        description='',
                                                        spec=[dict(required=False,
                                                                   question_name="broken",
                                                                   question_description="broken",
                                                                   variable="broken",
                                                                   type="broken")]))
        assert "allowed question types" in str(e)
        assert "error" in str(e)

    def test_update_survey_spec(self, job_template_ping, optional_survey_spec, required_survey_spec):
        """Verify the API allows replacing a survey spec with subsequent posts"""
        job_template_ping.add_survey(spec=optional_survey_spec)
        survey_spec = job_template_ping.get_related('survey_spec')
        assert survey_spec.spec == optional_survey_spec

        job_template_ping.add_survey(spec=required_survey_spec)
        survey_spec.get()
        assert survey_spec.spec == required_survey_spec

    def test_updating_survey_password_default_with_reserved_password_keyword_is_idempotent(self, factories):
        host = factories.host()
        jt = factories.job_template(inventory=host.ds.inventory, playbook='debug_extra_vars.yml')
        survey = [dict(required=False,
                       question_name='Q',
                       variable='var1',
                       type='password',
                       default="")]
        jt.add_survey(spec=survey)

        survey[0]['default'] = '$encrypted$'
        updated_survey = jt.add_survey(spec=survey)
        assert updated_survey.spec[0]['default'] == ""

        job = jt.launch().wait_until_completed()
        job.assert_successful()
        assert '"var1": ""' in job.result_stdout

    def test_only_select_jt_survey_fields_editable(self, factories):
        host = factories.host()
        jt = factories.job_template(inventory=host.ds.inventory, playbook='debug_extra_vars.yml')
        survey = [dict(required=True,
                       question_name='Q',
                       variable='var1',
                       type='password',
                       default="don't update me")]
        jt.add_survey(spec=survey)

        question = survey[0]
        for update in [dict(variable='var2', default='$encrypted$'),
                       dict(variable='var1', type='text')]:
            question.update(update)
            with pytest.raises(exc.BadRequest):
                jt.add_survey(spec=survey)

        question.update(dict(type='password', required=False, question_name='Q-new'))
        updated_survey = jt.add_survey(spec=survey)
        assert updated_survey['spec'][0]['required'] is False
        assert updated_survey['spec'][0]['question_name'] == 'Q-new'

        job = jt.launch().wait_until_completed()
        job.assert_successful()
        assert '"var1": "don\'t update me"' in job.result_stdout

    def test_job_template_launch_survey_enabled(self, job_template_ping, required_survey_spec):
        """Assess launch_pg.survey_enabled behaves as expected."""
        # check that survey_enabled is false by default
        launch_pg = job_template_ping.get_related("launch")
        assert not launch_pg.survey_enabled, \
            "launch_pg.survey_enabled is True even though JT survey_enabled is False \
            and no survey given."

        # check that survey_enabled is false when enabled on JT but no survey created
        job_template_ping.survey_enabled = True
        launch_pg = job_template_ping.get_related("launch")
        assert not launch_pg.survey_enabled, \
            "launch_pg.survey_enabled is True with JT survey_enabled as True \
            and no survey given."

        # check that survey_enabled is true when enabled on JT and survey created
        job_template_ping.add_survey(spec=required_survey_spec)
        launch_pg = job_template_ping.get_related("launch")
        assert launch_pg.survey_enabled, \
            "launch_pg.survey_enabled is False even though JT survey_enabled is True \
            and valid survey posted."

    @pytest.mark.yolo
    def test_launch_with_optional_survey_spec(self, job_template_ping, optional_survey_spec):
        """Verify launch_pg attributes with an optional survey spec and job extra_vars."""
        job_template_ping.add_survey(spec=optional_survey_spec)
        survey = job_template_ping.get_related('survey_spec')

        launch = job_template_ping.get_related('launch')
        assert launch.can_start_without_user_input
        assert launch.variables_needed_to_start == []

        job = job_template_ping.launch().wait_until_completed()
        job.assert_successful()

        job_extra_vars = utils.load_json_or_yaml(job.extra_vars)

        expected_extra_vars = dict()
        for question in survey.spec:
            if question.get('required', False) is False and question.get('default') not in (None, ''):
                expected_extra_vars[question['variable']] = question['default']

        assert set(job_extra_vars) == set(expected_extra_vars)

    def test_confirm_survey_spec_password_defaults_censored(self, factories):
        jt = factories.job_template()
        survey = [dict(required=False,
                       question_name='Test',
                       variable='var',
                       type='password',
                       default="don't expose me - {0}".format(fauxfactory.gen_utf8(3).encode('utf8')))]
        jt.add_survey(spec=survey)

        survey_spec = jt.related.survey_spec.get().spec
        assert survey_spec.pop()['default'] == '$encrypted$'

    @pytest.mark.yolo
    def test_confirm_survey_secret_extra_vars_not_in_activity_stream(self, factories):
        host = factories.host()
        jt = factories.job_template(inventory=host.ds.inventory, ask_variables_on_launch=True)
        jt.add_survey()
        job = jt.launch().wait_until_completed()
        job.assert_successful()

        assert json.loads(job.extra_vars) == dict(secret="$encrypted$")

        job_activity_stream = job.related.activity_stream.get().results.pop()
        assert json.loads(job_activity_stream.changes.extra_vars) == dict(secret="$encrypted$")

        job = jt.launch(dict(extra_vars=dict(secret='123', one=234, two=dict(three=345, four=dict(five=456))))).wait_until_completed()
        job.assert_successful()
        job_activity_stream = job.related.activity_stream.get().results.pop()
        assert json.loads(job_activity_stream.changes.extra_vars)['secret'] == "$encrypted$"

    @pytest.mark.parametrize('template', ['job', 'workflow_job'])
    def test_confirm_no_plaintext_survey_passwords_in_db(self, skip_if_cluster, v2, factories, get_pg_dump, template):
        resource = getattr(factories, template + '_template')()
        password = "don't expose me - {0}".format(fauxfactory.gen_utf8(3).encode('utf8'))
        survey = [dict(required=False,
                       question_name='Test',
                       variable='var',
                       type='password',
                       default=password)]
        resource.add_survey(spec=survey)

        pg_dump = get_pg_dump()

        try:
            undesired_location = pg_dump.index(password)
        except ValueError:
            return
        else:
            target_text = pg_dump[undesired_location - 200:undesired_location + 200]
            pytest.fail('Found plaintext survey password secret in db:\n\n{}'.format(target_text))

    def test_wrong_survey_variable_type_server_error(self, factories):
        """Test whether wrong survey variable type produces server error.

        This test targets the following issue:

        https://github.com/ansible/tower-qa/issues/942
        """
        host = factories.host()
        jt = factories.job_template(inventory=host.ds.inventory)

        survey = [dict(
            required=True,
            question_name='Q1',
            variable='var1',
            type='text',
            default='survey')]

        jt.add_survey(spec=survey)

        with pytest.raises(exc.BadRequest) as e:
            jt.launch(dict(extra_vars={'var1': 5})).wait_until_completed()

        assert 'expected to be a string' in str(e)

        survey = [
            dict(required=True, question_name='Q2', variable='var2', type='float')
        ]

        jt.add_survey(spec=survey)

        with pytest.raises(exc.BadRequest) as e:
            jt.launch(dict(extra_vars={'var2': 'abc'})).wait_until_completed()

        assert 'expected to be a numeric type' in str(e)

        survey = [
            dict(required=True, question_name='Q3', variable='var3', type='integer')
        ]

        jt.add_survey(spec=survey)

        with pytest.raises(exc.BadRequest) as e:
            jt.launch(dict(extra_vars={'var3': 'abc'})).wait_until_completed()

        assert 'expected to be an integer' in str(e)
