import logging
import json
import yaml

from awxkit import utils
import awxkit.awx.inventory
import awxkit.exceptions
import pytest

from tests.api import APITest


log = logging.getLogger(__name__)


@pytest.mark.usefixtures('authtoken')
class TestJobTemplateExtraVars(APITest):

    def get_required_survey_vars(self, survey_spec):
        required_vars = []
        for item in survey_spec.spec:
            if item.get('required'):
                required_vars.append(item.variable)
        return required_vars

    def get_default_survey_vars(self, survey_spec):
        default_vars = []
        for item in survey_spec.spec:
            if item.get('default'):
                default_vars.append(item.variable)
        return default_vars

    def update_launch_time_vars(self, launch_time_vars, update):
        """Updates a set of launch_time variables (either YAML or JSON) with a dictionary of
        key-value pairs. Returns YAML or JSON.
        """
        try:
            launch_time_vars = json.loads(launch_time_vars)
            launch_time_vars.update(update)
            return json.dumps(launch_time_vars)
        except:
            launch_time_vars = yaml.load(launch_time_vars, Loader=yaml.SafeLoader)
            launch_time_vars.update(update)
            return yaml.dump(launch_time_vars)

    def test_confirm_invalid_extra_vars_rejected(self, factories):
        jt = factories.job_template()
        for invalid, message in (
                ('"{"', 'Input type `str` is not a dictionary'),
                (('a', 'b'), 'Cannot parse as JSON'),
                (('one=1', 'two=2'), 'Cannot parse as JSON'),
                (0, 'Input type `int` is not a dictionary'),
                (0.1, 'Input type `float` is not a dictionary'),
                (True, 'Input type `bool` is not a dictionary'),
                ([1, 2, 3], 'Input type `list` is not a dictionary'),
                (['a', 'b', 'c'], 'Input type `list` is not a dictionary'),
                ('["a", "b", "c"]', 'Input type `list` is not a dictionary')):
            with pytest.raises(awxkit.exceptions.BadRequest) as e:
                print(invalid)
                jt.extra_vars = str(invalid)
            assert 'extra_vars' in e.value.msg
            assert message in e.value.msg['extra_vars'][0]

    def test_confirm_recursive_extra_vars_rejected(self, factories):
        jt = factories.job_template()
        with pytest.raises(awxkit.exceptions.BadRequest) as e:
            jt.extra_vars = "&id001\nfoo: *id001\n"
            assert 'Variables not compatible with JSON standard (error: Circular reference detected)' in e.msg

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

        # launch JT and assert successful
        job = job_template_with_extra_vars.launch().wait_until_completed()
        job.assert_successful()

        # assert extra_vars match JT extra_vars
        job_template_vars = utils.load_json_or_yaml(job_template_with_extra_vars.extra_vars)
        job_vars = json.loads(job.extra_vars)
        assert job_vars == job_template_vars

    @pytest.mark.ansible_integration
    def test_launch_with_extra_vars_at_launch(self, job_template_with_extra_vars, launch_time_extra_vars):
        """Verify that when launch-time extra_vars are provided, job extra_vars consist
        of a union of the launch-time and JT extra_vars. Launch-time variables should
        take precedence over JT variables with our colliding variable.
        """
        job_template_with_extra_vars.ask_variables_on_launch = True
        launch = job_template_with_extra_vars.related.launch.get()

        # assert values on launch resource
        assert not launch.can_start_without_user_input
        assert launch.ask_variables_on_launch
        assert not launch.passwords_needed_to_start
        assert not launch.variables_needed_to_start
        assert not launch.credential_needed_to_start

        # launch JT and assert successful
        job = job_template_with_extra_vars.launch(dict(extra_vars=launch_time_extra_vars)).wait_until_completed()
        job.assert_successful()

        jt_vars = utils.load_json_or_yaml(job_template_with_extra_vars.extra_vars)
        launch_time_vars = utils.load_json_or_yaml(launch_time_extra_vars)
        job_vars = json.loads(job.extra_vars)

        # assert expected job extra_vars
        assert set(jt_vars) < set(job_vars)
        assert set(launch_time_vars) < set(job_vars)
        assert set(job_vars) == set(jt_vars) | set(job_vars)

        assert job_vars['jt_var'] == jt_vars['jt_var']
        assert job_vars['job_var'] == launch_time_vars['job_var']
        assert job_vars['intersection'] == launch_time_vars['intersection'], \
            "Our launch-time variable did not replace our colliding JT variable value."

    def test_launch_with_excluded_variables_in_payload(self, job_template, launch_time_extra_vars):
        """Tests that when ask_variables_at_launch is disabled that launch-time variables get
        ignored.
        """
        assert not job_template.ask_variables_on_launch

        # launch JT with launch-time variables
        job = job_template.launch(dict(extra_vars=launch_time_extra_vars)).wait_until_completed()
        job.assert_successful()

        # assert launch-time variables excluded
        job_extra_vars = json.loads(job.extra_vars)
        assert job_extra_vars == {}, \
            "Unexpected value for job extra variables - {0}.".format(job.extra_vars)

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

        # launch JT and assert successful
        job = job_template_ask_variables_on_launch.launch().wait_until_completed()
        job.assert_successful()

        job_vars = json.loads(job.extra_vars)
        assert job_vars == {}, \
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

        # launch JT and assert successful
        payload = dict(extra_vars=launch_time_extra_vars)
        job = job_template_ask_variables_on_launch.launch(payload).wait_until_completed()

        launch_time_vars = utils.load_json_or_yaml(launch_time_extra_vars)
        job_vars = json.loads(job.extra_vars)
        assert launch_time_vars == job_vars

    def test_launch_without_variables_needed_to_start(self, job_template_variables_needed_to_start):
        """Verify the job->launch endpoint behaves as expected when launching a
        survey without required variables.
        """
        launch_pg = job_template_variables_needed_to_start.get_related('launch')
        survey_spec = job_template_variables_needed_to_start.get_related('survey_spec')

        print(json.dumps(launch_pg.json, indent=2))

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
        exc_info = pytest.raises(awxkit.exceptions.BadRequest, launch_pg.post)
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

    @pytest.mark.parametrize("launch_time_vars", [
        "{'likes_chicken': ['yes'], 'favorite_color': 'green'}",
        "---\nlikes_chicken:\n  - 'yes'\nfavorite_color: green"
    ], ids=['json', 'yaml'])
    def test_launch_with_variables_needed_to_start(self, job_template_variables_needed_to_start, launch_time_vars):
        """Verifies that job variables are a union of the variables supplied at launch time
        and variables sourced from survey defaults when:
        * Survey has required questions and non-required questions with default answers.
        * JT is launched supplying values for the required variables at launch time only.
        """
        launch = job_template_variables_needed_to_start.related.launch.get()
        survey_spec = job_template_variables_needed_to_start.related.survey_spec.get()

        # assert values on launch resource
        assert not launch.can_start_without_user_input
        assert not launch.ask_variables_on_launch
        assert not launch.passwords_needed_to_start
        assert launch.variables_needed_to_start
        assert not launch.credential_needed_to_start

        # assert expected launch page required variables
        required_survey_vars = self.get_required_survey_vars(survey_spec)
        assert set(required_survey_vars) == set(launch.variables_needed_to_start), \
            "Unexpected number of JT launch page variables listed as needed to start."

        # launch JT and assert successful
        payload = dict(extra_vars=launch_time_vars)
        job = job_template_variables_needed_to_start.launch(payload).wait_until_completed()
        job.assert_successful()

        default_survey_vars = self.get_default_survey_vars(survey_spec)
        survey_vars = [var for var in default_survey_vars if var not in required_survey_vars]
        launch_time_vars = utils.load_json_or_yaml(launch_time_vars)
        job_vars = json.loads(job.extra_vars)

        # assert expected job extra_vars
        assert set(survey_vars) < set(job_vars)
        assert set(launch_time_vars) < set(job_vars)
        assert set(job_vars) == set(survey_vars) | set(launch_time_vars)

        assert job_vars['survey_var'] == survey_spec.get_variable_default('survey_var')
        assert job_vars['likes_chicken'] == launch_time_vars['likes_chicken']
        assert job_vars['favorite_color'] == launch_time_vars['favorite_color']
        assert job_vars['intersection'] == survey_spec.get_variable_default('intersection')

    @pytest.mark.yolo
    def test_launch_with_variables_needed_to_start_and_extra_vars_at_launch(self, job_template_with_extra_vars, required_survey_spec,
                                                                            launch_time_extra_vars):
        """Verify that when launch-time extra_vars are provided, that job
        extra_variables are a union of the JT variables, survey variables
        (variables supplied by survey question default answers), and
        launch-time variables.
        """
        job_template_with_extra_vars.ask_variables_on_launch = True
        job_template_with_extra_vars.add_survey(spec=required_survey_spec)

        launch = job_template_with_extra_vars.related.launch.get()
        survey_spec = job_template_with_extra_vars.related.survey_spec.get()

        # assert values on launch resource
        assert not launch.can_start_without_user_input
        assert launch.ask_variables_on_launch
        assert not launch.passwords_needed_to_start
        assert launch.variables_needed_to_start
        assert not launch.credential_needed_to_start

        # assert expected launch page required variables
        required_survey_vars = self.get_required_survey_vars(survey_spec)
        assert set(required_survey_vars) == set(launch.variables_needed_to_start), \
            "Unexpected number of JT launch page variables listed as needed to start."

        # launch JT and assert successful
        launch_time_vars = self.update_launch_time_vars(launch_time_extra_vars, dict(likes_chicken=["yes"], favorite_color="green"))
        job = job_template_with_extra_vars.launch(dict(extra_vars=launch_time_vars)).wait_until_completed()
        job.assert_successful()

        jt_vars = utils.load_json_or_yaml(job_template_with_extra_vars.extra_vars)
        launch_time_vars = utils.load_json_or_yaml(launch_time_vars)
        default_survey_vars = self.get_default_survey_vars(survey_spec)
        survey_vars = [var for var in default_survey_vars if var not in required_survey_vars]
        job_vars = json.loads(job.extra_vars)

        # assert expected job extra_vars
        assert set(jt_vars) < set(job_vars)
        assert set(survey_vars) < set(job_vars)
        assert set(launch_time_vars) < set(job_vars)
        assert set(job_vars) == set(jt_vars) | set(survey_vars) | set(launch_time_vars)

        assert job_vars['jt_var'] == jt_vars['jt_var']
        assert job_vars['survey_var'] == survey_spec.get_variable_default('survey_var')
        assert job_vars['likes_chicken'] == launch_time_vars['likes_chicken']
        assert job_vars['favorite_color'] == launch_time_vars['favorite_color']
        assert job_vars['job_var'] == launch_time_vars['job_var']
        assert job_vars['intersection'] == launch_time_vars['intersection'], \
            "A launch-time variable did not replace our JT and survey intersection variable."

    @pytest.mark.parametrize('required', [True, False])
    def test_survey_vars_passed_with_jt_when_launch_vars_absent_and_survey_defaults_present(self, factories, required):
        """Verifies behavior for default survey responses.
            Required (True): Job should fail to start
            Not Required (False): Job should start and the defaults should be used
        """
        host = factories.host()
        jt = factories.job_template(
            inventory=host.ds.inventory, playbook='debug_extra_vars.yml')

        survey = [dict(required=required,
                       question_name='Q1',
                       variable='var1',
                       type='text',
                       default='survey'),
                  dict(required=required,
                       question_name='Q2',
                       variable='var2',
                       type='password',
                       default='survey')]
        jt.add_survey(spec=survey)

        if not required:
            j = jt.launch(dict(extra_vars=dict())).wait_until_completed()
            job = jt.get().related.last_job.get()
            j.assert_successful()
            job.assert_successful()
            assert '"var1": "survey"' in job.result_stdout
            assert '"var2": "survey"' in job.result_stdout

            assert json.loads(j.extra_vars) == dict(
                var1='survey', var2='$encrypted$')
            assert json.loads(job.extra_vars) == dict(
                var1='survey', var2='$encrypted$')
        if required:
            with pytest.raises(awxkit.exceptions.BadRequest) as e:
                j = jt.launch(dict(extra_vars=dict())).wait_until_completed()
            assert "variables_needed_to_start" in e.value.msg

    def test_included_extra_vars_with_vault_content(self, factories):
        cred = factories.credential(kind='vault', vault_password='password')
        jt = factories.job_template(playbook='custom_json.yml')
        jt.add_credential(cred)
        job = jt.launch().wait_until_completed(interval=1, timeout=30)
        job.assert_successful()

        expected_data = dict(
            vaulted_text = "people run into some space aliens and they end up fighting them",
            unsafe_text = "{{ unsafe }}"
        )

        # assure correct reporting of include task
        include_events = job.get_related(
            'job_events',
            event='runner_on_ok',
            task='include extra vars with vault/unsafe tags'
        )
        assert include_events.count == 1
        include_event = include_events.results.pop()
        include_data = include_event.event_data
        assert 'res' in include_event.event_data, include_event.event_data
        res = include_event.event_data['res']
        assert 'ansible_facts' in res, res
        assert set(res['ansible_facts'].keys()) == set(expected_data.keys())

        # assure correct reporting of debug tasks
        stdout = job.result_stdout
        for text in expected_data.values():
            assert text in stdout
