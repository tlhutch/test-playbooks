import logging
import json

from awxkit.exceptions import BadRequest
import pytest

from tests.api import APITest


log = logging.getLogger(__name__)

# Creating
# [ ] Node using (a) job template (b) project update (c) inventory update
# [ ] API browser's json template for node includes {success,failure,always} nodes. Can you post values for these?
# [ ] Able to use same node in multiple workflows
# [x] (-) Cannot use system job template
# [x] (-) Cannot use workflow job template
# [ ] (-) Cannot create node without specifying unified_job_template
# [ ] (-) Cannot use bad id for unified job template / workflow template
# [ ] (-) Configure node to trigger itself (e.g. on success)

# Deleting
# [ ] Deleting unified job template used by node
# [ ] Deleting workflow job template used by node


@pytest.mark.usefixtures('authtoken')
class Test_Workflow_Nodes(APITest):

    select_jt_fields = ('inventory', 'project', 'playbook', 'job_type')
    promptable_fields = ('inventory', 'job_type', 'job_tags', 'skip_tags', 'verbosity', 'diff_mode', 'limit')

    def test_workflow_node_jobs_should_source_from_underlying_template(self, factories):
        host = factories.host()
        wfjt = factories.workflow_job_template()
        jt = factories.job_template(inventory=host.ds.inventory, playbook='debug_extra_vars.yml')
        wf_node = factories.workflow_job_template_node(workflow_job_template=wfjt, unified_job_template=jt)

        survey = [dict(required=True,
                       question_name='Q1',
                       variable='var1',
                       type='text',
                       default='survey'),
                  dict(required=True,
                       question_name='Q2',
                       variable='var2',
                       type='password',
                       default='survey')]
        jt.add_survey(spec=survey)

        wfj = wfjt.launch().wait_until_completed()
        job = jt.get().related.last_job.get()

        wfj.assert_successful()
        job.assert_successful()
        assert json.loads(job.extra_vars) == {'var1': 'survey', 'var2': '$encrypted$'}

        # verify job sources JT and not wf node
        for field in self.select_jt_fields:
            assert getattr(jt, field) == getattr(job, field)
        for field in self.promptable_fields:
            assert getattr(jt, field) == getattr(job, field)
            assert getattr(wf_node, field) != getattr(job, field)
        job_creds = [cred.id for cred in job.related.credentials.get().results]
        wf_creds = [cred.id for cred in wf_node.related.credentials.get().results]
        jt_creds = [cred.id for cred in jt.related.credentials.get().results]
        assert sorted(job_creds) != sorted(wf_creds)
        assert sorted(job_creds) == sorted(jt_creds)

    def test_workflow_node_values_take_precedence_over_template_values(self, factories, ask_everything_jt):
        host, credential = factories.host(), factories.credential()
        wfjt = factories.workflow_job_template()
        wf_node = factories.workflow_job_template_node(workflow_job_template=wfjt, unified_job_template=ask_everything_jt,
                                                          inventory=host.ds.inventory, job_type='check',
                                                          job_tags='always', skip_tags='wf_skip_tag', verbosity=5,
                                                          diff_mode=True, limit=host.name,
                                                          extra_data={'var1': 'wf_var', 'var2': 'wf_var'})

        wf_node.add_credential(credential)
        survey = [dict(required=True,
                       question_name='Q1',
                       variable='var1',
                       type='text',
                       default='survey_var'),
                  dict(required=True,
                       question_name='Q2',
                       variable='var2',
                       type='password',
                       default='survey_var')]
        ask_everything_jt.add_survey(spec=survey)

        wfj = wfjt.launch().wait_until_completed()
        job = ask_everything_jt.get().related.last_job.get()
        wfj.assert_successful()
        job.assert_successful()
        assert json.loads(job.extra_vars) == {'var1': 'wf_var', 'var2': '$encrypted$'}

        # verify job sources wf node and not JT
        jt_fields = [field for field in self.select_jt_fields if field not in ('project', 'playbook')]
        for field in jt_fields:
            assert getattr(ask_everything_jt, field) != getattr(job, field)
        for field in self.promptable_fields:
            assert getattr(ask_everything_jt, field) != getattr(job, field)
            assert getattr(wf_node, field) == getattr(job, field)
        job_creds = [cred.id for cred in job.related.credentials.get().results]
        jt_creds = [cred.id for cred in ask_everything_jt.related.credentials.get().results]
        assert sorted(job_creds) != sorted(jt_creds)

    def test_workflow_node_values_take_precedence_over_wfjt_values(self, factories):
        inner_wfjt = factories.workflow_job_template(
            ask_variables_on_launch=True,
            ask_inventory_on_launch=True
        )
        wfjt = factories.workflow_job_template()
        # HACK: unified_job_template does not work with the dependency store
        wfjt_node = wfjt.get_related('workflow_nodes').post(dict(
            extra_data={'var1': 'wfjtn'},
            inventory=factories.inventory().id,
            unified_job_template=inner_wfjt.id,
        ))
        # sanity assertions
        assert wfjt_node.inventory != inner_wfjt.inventory
        assert wfjt_node.extra_data == {'var1': 'wfjtn'}
        assert inner_wfjt.extra_vars == ''

        wfj = wfjt.launch()
        wfj_node = wfj.get_related('workflow_nodes').results.pop()
        wfj_node.wait_for_job()
        job = wfj_node.get_related('job')
        assert job.inventory == wfjt_node.inventory
        assert json.loads(job.extra_vars) == wfjt_node.extra_data

    def test_workflow_prompted_inventory_value_takes_precedence_over_wfjt_value(self, factories):
        inventory = factories.inventory()
        jt = factories.job_template(ask_inventory_on_launch=True)
        inner_wfjt = factories.workflow_job_template(
            ask_inventory_on_launch=True
        )
        factories.workflow_job_template_node(workflow_job_template=inner_wfjt, unified_job_template=jt)
        wfjt = factories.workflow_job_template(
            ask_inventory_on_launch=True
        )
        wfjt.get_related('workflow_nodes').post(dict(
            workflow_job_template=wfjt.id,
            unified_job_template=inner_wfjt.id
        ))

        wfj = wfjt.launch(dict(inventory=inventory.id))
        wfj_node = wfj.get_related('workflow_nodes').results.pop()
        wfj_node.wait_for_job()
        job = wfj_node.get_related('job')
        assert job.inventory == inventory.id

    @pytest.mark.parametrize('add_methods', ['add_success_node',
                                             'add_failure_node',
                                             'add_always_node',
                                             'add_failure_node add_success_node add_always_node'],
                             ids=['success_node', 'failure_node', 'always_node', 'all_type_nodes']
                             )
    def test_workflow_job_nodes_can_have_always_nodes_with_other_nodes(self, factories, add_methods):
        """Assert that a workflow job template node can have an always node mixed with other children nodes."""
        jt = factories.job_template()
        wfjt = factories.workflow_job_template()
        parent_node = factories.workflow_job_template_node(workflow_job_template=wfjt, unified_job_template=jt)
        parent_node.add_always_node(unified_job_template=jt)
        # add additional child nodes with a variety of conditions
        for add_method in add_methods.split(' '):
            add_node_method = getattr(parent_node, add_method)
            add_node_method(unified_job_template=jt)

    def test_workflow_job_template_nodes_can_contain_system_job_templates(self, factories, api_system_job_templates_pg):
        wfjt = factories.workflow_job_template()
        system_jts = api_system_job_templates_pg.get()
        system_jt_ids = [sjt.id for sjt in system_jts.results]
        assert system_jts.results, 'Failed to locate any system job templates.'

        for sjt in system_jts.results:
            wfjt.related.workflow_nodes.post(dict(unified_job_template=sjt.id))
        wfjt_nodes = wfjt.related.workflow_nodes.get()
        assert wfjt_nodes.count == system_jts.count
        assert set(system_jt_ids) == set([wfjt_node.unified_job_template for wfjt_node in wfjt_nodes.results])

    def test_workflow_job_template_node_cannot_be_created_without_wfjt(self, factories, api_workflow_job_template_nodes_pg):
        jt = factories.job_template()
        with pytest.raises(BadRequest) as exception:
            api_workflow_job_template_nodes_pg.post(dict(unified_job_template=jt.id))
        assert exception.value.msg == {'workflow_job_template': ['This field is required.']}

    def test_workflow_node_creation_rejected_when_source_jt_has_ask_disabled(self, factories):
        inventory = factories.inventory()
        credential = factories.credential()

        wfjt = factories.workflow_job_template()
        jt = factories.job_template()

        with pytest.raises(BadRequest) as e:
            wfjtn = factories.workflow_job_template_node(workflow_job_template=wfjt, unified_job_template=jt,
                                                         extra_data=dict(var1='wfjtn'), job_type='check', job_tags='wfjtn',
                                                         skip_tags='wfjtn', limit='wfjtn', diff_mode=True, verbosity=2,
                                                         inventory=inventory)
            wfjtn.add_credential(credential)
        assert e.value[1] == {'job_tags': ['Field is not configured to prompt on launch.'],
                              'verbosity': ['Field is not configured to prompt on launch.'],
                              'job_type': ['Field is not configured to prompt on launch.'],
                              'diff_mode': ['Field is not configured to prompt on launch.'],
                              'skip_tags': ['Field is not configured to prompt on launch.'],
                              'limit': ['Field is not configured to prompt on launch.'],
                              'inventory': ['Field is not configured to prompt on launch.'],
                              'extra_data': ['Variables var1 are not allowed on launch. '
                                             'Check the Prompt on Launch setting on the Job Template to include Extra Variables.']}

    def test_workflow_node_creation_rejected_when_source_wfjt_has_ask_disabled(self, factories):
        inventory = factories.inventory()

        wfjt = factories.workflow_job_template()
        inner_wfjt = factories.workflow_job_template()

        with pytest.raises(BadRequest) as e:
            # HACK: unified_job_template does not work with the dependency store
            wfjt.get_related('workflow_nodes').post(dict(
                extra_data={'var1': 'wfjtn'},
                inventory=inventory.id,
                unified_job_template=inner_wfjt.id,
            ))
        assert e.value[1] == {
            'inventory': ['Field is not configured to prompt on launch.'],
            'extra_data': ['Variables var1 are not allowed on launch. '
                         'Check the Prompt on Launch setting on the Workflow Job Template to include Extra Variables.']
        }

    def test_workflow_node_creation_rejected_when_source_jt_has_ask_credential_disabled(self, factories):
        credential = factories.credential()

        wfjt = factories.workflow_job_template()
        jt = factories.job_template()

        with pytest.raises(BadRequest) as e:
            wfjtn = factories.workflow_job_template_node(workflow_job_template=wfjt, unified_job_template=jt)
            wfjtn.add_credential(credential)
        assert e.value[1] == {'msg': 'Related template is not configured to accept credentials on launch.'}

    def test_workflow_node_creation_rejected_when_jt_has_ask_credential(self, factories):
        wfjt = factories.workflow_job_template()
        cred = factories.credential(ssh_key_data=self.credentials.ssh.encrypted.ssh_key_data, password='ASK',
                                       become_password='ASK', ssh_key_unlock='ASK')
        jt = factories.job_template(credential=cred)
        with pytest.raises(BadRequest) as e:
            factories.workflow_job_template_node(workflow_job_template=wfjt, unified_job_template=jt)
        assert e.value[1] == {'passwords_needed_to_start':
                              ['Saved launch configurations cannot provide passwords needed to start.']}

    def test_workflow_node_creation_rejected_when_jt_has_missing_dependencies(self, factories):
        jt = factories.job_template(inventory=None, ask_inventory_on_launch=True)
        wfjt = factories.workflow_job_template()

        with pytest.raises(BadRequest) as e:
            factories.workflow_job_template_node(workflow_job_template=wfjt, unified_job_template=jt)
        assert e.value[1]['resources_needed_to_start'] == ['Job Template inventory is missing or undefined.']

    def spec_example(self):
        return [dict(required=False, question_name="Text-default too short.",
                     variable='test_var_one', type='text', min=7, default=''),
                dict(required=False, question_name="Text-default too long.",
                     variable='test_var_two', type='text', max=1, default='four'),
                dict(required=False, question_name="Text-passed default with minimum.",
                     variable='test_var_three', type='text', min=0, default='abc'),
                dict(required=False, question_name="Text-passed default with maximum.",
                     variable='test_var_four', type='text', max=7, default='1'),
                dict(required=False, question_name="Text-passed default with compatible minimum and maximum.",
                     variable='test_var_five', type='text', min=1, max=5, default='four'),
                dict(required=False, question_name="Text-default too long.",
                     variable='test_var_six', type='text', min=4, max=4, default='asdfasdf'),
                dict(required=False, question_name="Password-default too short.",
                     variable='test_var_seven', type='password', min=7, default='four'),
                dict(required=False, question_name="Password-default too long.",
                     variable='test_var_eight', type='password', max=1, default='four'),
                dict(required=False, question_name="Password-passed default with minimum.",
                     variable='test_var_nine', type='password', min=1, default='abc'),
                dict(required=False, question_name='Password-passed default with maximum.',
                     variable='test_var_ten', type='password', max=7, default='abc'),
                dict(required=False, question_name="Password-passed default with compatible minimum and maximum.",
                     variable='test_var_eleven', type='password', min=1, max=5, default='four'),
                dict(required=False, question_name="Password-default too long.",
                     variable='test_var_twelve', type='password', min=4, max=4, default='asdfasdf')]

    def test_workflow_nodes_must_abide_to_jt_survey_requirements(self, factories):
        wfjt = factories.workflow_job_template()
        jt = factories.job_template()
        jt.add_survey(spec=self.spec_example())

        with pytest.raises(BadRequest) as e:
            factories.workflow_job_template_node(workflow_job_template=wfjt, unified_job_template=jt,
                extra_data=dict(test_var_one='', test_var_two='four', test_var_three='abc',
                                test_var_four='1', test_var_five='four', test_var_six='asdfasdf',
                                test_var_seven='$encrypted$', test_var_eight='$encrypted$',
                                test_var_nine='$encrypted$', test_var_ten='$encrypted$',
                                test_var_eleven='$encrypted$', test_var_twelve='$encrypted$'))
        assert e.value[1] == dict(variables_needed_to_start=[
            "'test_var_one' value  is too small (length is 0 must be at least 7).",
            "'test_var_two' value four is too large (must be no more than 1).",
            "'test_var_six' value asdfasdf is too large (must be no more than 4)."])

    def test_node_encrypted_extra_data(self, factories):
        wfjt = factories.workflow_job_template()
        jt = factories.job_template()
        jt.add_survey(spec=self.spec_example())
        factories.workflow_job_template_node(workflow_job_template=wfjt, unified_job_template=jt,
            extra_data=dict(
                test_var_seven='$encrypted$', test_var_eight='f',
                test_var_nine='foo', test_var_ten='zar',
                test_var_eleven='woo', test_var_twelve='zzzz'
            )
        )
        workflow_job = wfjt.launch()
        node = workflow_job.get_related('workflow_nodes').results.pop()
        node.wait_for_job()
        job = node.get_related('job')
        job_vars = json.loads(job.extra_vars)
        assert 'test_var_seven' not in job_vars
        for var in ['test_var_eight', 'test_var_eight',
                'test_var_eight', 'test_var_eight', 'test_var_eight']:
            assert job_vars[var] == '$encrypted$'
