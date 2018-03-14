import pytest
import logging

from tests.api import Base_Api_Test

from towerkit.exceptions import BadRequest

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


@pytest.mark.api
@pytest.mark.destructive
@pytest.mark.usefixtures('authtoken', 'install_enterprise_license_unlimited')
class Test_Workflow_Nodes(Base_Api_Test):

    # Node cannot point to Workflow Job Template or System Job

    def test_workflow_job_template_node_cannot_contain_workflow_job_template(self, factories):
        wfjt = factories.workflow_job_template()
        with pytest.raises(BadRequest):
            wfjt.related.workflow_nodes.post(dict(unified_job_template=wfjt.id))

    def test_workflow_job_template_nodes_can_contain_system_job_templates(self, factories, api_system_job_templates_pg):
        wfjt = factories.workflow_job_template()
        system_jts = api_system_job_templates_pg.get()
        assert system_jts.results, 'Failed to locate any system job templates.'

        for sjt in system_jts.results:
            wfjt.related.workflow_nodes.post(dict(unified_job_template=sjt.id))

    def test_workflow_job_template_node_cannot_be_created_without_wfjt(self, factories, api_workflow_job_template_nodes_pg):
        jt = factories.job_template()
        with pytest.raises(BadRequest) as exception:
            api_workflow_job_template_nodes_pg.post(dict(unified_job_template=jt.id))
        assert 'Workflow job template is missing during creation' in str(exception.value)

    def test_workflow_job_template_node_cannot_be_created_without_job_template(self, factories, api_workflow_job_template_nodes_pg):
        wfjt = factories.workflow_job_template()
        with pytest.raises(BadRequest) as exception:
            api_workflow_job_template_nodes_pg.post(dict(workflow_job_template=wfjt.id))
        assert 'unified_job_template' in str(exception.value)
        assert 'This field cannot be blank.' in str(exception.value)

    @pytest.mark.github('https://github.com/ansible/ansible-tower/issues/7848')
    def test_workflow_node_creation_rejected_when_source_jt_has_ask_disabled(self, factories):
        inventory = factories.v2_inventory()
        credential = factories.v2_credential()

        wfjt = factories.v2_workflow_job_template()
        jt = factories.v2_job_template()

        with pytest.raises(BadRequest) as e:
            factories.v2_workflow_job_template_node(workflow_job_template=wfjt, unified_job_template=jt,
                                                    extra_data=dict(var1='wfjtn'), job_type='check', job_tags='wfjtn',
                                                    skip_tags='wfjtn', limit='wfjtn', diff_mode=True, verbosity=2,
                                                    inventory=inventory, credential=credential)
        assert e.value[1] == {'job_tags': ['Field is not configured to prompt on launch.'],
                              'verbosity': ['Field is not configured to prompt on launch.'],
                              'job_type': ['Field is not configured to prompt on launch.'],
                              'diff_mode': ['Field is not configured to prompt on launch.'],
                              'skip_tags': ['Field is not configured to prompt on launch.'],
                              'limit': ['Field is not configured to prompt on launch.'],
                              'inventory': ['Field is not configured to prompt on launch.'],
                              # 'credential': ['Field is not configured to prompt on launch.'],
                              'extra_data': ['Variables var1 are not allowed on launch. ' \
                                             'Check the Prompt on Launch setting on the Job Template to include Extra Variables.']}

    def test_workflow_node_creation_rejected_when_jt_has_ask_credential(self, factories):
        wfjt = factories.v2_workflow_job_template()
        cred = factories.v2_credential(ssh_key_data=self.credentials.ssh.encrypted.ssh_key_data, password='ASK',
                                       become_password='ASK', ssh_key_unlock='ASK')
        jt = factories.v2_job_template(credential=cred)
        with pytest.raises(BadRequest) as e:
            factories.v2_workflow_job_template_node(workflow_job_template=wfjt, unified_job_template=jt)
        assert e.value[1] == {'passwords_needed_to_start':
                              ['Saved launch configurations cannot provide passwords needed to start.']}

    def test_workflow_node_creation_rejected_when_jt_has_missing_dependencies(self, factories):
        jt = factories.v2_job_template(inventory=None, ask_inventory_on_launch=True)
        wfjt = factories.v2_workflow_job_template()

        with pytest.raises(BadRequest) as e:
            factories.v2_workflow_job_template_node(workflow_job_template=wfjt, unified_job_template=jt)
        assert e.value[1]['resources_needed_to_start'] == ['Job Template inventory is missing or undefined.']

    @pytest.mark.github('https://github.com/ansible/ansible-tower/issues/7864')
    def test_workflow_nodes_must_abide_to_jt_survey_requirements(self, factories):
        wfjt = factories.v2_workflow_job_template()
        jt = factories.v2_job_template()
        spec = [dict(required=False, question_name="Text-default too short.",
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
        jt.add_survey(spec=spec)

        with pytest.raises(BadRequest) as e:
            factories.v2_workflow_job_template_node(workflow_job_template=wfjt, unified_job_template=jt,
                extra_data=dict(test_var_one='', test_var_two='four', test_var_three='abc',
                                test_var_four='1', test_var_five='four', test_var_six='asdfasdf',
                                test_var_seven='$encrypted$', test_var_eight='$encrypted$',
                                test_var_nine='$encrypted$', test_var_ten='$encrypted$',
                                test_var_eleven='$encrypted$', test_var_twelve='$encrypted$'))
        assert e.value[1] == dict(variables_needed_to_start=[
            "'test_var_one' value  is too small (length is 0 must be at least 7).",
            "'test_var_two' value four is too large (must be no more than 1).",
            "'test_var_six' value asdfasdf is too large (must be no more than 4)."])
