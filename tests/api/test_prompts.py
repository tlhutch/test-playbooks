import copy
import json

from towerkit import utils
from towerkit import exceptions as exc
import pytest

from tests.api import Base_Api_Test


@pytest.mark.api
@pytest.mark.skip_selenium
@pytest.mark.usefixtures('authtoken', 'install_enterprise_license_unlimited')
class TestPrompts(Base_Api_Test):

    ask_jt_attrs = dict(ask_diff_mode_on_launch=True, ask_variables_on_launch=True,
                        ask_limit_on_launch=True, ask_tags_on_launch=True,
                        ask_skip_tags_on_launch=True, ask_job_type_on_launch=True,
                        ask_verbosity_on_launch=True, ask_inventory_on_launch=True,
                        ask_credential_on_launch=True)

    def test_created_schedule_with_default_jt(self, factories):
        jt = factories.v2_job_template()
        job = jt.launch().wait_until_completed()
        assert job.is_successful

        create_schedule = job.related.create_schedule.get()
        assert create_schedule.prompts == {}
        assert create_schedule.can_schedule

        schedule = create_schedule.post()
        assert schedule.name == 'Auto-generated schedule from job {}'.format(job.id)
        assert schedule.description == ''
        assert schedule.unified_job_template == jt.id
        assert not schedule.enabled

        assert not schedule.diff_mode
        assert schedule.extra_data == {}
        assert not schedule.limit
        assert not schedule.job_tags
        assert not schedule.skip_tags
        assert not schedule.job_type
        assert not schedule.verbosity
        assert not schedule.inventory
        assert schedule.related.credentials.get().count == 0

        rrule_dtstart = utils.to_str(schedule.dtstart).translate(None, '-:')
        assert schedule.rrule == "DTSTART:{0} RRULE:FREQ=MONTHLY;INTERVAL=1".format(rrule_dtstart)
        assert not schedule.dtend

    def test_created_schedule_with_ask_jt_and_launch_values(self, factories):
        jt = factories.v2_job_template(**self.ask_jt_attrs)
        job = jt.launch(dict(diff_mode=True, extra_vars=dict(var1='launch'), limit='launch', job_tags='launch',
                             skip_tags='launch', job_type='check', verbosity=5, inventory=jt.ds.inventory.id,
                             credentials=[jt.ds.credential.id])).wait_until_completed()
        assert job.is_successful

        create_schedule = job.related.create_schedule.get()
        assert create_schedule.prompts == dict(diff_mode=True, extra_vars=dict(var1='launch'),
                                               limit='launch', job_tags='launch', skip_tags='launch',
                                               job_type='check', verbosity=5)
        assert create_schedule.can_schedule

        schedule = create_schedule.post()
        assert schedule.name == 'Auto-generated schedule from job {}'.format(job.id)
        assert schedule.description == ''
        assert schedule.unified_job_template == jt.id
        assert not schedule.enabled

        assert schedule.diff_mode
        assert schedule.extra_data == dict(var1='launch')
        assert schedule.limit == 'launch'
        assert schedule.job_tags == 'launch'
        assert schedule.skip_tags == 'launch'
        assert schedule.job_type == 'check'
        assert schedule.verbosity == 5
        assert not schedule.inventory
        assert schedule.related.credentials.get().count == 0

        rrule_dtstart = utils.to_str(schedule.dtstart).translate(None, '-:')
        assert schedule.rrule == "DTSTART:{0} RRULE:FREQ=MONTHLY;INTERVAL=1".format(rrule_dtstart)
        assert not schedule.dtend

    def test_created_schedule_with_ask_jt_when_jt_defaults_supplied(self, factories):
        jt = factories.v2_job_template(**self.ask_jt_attrs)
        job = jt.launch(dict(diff_mode=jt.diff_mode, extra_vars=jt.extra_vars, limit=jt.limit, job_tags=jt.job_tags,
                             skip_tags=jt.skip_tags, job_type=jt.job_type, verbosity=jt.verbosity,
                             inventory=jt.ds.inventory.id, credentials=[jt.ds.credential.id])).wait_until_completed()
        assert job.is_successful

        create_schedule = job.related.create_schedule.get()
        assert create_schedule.prompts == {}
        assert create_schedule.can_schedule

        schedule = create_schedule.post()
        assert schedule.name == 'Auto-generated schedule from job {}'.format(job.id)
        assert schedule.description == ''
        assert schedule.unified_job_template == jt.id
        assert not schedule.enabled

        assert not schedule.diff_mode
        assert schedule.extra_data == {}
        assert not schedule.limit
        assert not schedule.job_tags
        assert not schedule.skip_tags
        assert not schedule.job_type
        assert not schedule.verbosity
        assert not schedule.inventory
        assert schedule.related.credentials.get().count == 0

        rrule_dtstart = utils.to_str(schedule.dtstart).translate(None, '-:')
        assert schedule.rrule == "DTSTART:{0} RRULE:FREQ=MONTHLY;INTERVAL=1".format(rrule_dtstart)
        assert not schedule.dtend

    def test_created_schedule_with_ask_inventory_and_credential_and_launch_resources(self, factories):
        inventory = factories.v2_inventory()
        ssh_cred, aws_cred = [factories.v2_credential(kind=kind) for kind in ('ssh', 'aws')]
        vault_cred = factories.v2_credential(kind='vault', inputs=dict(vault_password='fake'))
        credentials = [ssh_cred, aws_cred, vault_cred]
        cred_ids = [cred.id for cred in credentials]

        jt = factories.v2_job_template(ask_inventory_on_launch=True, ask_credential_on_launch=True)
        job = jt.launch(dict(inventory=inventory.id, credential=cred_ids)).wait_until_completed()
        assert job.is_successful

        create_schedule = job.related.create_schedule.get()
        assert create_schedule.prompts.inventory.id == inventory.id
        assert [cred.id for cred in create_schedule.prompts.credentials] == cred_ids
        assert create_schedule.can_schedule

        schedule = create_schedule.post()
        assert schedule.inventory == inventory.id
        schedule_creds = schedule.related.credentials.get()
        assert schedule_creds.count == 3
        for cred in schedule_creds.results:
            assert cred.id in cred_ids

    def test_launch_credentials_override_default_jt_credentials(self, factories):
        jt_vault, launch_vault = [factories.v2_credential(kind='vault', inputs=dict(vault_password='fake')) for _ in range(2)]
        jt_aws, jt_vmware = [factories.v2_credential(kind=kind) for kind in ('aws', 'vmware')]
        launch_aws, launch_vmware = [factories.v2_credential(kind=kind) for kind in ('aws', 'vmware')]

        jt = factories.v2_job_template(vault_credential=jt_vault.id, ask_credential_on_launch=True)
        for cred in (jt_aws, jt_vmware):
            with utils.suppress(exc.NoContent):
                jt.related.extra_credentials.post(dict(id=cred.id))

        launch_ssh = factories.v2_credential()
        launch_creds = [launch_ssh, launch_aws, launch_vmware, launch_vault]
        launch_cred_ids = [cred.id for cred in launch_creds]
        job = jt.launch(dict(credential=launch_cred_ids)).wait_until_completed()
        assert job.is_successful

        create_schedule = job.related.create_schedule.get()
        for cred in create_schedule.prompts.credentials:
            assert cred.id in launch_cred_ids
        assert create_schedule.can_schedule

        schedule = create_schedule.post()
        schedule_creds = schedule.related.credentials.get()
        assert schedule_creds.count == 4
        for cred in schedule_creds.results:
            assert cred.id in launch_cred_ids

    @pytest.mark.github('https://github.com/ansible/ansible-tower/issues/7844')
    def test_cannot_create_schedule_with_jt_with_ask_credential(self, factories):
        cred = factories.v2_credential(ssh_key_data=self.credentials.ssh.encrypted.ssh_key_data, password='ASK',
                                       become_password='ASK', ssh_key_unlock='ASK')
        jt = factories.v2_job_template(credential=cred)

        payload = dict(credential_passwords=dict(ssh_password='fake', become_password='fake',
                                                 ssh_key_unlock=self.credentials.ssh.encrypted.ssh_key_unlock))
        job = jt.launch(payload).wait_until_completed()
        assert job.is_successful

        create_schedule = job.related.create_schedule.get()
        assert create_schedule.prompts == {}
        assert not create_schedule.can_schedule

        with pytest.raises(exc.BadRequest) as e:
            create_schedule.post()
        assert e.value[1]['error'] == 'Information needed to schedule this job is missing.'

    def test_created_schedule_with_jt_with_survey_with_defaults(self, factories):
        jt = factories.v2_job_template()
        survey = [dict(required=False,
                       question_name='Q1',
                       variable='var1',
                       type='password',
                       default='survey'),
                  dict(required=False,
                       question_name='Q2',
                       variable='var2',
                       type='text',
                       default='survey')]
        jt.add_survey(spec=survey)

        job = jt.launch().wait_until_completed()
        assert job.is_successful

        create_schedule = job.related.create_schedule.get()
        assert create_schedule.prompts == {}
        assert create_schedule.can_schedule

        schedule = create_schedule.post()
        assert schedule.extra_data == {}

    @pytest.mark.parametrize('required', [True, False])
    def test_created_schedule_with_jt_with_survey_with_defaults_when_answers_supplied(self, factories, required):
        jt = factories.v2_job_template()
        survey = [dict(required=required,
                       question_name='Q1',
                       variable='var1',
                       type='password',
                       default='survey'),
                  dict(required=required,
                       question_name='Q2',
                       variable='var2',
                       type='text',
                       default='survey')]
        jt.add_survey(spec=survey)

        payload = dict(extra_vars=dict(var1='launch', var2='launch', nonsurvey_var='ignore me'))
        job = jt.launch(payload).wait_until_completed()
        assert job.is_successful

        create_schedule = job.related.create_schedule.get()
        assert create_schedule.prompts == dict(extra_vars=dict(var1='$encrypted$', var2='launch'))
        assert create_schedule.can_schedule

        schedule = create_schedule.post()
        assert schedule.extra_data == dict(var1='$encrypted$', var2='launch')

    def test_created_schedule_from_wfj_with_default_jt(self, factories):
        wfjt = factories.v2_workflow_job_template()
        jt = factories.v2_job_template()
        factories.v2_workflow_job_template_node(workflow_job_template=wfjt, unified_job_template=jt)

        wfj = wfjt.launch().wait_until_completed()
        job = jt.get().related.last_job.get()
        assert wfj.is_successful
        assert job.is_successful

        create_schedule = job.related.create_schedule.get()
        assert create_schedule.prompts == {}
        assert create_schedule.can_schedule

        schedule = create_schedule.post()
        assert schedule.name == 'Auto-generated schedule from job {}'.format(job.id)
        assert schedule.description == ''
        assert schedule.unified_job_template == jt.id
        assert not schedule.enabled

        assert not schedule.diff_mode
        assert schedule.extra_data == {}
        assert not schedule.limit
        assert not schedule.job_tags
        assert not schedule.skip_tags
        assert not schedule.job_type
        assert not schedule.verbosity
        assert not schedule.inventory
        assert schedule.related.credentials.get().count == 0

        rrule_dtstart = utils.to_str(schedule.dtstart).translate(None, '-:')
        assert schedule.rrule == "DTSTART:{0} RRULE:FREQ=MONTHLY;INTERVAL=1".format(rrule_dtstart)
        assert not schedule.dtend

    def test_created_schedule_from_wfj_with_ask_jt(self, factories):
        inventory = factories.v2_inventory()
        credential = factories.v2_credential()

        wfjt = factories.v2_workflow_job_template()
        jt = factories.v2_job_template(**self.ask_jt_attrs)
        factories.v2_workflow_job_template_node(workflow_job_template=wfjt, unified_job_template=jt,
                                                extra_data=dict(var1='wfjtn'), job_type='check', job_tags='wfjtn',
                                                skip_tags='wfjtn', limit='wfjtn', diff_mode=True, verbosity=2,
                                                inventory=inventory, credential=credential)

        wfj = wfjt.launch().wait_until_completed()
        job = jt.get().related.last_job.get()
        assert wfj.is_successful
        assert job.is_successful

        create_schedule = job.related.create_schedule.get()
        prompts = create_schedule.prompts
        assert prompts.inventory.id == inventory.id
        assert len(prompts.credentials) == 1
        assert prompts.credentials.pop().id == credential.id
        assert prompts.diff_mode
        assert prompts.extra_vars == dict(var1='wfjtn')
        assert prompts.job_tags == 'wfjtn'
        assert prompts.job_type == 'check'
        assert prompts.limit == 'wfjtn'
        assert prompts.skip_tags == 'wfjtn'
        assert prompts.verbosity == 2
        assert create_schedule.can_schedule

        schedule = create_schedule.post()
        assert schedule.name == 'Auto-generated schedule from job {}'.format(job.id)
        assert schedule.description == ''
        assert schedule.unified_job_template == jt.id
        assert not schedule.enabled

        assert schedule.diff_mode
        assert schedule.extra_data == dict(var1='wfjtn')
        assert schedule.limit == 'wfjtn'
        assert schedule.job_tags == 'wfjtn'
        assert schedule.skip_tags == 'wfjtn'
        assert schedule.job_type == 'check'
        assert schedule.verbosity == 2
        assert schedule.inventory == inventory.id
        schedule_creds = schedule.related.credentials.get()
        assert schedule_creds.count == 1
        assert schedule_creds.results.pop().id == credential.id

        rrule_dtstart = utils.to_str(schedule.dtstart).translate(None, '-:')
        assert schedule.rrule == "DTSTART:{0} RRULE:FREQ=MONTHLY;INTERVAL=1".format(rrule_dtstart)
        assert not schedule.dtend

    def test_created_schedule_from_wfj_with_ask_jt_when_jt_defaults_supplied(self, factories):
        wfjt = factories.v2_workflow_job_template()
        jt = factories.v2_job_template(**self.ask_jt_attrs)
        factories.v2_workflow_job_template_node(workflow_job_template=wfjt, unified_job_template=jt,
                                                extra_data=jt.extra_vars, job_type=jt.job_type, job_tags=jt.job_tags,
                                                skip_tags=jt.skip_tags, limit=jt.limit, diff_mode=jt.diff_mode,
                                                verbosity=jt.verbosity, inventory=jt.ds.inventory, credential=jt.ds.credential)

        wfj = wfjt.launch().wait_until_completed()
        job = jt.get().related.last_job.get()
        assert wfj.is_successful
        assert job.is_successful

        create_schedule = job.related.create_schedule.get()
        assert create_schedule.prompts == {}
        assert create_schedule.can_schedule

        schedule = create_schedule.post()
        assert schedule.name == 'Auto-generated schedule from job {}'.format(job.id)
        assert schedule.description == ''
        assert schedule.unified_job_template == jt.id
        assert not schedule.enabled

        assert not schedule.diff_mode
        assert schedule.extra_data == {}
        assert not schedule.limit
        assert not schedule.job_tags
        assert not schedule.skip_tags
        assert not schedule.job_type
        assert not schedule.verbosity
        assert not schedule.inventory
        assert schedule.related.credentials.get().count == 0

        rrule_dtstart = utils.to_str(schedule.dtstart).translate(None, '-:')
        assert schedule.rrule == "DTSTART:{0} RRULE:FREQ=MONTHLY;INTERVAL=1".format(rrule_dtstart)
        assert not schedule.dtend

    @pytest.mark.parametrize('required', [True, False])
    def test_created_schedule_from_wfj_with_variables_on_launch_and_surveys(self, factories, required):
        wfjt = factories.v2_workflow_job_template(ask_variables_on_launch=True)
        jt = factories.v2_job_template()
        factories.v2_workflow_job_template_node(workflow_job_template=wfjt, unified_job_template=jt)

        wfjt_survey = [dict(required=required,
                            question_name='Q1',
                            variable='var1',
                            type='text',
                            default='wfjt_survey'),
                       dict(required=required,
                            question_name='Q2',
                            variable='var2',
                            type='password',
                            default='wfjt_survey')]
        wfjt.add_survey(spec=wfjt_survey)

        jt_survey = copy.deepcopy(wfjt_survey)
        jt_survey[0]['default'] = 'jt_survey'
        jt_survey[1]['default'] = 'jt_survey'
        jt.add_survey(jt_survey)

        payload = dict(extra_vars=dict(var1='launch', var2='$encrypted$', var3='launch'))
        wfj = wfjt.launch(payload).wait_until_completed()
        job = jt.get().related.last_job.get()
        assert wfj.is_successful
        assert job.is_successful

        create_schedule = job.related.create_schedule.get()
        assert create_schedule.prompts == dict(extra_vars=dict(var1='launch', var2='$encrypted$', var3='launch'))
        assert create_schedule.can_schedule

        schedule = create_schedule.post()
        assert schedule.extra_data == dict(var1='launch', var2='$encrypted$', var3='launch')

    def test_launch_credentials_override_default_wfjn_credentials(self, factories):
        jt_vault, launch_vault = [factories.v2_credential(kind='vault', inputs=dict(vault_password='fake')) for _ in range(2)]
        jt_aws, jt_vmware = [factories.v2_credential(kind=kind) for kind in ('aws', 'vmware')]
        launch_aws, launch_vmware = [factories.v2_credential(kind=kind) for kind in ('aws', 'vmware')]
        launch_ssh = factories.v2_credential()
        launch_creds = [launch_ssh, launch_aws, launch_vmware, launch_vault]
        launch_cred_ids = [cred.id for cred in launch_creds]

        wfjt = factories.v2_workflow_job_template()
        jt = factories.v2_job_template(vault_credential=jt_vault.id, ask_credential_on_launch=True)
        for cred in (jt_aws, jt_vmware):
            with utils.suppress(exc.NoContent):
                jt.related.extra_credentials.post(dict(id=cred.id))
        wfn = factories.v2_workflow_job_template_node(workflow_job_template=wfjt, unified_job_template=jt,
                                                      credential=launch_ssh)
        for cred in (launch_aws, launch_vmware, launch_vault):
            with utils.suppress(exc.NoContent):
                wfn.related.credentials.post(dict(id=cred.id))

        wfj = wfjt.launch().wait_until_completed()
        job = jt.get().related.last_job.get()
        assert wfj.is_successful
        assert job.is_successful

        create_schedule = job.related.create_schedule.get()
        assert len(create_schedule.prompts.credentials) == 4
        for cred in create_schedule.prompts.credentials:
            assert cred.id in launch_cred_ids
        assert create_schedule.can_schedule

        schedule = create_schedule.post()
        schedule_creds = schedule.related.credentials.get()
        assert schedule_creds.count == 4
        for cred in schedule_creds.results:
            assert cred.id in launch_cred_ids

    @pytest.mark.github('https://github.com/ansible/ansible-tower/issues/7848')
    def test_workflow_node_creation_rejected_when_source_jt_has_ask_disabled(self, factories):
        inventory = factories.v2_inventory()
        credential = factories.v2_credential()

        wfjt = factories.v2_workflow_job_template()
        jt = factories.v2_job_template()

        with pytest.raises(exc.BadRequest) as e:
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
        with pytest.raises(exc.BadRequest) as e:
            factories.v2_workflow_job_template_node(workflow_job_template=wfjt, unified_job_template=jt)
        assert e.value[1] == {'passwords_needed_to_start':
                             ['Saved launch configurations cannot provide passwords needed to start.']}

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
                dict(required=False, question_name="Text-passed default with conflicting minimum and maximum.",
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
                dict(required=False, question_name="Password-passed default with conflicting minimum and maximum.",
                     variable='test_var_twelve', type='password', min=4, max=4, default='asdfasdf')]
        jt.add_survey(spec=spec)

        with pytest.raises(exc.BadRequest) as e:
            factories.v2_workflow_job_template_node(workflow_job_template=wfjt, unified_job_template=jt,
                extra_data=dict(test_var_one='', test_var_two='four', test_var_three='abc',
                                test_var_four='1', test_var_five='four', test_var_six='asdfasdf',
                                test_var_seven='$encrypted$', test_var_eight='$encrypted$',
                                test_var_nine='$encrypted$', test_var_ten='$encrypted$',
                                test_var_eleven='$encrypted$', test_var_twelve='$encrypted$'))
        # assert e.value[1] == ???

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

    @pytest.mark.github('https://github.com/ansible/ansible-tower/issues/7866')
    def test_cannot_create_schedule_from_job_with_missing_jt_dependency(self, factories):
        jt = factories.v2_job_template()
        job = jt.launch().wait_until_completed()

        jt.ds.inventory.delete().wait_until_deleted()

        create_schedule = job.related.create_schedule.get()
        assert create_schedule.prompts == dict()
        assert not create_schedule.can_schedule

        with pytest.raises(exc.BadRequest) as e:
            create_schedule.post()

    def test_cannot_create_schedule_from_job_with_missing_ask_jt_dependency(self, factories):
        inv = factories.v2_inventory()
        jt = factories.v2_job_template(inventory=None, ask_inventory_on_launch=True)
        job = jt.launch(dict(inventory=inv.id)).wait_until_completed()

        inv.delete().wait_until_deleted()

        create_schedule = job.related.create_schedule.get()
        assert create_schedule.prompts == dict()
        assert not create_schedule.can_schedule

        with pytest.raises(exc.BadRequest):
            create_schedule.post()
