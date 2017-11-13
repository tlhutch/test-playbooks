import json

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
