import copy

from awxkit import utils
from awxkit import exceptions as exc
import pytest

from tests.api import APITest


@pytest.mark.usefixtures('authtoken')
class TestPrompts(APITest):

    ask_jt_attrs = dict(ask_diff_mode_on_launch=True, ask_variables_on_launch=True,
                        ask_limit_on_launch=True, ask_tags_on_launch=True,
                        ask_skip_tags_on_launch=True, ask_job_type_on_launch=True,
                        ask_verbosity_on_launch=True, ask_inventory_on_launch=True,
                        ask_credential_on_launch=True)

    def format_dtstart(self, schedule):
        return str(schedule.dtstart).translate(str.maketrans('', '', '-:'))

    def test_created_schedule_with_default_jt(self, factories):
        jt = factories.job_template()
        job = jt.launch().wait_until_completed()
        job.assert_successful()

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

        assert schedule.rrule == "DTSTART:{0} RRULE:FREQ=MONTHLY;INTERVAL=1".format(self.format_dtstart(schedule))
        assert not schedule.dtend

    def test_created_schedule_with_ask_jt_and_launch_values(self, factories):
        jt = factories.job_template(**self.ask_jt_attrs)
        job = jt.launch(dict(diff_mode=True, extra_vars=dict(var1='launch'), limit='launch', job_tags='launch',
                             skip_tags='launch', job_type='check', verbosity=5, inventory=jt.ds.inventory.id,
                             credentials=[jt.ds.credential.id])).wait_until_completed()
        job.assert_successful()

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

        assert schedule.rrule == "DTSTART:{0} RRULE:FREQ=MONTHLY;INTERVAL=1".format(self.format_dtstart(schedule))
        assert not schedule.dtend

    def test_created_schedule_with_ask_jt_when_jt_defaults_supplied(self, factories):
        jt = factories.job_template(**self.ask_jt_attrs)
        job = jt.launch(dict(diff_mode=jt.diff_mode, extra_vars=jt.extra_vars, limit=jt.limit, job_tags=jt.job_tags,
                             skip_tags=jt.skip_tags, job_type=jt.job_type, verbosity=jt.verbosity,
                             inventory=jt.ds.inventory.id, credentials=[jt.ds.credential.id])).wait_until_completed()
        job.assert_successful()

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

        assert schedule.rrule == "DTSTART:{0} RRULE:FREQ=MONTHLY;INTERVAL=1".format(self.format_dtstart(schedule))
        assert not schedule.dtend

    def test_created_schedule_with_ask_inventory_and_credential_and_launch_resources(self, factories):
        inventory = factories.inventory()
        ssh_cred, aws_cred = [factories.credential(kind=kind) for kind in ('ssh', 'aws')]
        vault_cred = factories.credential(kind='vault', inputs=dict(vault_password='fake'))
        credentials = [ssh_cred, aws_cred, vault_cred]
        cred_ids = [cred.id for cred in credentials]

        jt = factories.job_template(ask_inventory_on_launch=True, ask_credential_on_launch=True)
        job = jt.launch(dict(inventory=inventory.id, credentials=cred_ids)).wait_until_completed()
        job.assert_successful()

        create_schedule = job.related.create_schedule.get()
        assert create_schedule.prompts.inventory.id == inventory.id
        assert set([cred.id for cred in create_schedule.prompts.credentials]) == set(cred_ids)
        assert create_schedule.can_schedule

        schedule = create_schedule.post()
        assert schedule.inventory == inventory.id
        schedule_creds = schedule.related.credentials.get()
        assert schedule_creds.count == 3
        for cred in schedule_creds.results:
            assert cred.id in cred_ids

    def test_launch_credentials_override_default_jt_credentials(self, factories):
        jt_vault, launch_vault = [factories.credential(kind='vault', inputs=dict(vault_password='fake')) for _ in range(2)]
        jt_aws, jt_vmware = [factories.credential(kind=kind) for kind in ('aws', 'vmware')]
        launch_aws, launch_vmware = [factories.credential(kind=kind) for kind in ('aws', 'vmware')]

        jt = factories.job_template(vault_credential=jt_vault.id, ask_credential_on_launch=True)
        for cred in (jt_aws, jt_vmware):
            jt.add_extra_credential(cred)

        launch_ssh = factories.credential()
        launch_creds = [launch_ssh, launch_aws, launch_vmware, launch_vault]
        launch_cred_ids = [cred.id for cred in launch_creds]
        job = jt.launch(dict(credentials=launch_cred_ids)).wait_until_completed()
        job.assert_successful()

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

    def test_cannot_create_schedule_with_jt_with_ask_credential(self, factories):
        cred = factories.credential(ssh_key_data=self.credentials.ssh.encrypted.ssh_key_data, password='ASK',
                                       become_password='ASK', ssh_key_unlock='ASK')
        jt = factories.job_template(credential=cred)

        payload = dict(credential_passwords=dict(ssh_password='fake', become_password='fake',
                                                 ssh_key_unlock=self.credentials.ssh.encrypted.ssh_key_unlock))
        job = jt.launch(payload).wait_until_completed()
        job.assert_successful()

        create_schedule = job.related.create_schedule.get()
        assert create_schedule.prompts == {}
        assert not create_schedule.can_schedule

        with pytest.raises(exc.BadRequest) as e:
            create_schedule.post()
        assert e.value[1]['error'] == 'Cannot create schedule because job requires credential passwords.'

    def test_created_schedule_with_jt_with_survey_with_defaults(self, factories):
        jt = factories.job_template()
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
        job.assert_successful()

        create_schedule = job.related.create_schedule.get()
        assert create_schedule.prompts == {}
        assert create_schedule.can_schedule

        schedule = create_schedule.post()
        assert schedule.extra_data == {}

    @pytest.mark.parametrize('required', [True, False])
    def test_created_schedule_with_jt_with_survey_with_defaults_when_answers_supplied(self, factories, required):
        jt = factories.job_template()
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
        job.assert_successful()

        create_schedule = job.related.create_schedule.get()
        assert create_schedule.prompts == dict(extra_vars=dict(var1='$encrypted$', var2='launch'))
        assert create_schedule.can_schedule

        schedule = create_schedule.post()
        assert schedule.extra_data == dict(var1='$encrypted$', var2='launch')

    def test_created_schedule_from_wfj_with_default_jt(self, factories):
        wfjt = factories.workflow_job_template()
        jt = factories.job_template()
        factories.workflow_job_template_node(workflow_job_template=wfjt, unified_job_template=jt)

        wfj = wfjt.launch().wait_until_completed()
        job = jt.get().related.last_job.get()
        wfj.assert_successful()
        job.assert_successful()

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

        assert schedule.rrule == "DTSTART:{0} RRULE:FREQ=MONTHLY;INTERVAL=1".format(self.format_dtstart(schedule))
        assert not schedule.dtend

    @pytest.mark.yolo
    def test_created_schedule_from_wfj_with_ask_jt(self, factories):
        inventory = factories.inventory()
        credential = factories.credential()

        wfjt = factories.workflow_job_template()
        jt = factories.job_template(**self.ask_jt_attrs)
        node = factories.workflow_job_template_node(workflow_job_template=wfjt, unified_job_template=jt,
                                                    extra_data=dict(var1='wfjtn'), job_type='check', job_tags='wfjtn',
                                                    skip_tags='wfjtn', limit='wfjtn', diff_mode=True, verbosity=2,
                                                    inventory=inventory)

        node.add_credential(credential)
        wfj = wfjt.launch().wait_until_completed()
        job = jt.get().related.last_job.get()
        wfj.assert_successful()
        job.assert_successful()

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

        assert schedule.rrule == "DTSTART:{0} RRULE:FREQ=MONTHLY;INTERVAL=1".format(self.format_dtstart(schedule))
        assert not schedule.dtend

    def test_created_schedule_from_wfj_with_ask_jt_when_jt_defaults_supplied(self, factories):
        wfjt = factories.workflow_job_template()
        jt = factories.job_template(**self.ask_jt_attrs)
        factories.workflow_job_template_node(workflow_job_template=wfjt, unified_job_template=jt,
                                                extra_data=jt.extra_vars, job_type=jt.job_type, job_tags=jt.job_tags,
                                                skip_tags=jt.skip_tags, limit=jt.limit, diff_mode=jt.diff_mode,
                                                verbosity=jt.verbosity, inventory=jt.ds.inventory, credential=jt.ds.credential)

        wfj = wfjt.launch().wait_until_completed()
        job = jt.get().related.last_job.get()
        wfj.assert_successful()
        job.assert_successful()

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

        assert schedule.rrule == "DTSTART:{0} RRULE:FREQ=MONTHLY;INTERVAL=1".format(self.format_dtstart(schedule))
        assert not schedule.dtend

    @pytest.mark.parametrize('required', [True, False])
    def test_created_schedule_from_wfj_with_variables_on_launch_and_surveys(self, factories, required):
        wfjt = factories.workflow_job_template(ask_variables_on_launch=True)
        jt = factories.job_template()
        factories.workflow_job_template_node(workflow_job_template=wfjt, unified_job_template=jt)

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
        jt.add_survey(spec=jt_survey)

        payload = dict(extra_vars=dict(var1='launch', var2='$encrypted$', var3='launch'))
        wfj = wfjt.launch(payload).wait_until_completed()
        job = jt.get().related.last_job.get()
        wfj.assert_successful()
        job.assert_successful()

        create_schedule = job.related.create_schedule.get()
        assert create_schedule.prompts == dict(extra_vars=dict(var1='launch', var2='$encrypted$', var3='launch'))
        assert create_schedule.can_schedule

        schedule = create_schedule.post()
        assert schedule.extra_data == dict(var1='launch', var2='$encrypted$', var3='launch')

    @pytest.mark.yolo
    def test_launch_credentials_override_default_wfjn_credentials(self, factories):
        jt_vault, launch_vault = [factories.credential(kind='vault', inputs=dict(vault_password='fake')) for _ in range(2)]
        jt_aws, jt_vmware = [factories.credential(kind=kind) for kind in ('aws', 'vmware')]
        launch_aws, launch_vmware = [factories.credential(kind=kind) for kind in ('aws', 'vmware')]
        launch_ssh = factories.credential()
        launch_creds = [launch_ssh, launch_aws, launch_vmware, launch_vault]
        launch_cred_ids = [cred.id for cred in launch_creds]

        wfjt = factories.workflow_job_template()
        jt = factories.job_template(vault_credential=jt_vault.id, ask_credential_on_launch=True)
        for cred in (jt_aws, jt_vmware):
            jt.add_extra_credential(cred)
        wfjtn = factories.workflow_job_template_node(workflow_job_template=wfjt, unified_job_template=jt)
        wfjtn.add_credential(launch_ssh)
        for cred in (launch_aws, launch_vmware, launch_vault):
            with utils.suppress(exc.NoContent):
                wfjtn.related.credentials.post(dict(id=cred.id))

        wfj = wfjt.launch().wait_until_completed()
        job = jt.get().related.last_job.get()
        wfj.assert_successful()
        job.assert_successful()

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

    def test_cannot_create_schedule_from_job_with_missing_jt_dependency(self, factories):
        jt = factories.job_template()
        job = jt.launch().wait_until_completed()

        jt.ds.inventory.delete().wait_until_deleted()

        create_schedule = job.related.create_schedule.get()
        assert create_schedule.prompts == dict()
        assert not create_schedule.can_schedule

        with pytest.raises(exc.BadRequest) as e:
            create_schedule.post()
        assert e.value[1]['error'] == 'Cannot create schedule because a related resource is missing.'

    def test_cannot_create_schedule_from_job_with_missing_ask_jt_dependency(self, factories):
        inv = factories.inventory()
        jt = factories.job_template(inventory=None, ask_inventory_on_launch=True)
        job = jt.launch(dict(inventory=inv.id)).wait_until_completed()

        inv.delete().wait_until_deleted()

        create_schedule = job.related.create_schedule.get()
        assert create_schedule.prompts == dict()
        assert not create_schedule.can_schedule

        with pytest.raises(exc.BadRequest):
            create_schedule.post()
