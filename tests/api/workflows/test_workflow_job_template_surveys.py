import copy
import json

import awxkit.exceptions as exc
import pytest

from tests.api import APITest


@pytest.mark.usefixtures('authtoken')
class TestWorkflowJobTemplateSurveys(APITest):

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

    @pytest.fixture
    def debug_extra_vars_job_template(self, instance_group, factories):
        host = factories.host()
        jt = factories.job_template(inventory=host.ds.inventory, playbook='debug_extra_vars.yml')
        jt.add_instance_group(instance_group)
        return jt

    @pytest.mark.parametrize('template', ['wfjt', 'jt'])
    def test_single_template_survey_password_defaults_passed_to_jobs(self, debug_extra_vars_job_template, factories, template):
        wfjt = factories.workflow_job_template()
        jt = debug_extra_vars_job_template
        factories.workflow_job_template_node(workflow_job_template=wfjt, unified_job_template=jt)

        if template == 'wfjt':
            wfjt.add_survey(spec=self.survey)
        else:
            jt.add_survey(spec=self.survey)

        wfj = wfjt.launch().wait_until_completed(timeout=120)
        job = jt.get().related.last_job.get()
        wfj.assert_successful()
        job.assert_successful()
        assert '"var1": "var1_default"' in job.result_stdout
        assert '"var2": "var2_default"' in job.result_stdout

    def test_survey_default_must_be_from_choices(self, factories):
        wfjt = factories.workflow_job_template()
        survey = [dict(required=False,
                   question_name='Test-Default-MultiSelect',
                   variable='var1',
                   type='multiselect',
                   default='var1_default',
                   choices='not\nan\noption')]

        with pytest.raises(exc.BadRequest) as e:
            wfjt.add_survey(spec=survey)

        assert 'Default choice must be answered from the choices listed' in str(e)

        survey = [dict(required=False,
                question_name='Test-Default-MultipleChoice',
                variable='var1',
                type='multiplechoice',
                default='var1_default',
                choices='not\nan\noption')]

        with pytest.raises(exc.BadRequest) as e:
            wfjt.add_survey(spec=survey)

        assert 'Default choice must be answered from the choices listed' in str(e)

    def test_wfjt_and_wfjn_jt_survey_password_defaults_passed_to_jobs(self, debug_extra_vars_job_template, factories):
        wfjt = factories.workflow_job_template()
        jt = debug_extra_vars_job_template
        factories.workflow_job_template_node(workflow_job_template=wfjt, unified_job_template=jt)

        wfjt.add_survey(spec=self.survey)

        jt_survey = copy.deepcopy(self.survey)
        jt_survey[0]['default'] = 'wfjn_var1_default'
        jt_survey[1]['default'] = 'wfjn_var2_default'
        jt.add_survey(jt_survey)

        wfj1 = wfjt.launch().wait_until_completed(timeout=120)
        job1 = jt.get().related.last_job.get()
        wfj1.assert_successful()
        job1.assert_successful()
        assert '"var1": "var1_default"' in job1.result_stdout
        assert '"var2": "var2_default"' in job1.result_stdout

        wfj2 = wfj1.relaunch().wait_until_completed()
        job2 = jt.related.last_job.get()
        wfj2.assert_successful()
        job2.assert_successful()
        assert '"var1": "var1_default"' in job2.result_stdout
        assert '"var2": "var2_default"' in job2.result_stdout

    def test_wfjt_survey_with_required_and_optional_fields(self, debug_extra_vars_job_template, factories):
        wfjt = factories.workflow_job_template()
        jt = debug_extra_vars_job_template
        factories.workflow_job_template_node(workflow_job_template=wfjt, unified_job_template=jt)

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
        wfjt.add_survey(spec=survey)

        wfj = wfjt.launch(dict(extra_vars=dict(var1='launch'))).wait_until_completed(timeout=120)
        job = jt.get().related.last_job.get()
        wfj.assert_successful()
        job.assert_successful()
        assert '"var1": "launch"' in job.result_stdout
        assert '"var2": "var2_default"' in job.result_stdout

        assert json.loads(wfj.extra_vars) == dict(var1='$encrypted$', var2='$encrypted$')
        assert json.loads(job.extra_vars) == dict(var1='$encrypted$', var2='$encrypted$')

    def test_null_wfjt_survey_defaults_passed_to_jobs(self, debug_extra_vars_job_template, factories):
        wfjt = factories.workflow_job_template()
        jt = debug_extra_vars_job_template
        factories = factories.workflow_job_template_node(workflow_job_template=wfjt, unified_job_template=jt)

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
        wfjt.add_survey(spec=survey)

        survey[0]['default'] = 'jt_default1'
        survey[1]['default'] = 'jt_default2'
        jt.add_survey(spec=survey)

        wfj = wfjt.launch().wait_until_completed(timeout=120)
        job = jt.get().related.last_job.get()
        wfj.assert_successful()
        job.assert_successful()
        assert '"var1": ""' in job.result_stdout
        assert '"var2": ""' in job.result_stdout

    def test_survey_variables_overriden_when_supplied_at_launch(self, debug_extra_vars_job_template, factories):
        wfjt = factories.workflow_job_template()
        jt = debug_extra_vars_job_template
        factories.workflow_job_template_node(workflow_job_template=wfjt, unified_job_template=jt)

        survey = [dict(required=True,
                       question_name='Test-1',
                       variable='var1',
                       type='password',
                       default='var1_default'),
                  dict(required=False,
                       question_name='Test-2',
                       variable='var2',
                       type='text',
                       default='var2_default')]
        wfjt.add_survey(spec=survey)

        wfj = wfjt.launch(dict(extra_vars=dict(var1='var1_launch',
                                               var2='var2_launch'))).wait_until_completed()
        job = jt.get().related.last_job.get()
        wfj.assert_successful()
        job.assert_successful()
        assert '"var1": "var1_launch"' in job.result_stdout
        assert '"var2": "var2_launch"' in job.result_stdout

    def test_only_select_wfjt_survey_fields_editable(self, debug_extra_vars_job_template, factories):
        wfjt = factories.workflow_job_template()
        jt = debug_extra_vars_job_template
        factories.workflow_job_template_node(workflow_job_template=wfjt, unified_job_template=jt)

        survey = [dict(required=True,
                       question_name='Q',
                       variable='var1',
                       type='password',
                       default="don't update me")]
        wfjt.add_survey(spec=survey)

        question = survey[0]
        for update in [dict(variable='var2', default='$encrypted$'),
                       dict(variable='var1', type='text')]:
            question.update(update)
            with pytest.raises(exc.BadRequest):
                wfjt.add_survey(spec=survey)

        question.update(dict(type='password', required=False, question_name='Q-new'))
        updated_survey = wfjt.add_survey(spec=survey)
        assert updated_survey['spec'][0]['required'] is False
        assert updated_survey['spec'][0]['question_name'] == 'Q-new'

        wfjt.launch().wait_until_completed()
        job = jt.get().related.last_job.get()
        job.assert_successful()
        assert '"var1": "don\'t update me"' in job.result_stdout
