import json
import copy

from towerkit import utils
import pytest

from tests.api import Base_Api_Test


@pytest.mark.usefixtures('authtoken', 'install_enterprise_license_unlimited')
class TestWorkflowExtraVars(Base_Api_Test):

    def test_launch_with_workflow_extra_vars(self, factories, workflow_job_template_with_extra_vars):
        """Verify that WFJs and WFN jobs inherit WFJT extra_vars."""
        factories.workflow_job_template_node(workflow_job_template=workflow_job_template_with_extra_vars)

        wfj = workflow_job_template_with_extra_vars.launch().wait_until_completed()
        assert wfj.is_successful

        nodes = wfj.related.workflow_nodes.get()
        assert len(nodes.results) == 1, "Only expecting one node, found:\n\n{0}".format(nodes)
        node_job = nodes.results.pop().related.job.get()
        assert node_job.is_successful

        # assert expected wfj and node job extra_vars
        wfjt_vars = utils.load_json_or_yaml(workflow_job_template_with_extra_vars.extra_vars)
        wfj_vars = json.loads(wfj.extra_vars)
        node_job_vars = json.loads(node_job.extra_vars)

        assert wfj_vars == wfjt_vars
        assert node_job_vars == wfjt_vars

    @pytest.mark.parametrize("launch_time_vars", [
        "{'likes_chicken': ['yes'], 'favorite_color': 'green'}",
        "---\nlikes_chicken:\n  - 'yes'\nfavorite_color: green"
    ], ids=['json', 'yaml'])
    def test_launch_with_workflow_survey_extra_vars(self, factories, required_survey_spec, launch_time_vars):
        """Verify that WFJs and WFN jobs inherit WFJT survey extra_vars."""
        wfjt = factories.workflow_job_template()
        factories.workflow_job_template_node(workflow_job_template=wfjt)
        survey_spec = wfjt.add_survey(spec=required_survey_spec)

        wfj = wfjt.launch(dict(extra_vars=launch_time_vars)).wait_until_completed()
        assert wfj.is_successful

        nodes = wfj.related.workflow_nodes.get()
        assert len(nodes.results) == 1, "Only expecting one node, found:\n\n{0}".format(nodes)
        node_job = nodes.results.pop().related.job.get()
        assert node_job.is_successful

        # assert expected wfj and node job extra_vars
        required_survey_vars = survey_spec.get_required_vars()
        default_survey_vars = survey_spec.get_default_vars()
        survey_vars = [var for var in default_survey_vars if var not in required_survey_vars]
        launch_time_vars = utils.load_json_or_yaml(launch_time_vars)

        wfj_vars = json.loads(wfj.extra_vars)
        node_job_vars = json.loads(node_job.extra_vars)

        assert set(survey_vars) < set(wfj_vars)
        assert set(launch_time_vars) < set(wfj_vars)
        assert set(wfj_vars) == set(survey_vars) | set(launch_time_vars)

        assert wfj_vars['survey_var'] == survey_spec.get_variable_default('survey_var')
        assert wfj_vars['likes_chicken'] == launch_time_vars['likes_chicken']
        assert wfj_vars['favorite_color'] == launch_time_vars['favorite_color']
        assert wfj_vars['intersection'] == survey_spec.get_variable_default('intersection')

        assert node_job_vars == wfj_vars

    def test_launch_without_workflow_survey_extra_vars(self, factories):
        """Verify that WFJs and WFN jobs do not inherit WFJT survey extra_vars
        when survey_enabled is disabled."""
        wfjt = factories.workflow_job_template()
        wfjt.add_survey(required=False, enabled=False)
        factories.workflow_job_template_node(workflow_job_template=wfjt)

        wfj = wfjt.launch().wait_until_completed()
        assert wfj.is_successful

        nodes = wfj.related.workflow_nodes.get()
        assert len(nodes.results) == 1, "Only expecting one node, found:\n\n{0}".format(nodes)
        node_job = nodes.results.pop().related.job.get()
        assert node_job.is_successful

        # assert expected wfj and node job extra_vars
        wfj_vars = json.loads(wfj.extra_vars)
        node_job_vars = json.loads(node_job.extra_vars)

        assert not wfj_vars
        assert not node_job_vars

    def test_launch_with_job_template_extra_vars(self, factories, job_template_with_extra_vars):
        """Verify that WFN jobs inherit JT extra_vars."""
        wfjt = factories.workflow_job_template()
        factories.workflow_job_template_node(workflow_job_template=wfjt, unified_job_template=job_template_with_extra_vars)

        wfj = wfjt.launch().wait_until_completed()
        assert wfj.is_successful

        nodes = wfj.related.workflow_nodes.get()
        assert len(nodes.results) == 1, "Only expecting one node, found:\n\n{0}".format(nodes)
        node_job = nodes.results.pop().related.job.get()
        assert node_job.is_successful

        # assert expected wfj and node job extra_vars
        jt_vars = utils.load_json_or_yaml(job_template_with_extra_vars.extra_vars)
        wfj_vars = json.loads(wfj.extra_vars)
        node_job_vars = json.loads(node_job.extra_vars)

        assert not wfj_vars
        assert node_job_vars == jt_vars

    def test_launch_with_job_template_survey_extra_vars(self, factories, job_template_variables_needed_to_start):
        """Verify that WFN jobs inherit JT survey default extra_vars. Also verify that WFN
        jobs succeed even though required survey variables are not supplied at launch.
        """
        wfjt = factories.workflow_job_template()
        factories.workflow_job_template_node(workflow_job_template=wfjt, unified_job_template=job_template_variables_needed_to_start)
        survey_spec = job_template_variables_needed_to_start.related.survey_spec.get()

        wfj = wfjt.launch().wait_until_completed()
        assert wfj.is_successful

        nodes = wfj.related.workflow_nodes.get()
        assert len(nodes.results) == 1, "Only expecting one node, found:\n\n{0}".format(nodes)
        node_job = nodes.results.pop().related.job.get()
        assert node_job.is_successful

        # assert expected wfj and node job extra_vars
        survey_vars = survey_spec.get_default_vars()
        wfj_vars = json.loads(wfj.extra_vars)
        node_job_vars = json.loads(node_job.extra_vars)

        assert not wfj_vars
        assert node_job_vars == survey_vars

    @pytest.mark.github("https://github.com/ansible/ansible-tower/issues/6344")
    def test_launch_with_job_template_and_job_template_survey_extra_vars(self, factories, job_template_with_extra_vars,
                                                                         required_survey_spec):
        """Verify that WFN jobs inerhit JT and JT survey extra_vars. JT survey extra_vars
        should take precedence over JT extra_vars."""
        wfjt = factories.workflow_job_template()
        factories.workflow_job_template_node(workflow_job_template=wfjt, unified_job_template=job_template_with_extra_vars)
        survey_spec = job_template_with_extra_vars.add_survey(spec=required_survey_spec)

        wfj = wfjt.launch().wait_until_completed()
        assert wfj.is_successful

        nodes = wfj.related.workflow_nodes.get()
        assert len(nodes.results) == 1, "Only expecting one node, found:\n\n{0}".format(nodes)
        node_job = nodes.results.pop().related.job.get()
        assert node_job.is_successful

        # assert expected wfj and node job extra_vars
        jt_vars = utils.load_json_or_yaml(job_template_with_extra_vars.extra_vars)
        survey_vars = survey_spec.get_default_vars()
        wfj_vars = json.loads(wfj.extra_vars)
        node_job_vars = json.loads(node_job.extra_vars)

        assert not wfj_vars

        assert set(node_job_vars) == set(jt_vars) | set(survey_vars)

        assert node_job_vars['jt_var'] == jt_vars['jt_var']
        assert node_job_vars['survey_var'] == survey_vars['survey_var']
        assert node_job_vars['favorite_color'] == survey_vars['favorite_color']
        assert node_job_vars['intersection'] == survey_vars['intersection']

    def test_launch_with_workflow_and_job_template_extra_vars(self, factories, workflow_job_template_with_extra_vars,
                                                              job_template_with_extra_vars):
        """Verify that WFJT and WFN jobs inherit WFJT extra_vars and
        that WFN jobs additionally inherit WFN extra_vars.
        """
        factories.workflow_job_template_node(workflow_job_template=workflow_job_template_with_extra_vars,
                                             unified_job_template=job_template_with_extra_vars)

        wfj = workflow_job_template_with_extra_vars.launch().wait_until_completed()
        assert wfj.is_successful

        nodes = wfj.related.workflow_nodes.get()
        assert len(nodes.results) == 1, "Only expecting one node, found:\n\n{0}".format(nodes)
        node_job = nodes.results.pop().related.job.get()
        assert node_job.is_successful

        # assert expected wfj and node job extra_vars
        jt_vars = utils.load_json_or_yaml(job_template_with_extra_vars.extra_vars)
        wfjt_vars = utils.load_json_or_yaml(workflow_job_template_with_extra_vars.extra_vars)
        wfj_vars = json.loads(wfj.extra_vars)
        node_job_vars = json.loads(node_job.extra_vars)

        assert wfj_vars == wfjt_vars

        assert set(jt_vars) < set(node_job_vars)
        assert set(wfjt_vars) < set(node_job_vars)
        assert set(node_job_vars) == set(jt_vars) | set(wfjt_vars)

        assert node_job_vars['jt_var'] == jt_vars['jt_var']
        assert node_job_vars['wfjt_var'] == wfjt_vars['wfjt_var']
        assert node_job_vars['intersection'] == wfjt_vars['intersection']

    def test_launch_with_workflow_and_job_template_and_both_survey_extra_vars(self, factories,
                                                                              workflow_job_template_with_extra_vars,
                                                                              job_template_with_extra_vars):
        """Verify WFJ and WFNJ extra_vars in an instance where our WFJT and
        WFN both have extra_vars and surveys.
        """
        wfjt_survey = [dict(required=False,
                            question_name='WFJT Intersection',
                            variable='intersection',
                            type='text',
                            default='wfjt survey'),
                       dict(required=False,
                            question_name='WFJT Variable',
                            variable='wfjt_survey',
                            type='text',
                            default='wfjt survey')]
        wfjt_survey = workflow_job_template_with_extra_vars.add_survey(spec=wfjt_survey)
        jt_survey = [dict(required=False,
                          question_name='JT Intersection',
                          variable='intersection',
                          type='text',
                          default='jt survey'),
                     dict(required=False,
                          question_name="JT Variable",
                          variable='jt_survey',
                          type='text',
                          default="jt survey")]
        jt_survey = job_template_with_extra_vars.add_survey(spec=jt_survey)
        factories.workflow_job_template_node(workflow_job_template=workflow_job_template_with_extra_vars,
                                             unified_job_template=job_template_with_extra_vars)

        wfj = workflow_job_template_with_extra_vars.launch().wait_until_completed()
        assert wfj.is_successful

        nodes = wfj.related.workflow_nodes.get()
        assert len(nodes.results) == 1, "Only expecting one node, found:\n\n{0}".format(nodes)
        node_job = nodes.results.pop().related.job.get()
        assert node_job.is_successful

        # assert expected wfj and node job extra_vars
        jt_vars = utils.load_json_or_yaml(job_template_with_extra_vars.extra_vars)
        jt_survey_vars = jt_survey.get_default_vars()
        wfjt_vars = utils.load_json_or_yaml(workflow_job_template_with_extra_vars.extra_vars)
        wfjt_survey_vars = wfjt_survey.get_default_vars()
        wfj_vars = json.loads(wfj.extra_vars)
        node_job_vars = json.loads(node_job.extra_vars)

        assert set(wfjt_vars) < set(wfj_vars)
        assert set(wfjt_survey_vars) < set(wfj_vars)
        assert set(wfj_vars) == set(wfjt_vars) | set(wfjt_survey_vars)

        assert wfj_vars['wfjt_var'] == wfjt_vars['wfjt_var']
        assert wfj_vars['wfjt_survey'] == wfjt_survey_vars['wfjt_survey']
        assert wfj_vars['intersection'] == wfjt_survey_vars['intersection']

        for extra_vars in [jt_vars, jt_survey_vars, wfjt_vars, wfjt_survey_vars]:
            assert set(extra_vars) < set(node_job_vars)
        assert set(node_job_vars) == set(jt_vars) | set(jt_survey_vars) | set(wfjt_vars) | set(wfjt_survey_vars)

        assert node_job_vars['jt_var'] == jt_vars['jt_var']
        assert node_job_vars['jt_survey'] == jt_survey_vars['jt_survey']
        assert node_job_vars['wfjt_var'] == wfjt_vars['wfjt_var']
        assert node_job_vars['wfjt_survey'] == wfjt_survey_vars['wfjt_survey']
        assert node_job_vars['intersection'] == wfjt_survey_vars['intersection']

    def test_extra_vars_passed_with_wfjt_when_ask_variables_enabled_and_launch_vars_supplied(self, factories):
        host = factories.v2_host()
        wfjt = factories.v2_workflow_job_template(ask_variables_on_launch=True)
        jt = factories.v2_job_template(inventory=host.ds.inventory, playbook='debug_extra_vars.yml')
        factories.v2_workflow_job_template_node(workflow_job_template=wfjt, unified_job_template=jt)

        wfj = wfjt.launch(dict(extra_vars=dict(var1='launch', var2='$encrypted$'))).wait_until_completed()
        job = jt.get().related.last_job.get()
        assert wfj.is_successful
        assert job.is_successful
        assert '"var1": "launch"' in job.result_stdout
        assert '"var2": "$encrypted$"' in job.result_stdout

        assert json.loads(wfj.extra_vars) == dict(var1='launch', var2='$encrypted$')
        assert json.loads(job.extra_vars) == dict(var1='launch', var2='$encrypted$')

    def test_extra_vars_not_passed_with_wfjt_when_ask_variables_enabled_and_none_supplied(self, factories):
        host = factories.v2_host()
        wfjt = factories.v2_workflow_job_template(ask_variables_on_launch=True)
        jt = factories.v2_job_template(inventory=host.ds.inventory, playbook='debug_extra_vars.yml')
        factories.v2_workflow_job_template_node(workflow_job_template=wfjt, unified_job_template=jt)

        wfj = wfjt.launch(dict(extra_vars=dict())).wait_until_completed()
        job = jt.get().related.last_job.get()
        assert wfj.is_successful
        assert job.is_successful

        assert json.loads(wfj.extra_vars) == dict()
        assert json.loads(job.extra_vars) == dict()

    def test_extra_vars_passed_with_wfjt_when_encrypted_keywords_supplied_at_launch(self, factories):
        host = factories.v2_host()
        wfjt = factories.v2_workflow_job_template(ask_variables_on_launch=True)
        jt = factories.v2_job_template(inventory=host.ds.inventory, playbook='debug_extra_vars.yml')
        factories.v2_workflow_job_template_node(workflow_job_template=wfjt, unified_job_template=jt)

        survey = [dict(required=False,
                       question_name='Q1',
                       variable='var1',
                       type='text',
                       default='survey'),
                  dict(required=False,
                       question_name='Q2',
                       variable='var2',
                       type='password',
                       default='survey')]
        wfjt.add_survey(spec=survey)

        # with var1, verify that a string survey variable passes $encrypted$ placeholder
        payload = dict(var1='$encrypted$', var2='$encrypted$', var3='$encrypted$')
        wfj = wfjt.launch(dict(extra_vars=payload)).wait_until_completed()
        job = jt.get().related.last_job.get()
        assert wfj.is_successful
        assert job.is_successful
        assert '"var1": "$encrypted$"' in job.result_stdout
        assert '"var2": "survey"' in job.result_stdout

        assert json.loads(wfj.extra_vars) == dict(var1='$encrypted$', var2='$encrypted$', var3='$encrypted$')
        assert json.loads(job.extra_vars) == dict(var1='$encrypted$', var2='$encrypted$', var3='$encrypted$')

    @pytest.mark.parametrize('required', [True, False])
    def test_launch_vars_passed_with_wfjt_when_launch_vars_and_survey_defaults_present(self, factories, required):
        host = factories.v2_host()
        wfjt = factories.v2_workflow_job_template(ask_variables_on_launch=True)
        jt = factories.v2_job_template(inventory=host.ds.inventory, playbook='debug_extra_vars.yml')
        factories.v2_workflow_job_template_node(workflow_job_template=wfjt, unified_job_template=jt)

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
        wfjt.add_survey(spec=survey)

        payload = dict(var1='launch', var2='launch', var3='$encrypted$')
        wfj = wfjt.launch(dict(extra_vars=payload)).wait_until_completed()
        job = jt.get().related.last_job.get()
        assert wfj.is_successful
        assert job.is_successful
        assert '"var1": "launch"' in job.result_stdout
        assert '"var2": "launch"' in job.result_stdout

        assert json.loads(wfj.extra_vars) == dict(var1='launch', var2='$encrypted$', var3='$encrypted$')
        assert json.loads(job.extra_vars) == dict(var1='launch', var2='$encrypted$', var3='$encrypted$')

    @pytest.mark.parametrize('required', [True, False])
    def test_survey_vars_passed_with_wfjt_when_launch_vars_absent_and_survey_defaults_present(self, factories, required):
        host = factories.v2_host()
        wfjt = factories.v2_workflow_job_template(ask_variables_on_launch=True)
        jt = factories.v2_job_template(inventory=host.ds.inventory, playbook='debug_extra_vars.yml')
        factories.v2_workflow_job_template_node(workflow_job_template=wfjt, unified_job_template=jt)

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
        wfjt.add_survey(spec=survey)

        wfj = wfjt.launch(dict(extra_vars=dict())).wait_until_completed()
        job = jt.get().related.last_job.get()
        assert wfj.is_successful
        assert job.is_successful
        assert '"var1": "survey"' in job.result_stdout
        assert '"var2": "survey"' in job.result_stdout

        assert json.loads(wfj.extra_vars) == dict(var1='survey', var2='$encrypted$')
        assert json.loads(job.extra_vars) == dict(var1='survey', var2='$encrypted$')

    def test_launch_vars_passed_with_wfjt_when_launch_vars_and_multiple_surveys_present(self, factories):
        host = factories.v2_host()
        wfjt = factories.v2_workflow_job_template(ask_variables_on_launch=True, extra_vars=dict(var1='wfjt', var2='wfjt'))
        jt = factories.v2_job_template(inventory=host.ds.inventory, playbook='debug_extra_vars.yml',
                                       extra_vars=dict(var1='jt', var2='jt'))
        factories.v2_workflow_job_template_node(workflow_job_template=wfjt, unified_job_template=jt)

        wfjt_survey = [dict(required=False,
                            question_name='Q1',
                            variable='var1',
                            type='text',
                            default='survey'),
                       dict(required=False,
                            question_name='Q2',
                            variable='var2',
                            type='password',
                            default='survey')]
        wfjt.add_survey(spec=wfjt_survey)

        jt_survey = copy.deepcopy(wfjt_survey)
        jt_survey[0]['default'] = 'wfjn_var1_default'
        jt_survey[1]['default'] = 'wfjn_var2_default'
        jt.add_survey(spec=jt_survey)

        payload = dict(extra_vars=dict(var1='launch', var2='launch', var3='launch'))
        wfj = wfjt.launch(payload).wait_until_completed()
        job = jt.get().related.last_job.get()
        assert wfj.is_successful
        assert job.is_successful
        assert '"var1": "launch"' in job.result_stdout
        assert '"var2": "launch"' in job.result_stdout

        assert json.loads(wfj.extra_vars) == dict(var1='launch', var2='$encrypted$', var3='launch')
        assert json.loads(job.extra_vars) == dict(var1='launch', var2='$encrypted$', var3='launch')

    def test_wfjt_nodes_source_variables_with_set_stats(self, factories):
        host = factories.v2_host()
        set_stats_jt = factories.v2_job_template(playbook='test_set_stats.yml')
        success_jt = factories.v2_job_template()
        failure_jt = factories.v2_job_template(inventory=host.ds.inventory, playbook='fail_unless.yml')

        wfjt = factories.v2_workflow_job_template()
        stats_node = factories.v2_workflow_job_template_node(workflow_job_template=wfjt, unified_job_template=set_stats_jt)
        stats_node.add_always_node(unified_job_template=success_jt).add_success_node(unified_job_template=failure_jt) \
            .add_failure_node(unified_job_template=success_jt)

        wfj = wfjt.launch().wait_until_completed()
        assert wfj.is_successful
        assert wfj.extra_vars == '{}'
        assert set_stats_jt.get().related.last_job.get().extra_vars == '{}'

        for job in success_jt.related.jobs.get().results + failure_jt.related.jobs.get().results:
            sourced_vars = json.loads(job.extra_vars)
            assert sourced_vars['string'] == 'abc'
            assert sourced_vars['unicode'] == u'\u7af3\u466d\u97fd'
            assert sourced_vars['float'] == 1.0
            assert sourced_vars['integer'] == 123
            assert sourced_vars['boolean']
            assert not sourced_vars['none']
            assert sourced_vars['list'] == ['abc', 123, 1.0, u'\u7af3\u466d\u97fd', True, None, [], {}]
            assert sourced_vars['object'] == dict(string='abc', unicode=u'\u7af3\u466d\u97fd', float=1.0, integer=123, boolean=True,
                                                  none=None, list=[], object={})
            assert sourced_vars['empty_list'] == []
            assert sourced_vars['empty_object'] == {}
