import json
import copy

from awxkit import utils
from awxkit.exceptions import NoContent, BadRequest, Forbidden
import pytest

from tests.api import APITest


@pytest.mark.usefixtures('authtoken')
class TestWorkflowExtraVars(APITest):

    def test_launch_with_workflow_extra_vars(self, factories, workflow_job_template_with_extra_vars, job_template):
        """Verify that WFJs and WFN jobs inherit WFJT extra_vars."""
        factories.workflow_job_template_node(workflow_job_template=workflow_job_template_with_extra_vars, unified_job_template=job_template)

        wfj = workflow_job_template_with_extra_vars.launch().wait_until_completed()
        wfj.assert_successful()

        nodes = wfj.related.workflow_nodes.get()
        assert len(nodes.results) == 1, "Only expecting one node, found:\n\n{0}".format(nodes)
        node_job = nodes.results.pop().related.job.get()
        node_job.assert_successful()

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
        wfj.assert_successful()

        nodes = wfj.related.workflow_nodes.get()
        assert len(nodes.results) == 1, "Only expecting one node, found:\n\n{0}".format(nodes)
        node_job = nodes.results.pop().related.job.get()
        node_job.assert_successful()

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
        wfj.assert_successful()

        nodes = wfj.related.workflow_nodes.get()
        assert len(nodes.results) == 1, "Only expecting one node, found:\n\n{0}".format(nodes)
        node_job = nodes.results.pop().related.job.get()
        node_job.assert_successful()

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
        wfj.assert_successful()

        nodes = wfj.related.workflow_nodes.get()
        assert len(nodes.results) == 1, "Only expecting one node, found:\n\n{0}".format(nodes)
        node_job = nodes.results.pop().related.job.get()
        node_job.assert_successful()

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
        wfj.assert_successful()

        nodes = wfj.related.workflow_nodes.get()
        assert len(nodes.results) == 1, "Only expecting one node, found:\n\n{0}".format(nodes)
        node_job = nodes.results.pop().related.job.get()
        node_job.assert_successful()

        # assert expected wfj and node job extra_vars
        survey_vars = survey_spec.get_default_vars()
        wfj_vars = json.loads(wfj.extra_vars)
        node_job_vars = json.loads(node_job.extra_vars)

        assert not wfj_vars
        assert node_job_vars == survey_vars

    def test_launch_with_job_template_and_job_template_survey_extra_vars(self, factories, job_template_with_extra_vars,
                                                                         required_survey_spec):
        """Verify that WFN jobs inerhit JT and JT survey extra_vars. JT survey extra_vars
        should take precedence over JT extra_vars."""
        wfjt = factories.workflow_job_template()
        factories.workflow_job_template_node(workflow_job_template=wfjt, unified_job_template=job_template_with_extra_vars)
        survey_spec = job_template_with_extra_vars.add_survey(spec=required_survey_spec)

        wfj = wfjt.launch().wait_until_completed()
        wfj.assert_successful()

        nodes = wfj.related.workflow_nodes.get()
        assert len(nodes.results) == 1, "Only expecting one node, found:\n\n{0}".format(nodes)
        node_job = nodes.results.pop().related.job.get()
        node_job.assert_successful()

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
        wfj.assert_successful()

        nodes = wfj.related.workflow_nodes.get()
        assert len(nodes.results) == 1, "Only expecting one node, found:\n\n{0}".format(nodes)
        node_job = nodes.results.pop().related.job.get()
        node_job.assert_successful()

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
        wfj.assert_successful()

        nodes = wfj.related.workflow_nodes.get()
        assert len(nodes.results) == 1, "Only expecting one node, found:\n\n{0}".format(nodes)
        node_job = nodes.results.pop().related.job.get()
        node_job.assert_successful()

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
        host = factories.host()
        wfjt = factories.workflow_job_template(ask_variables_on_launch=True)
        jt = factories.job_template(inventory=host.ds.inventory, playbook='debug_extra_vars.yml')
        factories.workflow_job_template_node(workflow_job_template=wfjt, unified_job_template=jt)

        wfj = wfjt.launch(dict(extra_vars=dict(var1='launch', var2='$encrypted$'))).wait_until_completed()
        job = jt.get().related.last_job.get()
        wfj.assert_successful()
        job.assert_successful()
        assert '"var1": "launch"' in job.result_stdout
        assert '"var2": "$encrypted$"' in job.result_stdout

        assert json.loads(wfj.extra_vars) == dict(var1='launch', var2='$encrypted$')
        assert json.loads(job.extra_vars) == dict(var1='launch', var2='$encrypted$')

    def test_extra_vars_not_passed_with_wfjt_when_ask_variables_enabled_and_none_supplied(self, factories):
        host = factories.host()
        wfjt = factories.workflow_job_template(ask_variables_on_launch=True)
        jt = factories.job_template(inventory=host.ds.inventory, playbook='debug_extra_vars.yml')
        factories.workflow_job_template_node(workflow_job_template=wfjt, unified_job_template=jt)

        wfj = wfjt.launch(dict(extra_vars=dict())).wait_until_completed()
        job = jt.get().related.last_job.get()
        wfj.assert_successful()
        job.assert_successful()

        assert json.loads(wfj.extra_vars) == dict()
        assert json.loads(job.extra_vars) == dict()

    def test_extra_vars_passed_with_wfjt_when_encrypted_keywords_supplied_at_launch(self, instance_group, factories):
        host = factories.host()
        wfjt = factories.workflow_job_template(ask_variables_on_launch=True)
        jt = factories.job_template(inventory=host.ds.inventory, playbook='debug_extra_vars.yml')
        jt.add_instance_group(instance_group)
        factories.workflow_job_template_node(workflow_job_template=wfjt, unified_job_template=jt)

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
        wfj = wfjt.launch(dict(extra_vars=payload)).wait_until_completed(timeout=600)
        job = jt.get().related.last_job.get()
        wfj.assert_successful()
        job.assert_successful()
        assert '"var1": "$encrypted$"' in job.result_stdout
        assert '"var2": "survey"' in job.result_stdout

        assert json.loads(wfj.extra_vars) == dict(var1='$encrypted$', var2='$encrypted$', var3='$encrypted$')
        assert json.loads(job.extra_vars) == dict(var1='$encrypted$', var2='$encrypted$', var3='$encrypted$')

    @pytest.mark.parametrize('required', [True, False])
    def test_launch_vars_passed_with_wfjt_when_launch_vars_and_survey_defaults_present(self, factories, required):
        host = factories.host()
        wfjt = factories.workflow_job_template(ask_variables_on_launch=True)
        jt = factories.job_template(inventory=host.ds.inventory, playbook='debug_extra_vars.yml')
        factories.workflow_job_template_node(workflow_job_template=wfjt, unified_job_template=jt)

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
        wfj.assert_successful()
        job.assert_successful()
        assert '"var1": "launch"' in job.result_stdout
        assert '"var2": "launch"' in job.result_stdout

        assert json.loads(wfj.extra_vars) == dict(var1='launch', var2='$encrypted$', var3='$encrypted$')
        assert json.loads(job.extra_vars) == dict(var1='launch', var2='$encrypted$', var3='$encrypted$')

    @pytest.mark.parametrize('required', [True, False])
    def test_survey_vars_passed_with_wfjt_when_launch_vars_absent_and_survey_defaults_present(self, factories, required):
        """Verifies behavior for default survey responses.
            Required (True): Job should fail to start
            Not Required (False): Job should start and the defaults should be used
        """
        host = factories.host()
        wfjt = factories.workflow_job_template(ask_variables_on_launch=True)
        jt = factories.job_template(inventory=host.ds.inventory, playbook='debug_extra_vars.yml')
        factories.workflow_job_template_node(workflow_job_template=wfjt, unified_job_template=jt)

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

        if not required:
            wfj = wfjt.launch(dict(extra_vars=dict())).wait_until_completed()
            job = jt.get().related.last_job.get()
            wfj.assert_successful()
            job.assert_successful()
            assert '"var1": "survey"' in job.result_stdout
            assert '"var2": "survey"' in job.result_stdout

            assert json.loads(wfj.extra_vars) == dict(var1='survey', var2='$encrypted$')
            assert json.loads(job.extra_vars) == dict(var1='survey', var2='$encrypted$')

        if required:
            with pytest.raises(BadRequest) as e:
                wfjt.launch(dict(extra_vars=dict())).wait_until_completed()
            assert "variables_needed_to_start" in e.value.msg

    @pytest.mark.parametrize('jt_prompts', ['same', 'none', 'all'])
    def test_launch_vars_passed_with_wfjt_when_launch_vars_and_multiple_surveys_present(self, instance_group, factories, jt_prompts):
        org = factories.organization()
        inv = factories.inventory(organization=org)
        factories.host(inventory=inv)
        wfjt = factories.workflow_job_template(
            ask_variables_on_launch=True,
            extra_vars=dict(var1='wfjt', var2='wfjt'),
            organization=org
        )
        project = factories.project(organization=org)
        jt = factories.job_template(inventory=inv, playbook='debug_extra_vars.yml', project=project,
                                       extra_vars=dict(var1='jt', var2='jt'))
        jt.add_instance_group(instance_group)
        factories.workflow_job_template_node(workflow_job_template=wfjt, unified_job_template=jt)

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

        if jt_prompts == 'same':
            jt_survey = copy.deepcopy(wfjt_survey)
            jt_survey[0]['default'] = 'wfjn_var1_default'
            jt_survey[1]['default'] = 'wfjn_var2_default'
            jt.add_survey(spec=jt_survey)
        if jt_prompts == 'all':
            jt.ask_variables_on_launch = True

        payload = dict(extra_vars=dict(var1='launch', var2='launch', var3='launch'))
        wfj = wfjt.launch(payload).wait_until_completed(timeout=600)
        job = jt.get().related.last_job.get()
        wfj.assert_successful()
        job.assert_successful()
        assert '"var1": "launch"' in job.result_stdout
        assert '"var2": "launch"' in job.result_stdout

        assert json.loads(wfj.extra_vars) == dict(var1='launch', var2='$encrypted$', var3='launch')
        assert json.loads(job.extra_vars) == dict(var1='launch', var2='$encrypted$', var3='launch')

        execute_user = factories.user()
        wfjt.set_object_roles(execute_user, 'execute')
        jt.set_object_roles(execute_user, 'execute')

        org_admin = factories.user(organization=org)
        org.set_object_roles(org_admin, 'admin')

        # also see https://github.com/ansible/tower/issues/3479 for background
        for other_user in (execute_user, org_admin):
            with self.current_user(other_user):
                # this is forbidden because original user gave var2='launch'
                # this is a password value, so should not be shared with other users
                with pytest.raises(Forbidden) as e:
                    wfj.relaunch()
                assert 'secret prompts provided by another user' in str(e.value.msg)
                with pytest.raises(Forbidden) as e:
                    job.relaunch()
                assert 'secret prompts provided by another user' in str(e.value.msg)

    def test_wfjt_nodes_source_variables_with_set_stats(self, instance_group, factories, artifacts_from_stats_playbook):
        host = factories.host()
        set_stats_jt = factories.job_template(playbook='test_set_stats.yml')
        set_stats_jt.add_instance_group(instance_group)
        no_stats_jt = factories.job_template()
        no_stats_jt.add_instance_group(instance_group)
        success_jt = factories.job_template()
        success_jt.add_instance_group(instance_group)
        failure_jt = factories.job_template(inventory=host.ds.inventory, playbook='fail_unless.yml')
        failure_jt.add_instance_group(instance_group)

        wfjt = factories.workflow_job_template()
        # Create common ancestor for two branches, one that has set_stats
        # passed downstream and another that has no stats set.
        ancestor = factories.workflow_job_template_node(workflow_job_template=wfjt, unified_job_template=no_stats_jt)
        stats_node = factories.workflow_job_template_node(workflow_job_template=wfjt, unified_job_template=set_stats_jt)
        with pytest.raises(NoContent):
            ancestor.related.success_nodes.post(dict(id=stats_node.id))
        # Create branch of nodes that should have no stats passed to them
        ancestor.add_always_node(unified_job_template=no_stats_jt).add_always_node(unified_job_template=no_stats_jt)
        stats_node.add_always_node(unified_job_template=success_jt).add_success_node(unified_job_template=failure_jt) \
            .add_failure_node(unified_job_template=success_jt)

        wfj = wfjt.launch().wait_until_completed(timeout=600)
        wfj.assert_successful()
        assert wfj.extra_vars == '{}'

        # verify jobs spawned as expected
        assert success_jt.related.jobs.get().count == 2
        assert failure_jt.related.jobs.get().count == 1

        # the root job produces the artifacts
        root_job = set_stats_jt.get().related.last_job.get()
        root_job.assert_successful()
        assert root_job.extra_vars == '{}'
        assert root_job.artifacts == artifacts_from_stats_playbook

        # downstram jobs consume those artifacts
        for job in success_jt.related.jobs.get().results + failure_jt.related.jobs.get().results:
            sourced_vars = json.loads(job.extra_vars)
            assert sourced_vars == artifacts_from_stats_playbook

        for job in no_stats_jt.related.jobs.get().results:
            sourced_vars = json.loads(job.extra_vars)
            assert sourced_vars == {}, 'Variables ended up in other jobs where set_stats should not have propogated.'

    @pytest.mark.parametrize("res_type", [
        'inventory_source',
        'project',
        'workflow_job_template'
    ])
    def test_artifacts_pass_through_non_job(self, instance_group, factories, artifacts_from_stats_playbook, res_type):
        """This test sandwiches two jobs between a non-job type, like
        job1 -> inventory update -> job2
        With this configuration, job1 uses set_stats
        Doing this, we confirm that job2 receives the vars from artifacts,
        and we confirm that the non-job job is not in any way broken
        """
        set_stats_jt = factories.job_template(playbook='test_set_stats.yml')
        set_stats_jt.add_instance_group(instance_group)
        wfjt = factories.workflow_job_template()
        stats_node = factories.workflow_job_template_node(
            workflow_job_template=wfjt,
            unified_job_template=set_stats_jt
        )
        non_job_node = stats_node.add_always_node(
            unified_job_template=getattr(factories, res_type)()
        )
        receiving_jt = factories.job_template(
            ask_variables_on_launch=True
        )
        receiving_jt.add_instance_group(instance_group)
        non_job_node.add_always_node(
            unified_job_template=receiving_jt
        )

        workflow_job = wfjt.launch()

        receiving_node = workflow_job.related.workflow_nodes.get(
            unified_job_template=receiving_jt.id
        ).results.pop()
        stats_node = workflow_job.related.workflow_nodes.get(
            unified_job_template=set_stats_jt.id
        ).results.pop()
        stats_node.wait_for_job(timeout=120)
        receiving_node.wait_for_job(timeout=120)
        receiving_job = receiving_node.get_related('job')
        assert json.loads(receiving_job.extra_vars) == artifacts_from_stats_playbook

        workflow_job.wait_until_completed()
        workflow_job.assert_successful()

    def test_artifacts_passed_to_workflow_nodes(self, instance_group, factories, artifacts_from_stats_playbook):
        """Test artifacts used with workflows-in-workflows
        """
        set_stats_jt = factories.job_template(playbook='test_set_stats.yml')
        set_stats_jt.add_instance_group(instance_group)
        receiving_jt = factories.job_template(ask_variables_on_launch=True)
        receiving_jt.add_instance_group(instance_group)
        receiving_wfjt = factories.workflow_job_template(ask_variables_on_launch=True)
        factories.workflow_job_template_node(
            workflow_job_template=receiving_wfjt,
            unified_job_template=receiving_jt
        )

        wfjt = factories.workflow_job_template()
        stats_node = factories.workflow_job_template_node(
            workflow_job_template=wfjt,
            unified_job_template=set_stats_jt
        )
        stats_node.add_always_node(unified_job_template=receiving_wfjt)

        workflow_job = wfjt.launch()

        receiving_wfjt_node = workflow_job.related.workflow_nodes.get(
            unified_job_template=receiving_wfjt.id
        ).results.pop()
        receiving_wfjt_node.wait_for_job(timeout=120)
        receiving_wfjt_job = receiving_wfjt_node.get_related('job')
        assert json.loads(receiving_wfjt_job.extra_vars) == artifacts_from_stats_playbook

        receiving_jt_node = receiving_wfjt_job.related.workflow_nodes.get(
            unified_job_template=receiving_jt.id
        ).results.pop()
        receiving_jt_node.wait_for_job(timeout=120)
        receiving_job = receiving_jt_node.get_related('job')
        assert json.loads(receiving_job.extra_vars) == artifacts_from_stats_playbook

        workflow_job.wait_until_completed(timeout=600)
        workflow_job.assert_successful()
