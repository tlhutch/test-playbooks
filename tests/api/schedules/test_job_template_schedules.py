import json

from awxkit import utils
from awxkit import exceptions as exc
import pytest

from tests.api.schedules import SchedulesTest


@pytest.mark.usefixtures('authtoken')
class TestJobTemplateSchedules(SchedulesTest):

    select_jt_fields = ('inventory', 'project', 'playbook', 'job_type')
    promptable_fields = ('inventory', 'job_type', 'job_tags', 'skip_tags', 'verbosity',
                         'diff_mode', 'limit')

    def ask_everything(self, setup=False, inventory=None, config=False):
        r = {}
        # names for promptable fields and a non-default value
        prompts = [
                ('variables', {'var1': 'bar'}),
                ('diff_mode', True),
                ('limit', 'test_limit'),
                ('tags', 'test_tag'),
                ('skip_tags', 'test_skip_tag'),
                ('job_type', 'check'),
                ('verbosity', 5),
                ('inventory', inventory.id if inventory else None)
        ]
        for fd, val in prompts:
            if setup:
                r['ask_{}_on_launch'.format(fd)] = True
            else:
                job_fd = fd
                if fd == 'tags':
                    job_fd = 'job_tags'
                if fd == 'variables':
                    if config:
                        job_fd = 'extra_data'
                    else:
                        job_fd = 'extra_vars'
                r[job_fd] = val
        return r

    def test_schedule_uses_prompted_fields(self, factories):
        jt = factories.job_template(**self.ask_everything(setup=True))
        inventory = factories.inventory()
        schedule = jt.add_schedule(rrule=self.minutely_rrule(),
            **self.ask_everything(inventory=inventory, config=True))

        bad_params = []
        for fd, val in self.ask_everything(inventory=inventory, config=True).items():
            if getattr(schedule, fd) != val:
                bad_params.append((fd, val, getattr(schedule, fd)))
        assert not bad_params, 'Schedule parameters {} were not enabled.'.format(bad_params)

    def test_schedule_creation_rejected_when_jt_ask_disabled(self, factories, inventory):
        jt = factories.job_template()
        mrrule = self.minutely_rrule()
        schedule_prompts = self.ask_everything(inventory=inventory, config=True)
        for key, value in schedule_prompts.items():
            data = {}
            data[key] = value
            with pytest.raises(exc.BadRequest) as e:
                jt.add_schedule(rrule=mrrule, **data)
            msg = 'Field is not configured to prompt on launch.'
            if key == 'extra_data':
                msg = ('Variables {} are not allowed on launch. Check the Prompt '
                       'on Launch setting on the Job Template to include Extra Variables.'.format(
                            list(schedule_prompts['extra_data'].keys())[0]))
            assert e.value[1] == {key: [msg]}

    def test_schedule_creation_rejected_when_jt_ask_credential_disabled(self, factories):
        jt = factories.job_template()
        mrrule = self.minutely_rrule()
        schedule = jt.add_schedule(rrule=mrrule)
        credential = factories.credential()

        with pytest.raises(exc.BadRequest) as e:
            schedule.add_credential(credential)
        assert e.value[1] == {'msg': 'Related template is not configured to accept credentials on launch.'}

    def test_schedule_jobs_should_source_from_underlying_template(self, factories):
        jt = factories.job_template()
        factories.host(inventory=jt.ds.inventory)

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
        jt.add_survey(spec=survey)
        schedule = jt.add_schedule(rrule=self.minutely_rrule())

        unified_jobs = schedule.related.unified_jobs.get()
        utils.poll_until(lambda: unified_jobs.get().count == 1, timeout=1.5 * 60)
        job = unified_jobs.results.pop()
        job.wait_until_completed().assert_successful()
        assert json.loads(job.extra_vars) == {'var1': 'survey', 'var2': '$encrypted$'}

        for field in self.select_jt_fields:
            assert getattr(jt, field) == getattr(job, field)
        for field in self.promptable_fields:
            assert getattr(jt, field) == getattr(job, field)
        job_creds = [cred.id for cred in job.related.credentials.get().results]
        jt_creds = [cred.id for cred in jt.related.credentials.get().results]
        assert sorted(job_creds) == sorted(jt_creds)

    def test_schedule_values_take_precedence_over_jt_values(self, factories, ask_everything_jt):
        host = factories.host()

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
        ask_everything_jt.add_survey(spec=survey)
        payload = dict(rrule=self.minutely_rrule(), inventory=host.ds.inventory.id, job_type='check',
                       job_tags='always', skip_tags='unmatched', limit='all', diff_mode=True, verbosity=5,
                       extra_data={'var1': 'schedule', 'var2': 'schedule'})
        schedule = ask_everything_jt.add_schedule(**payload)

        creds = [factories.credential(kind=kind) for kind in ('ssh', 'aws')]
        creds.append(factories.credential(kind='vault', inputs={'vault_password': 'fake'}))
        for cred in creds:
            schedule.add_credential(cred)

        unified_jobs = schedule.related.unified_jobs.get()
        utils.poll_until(lambda: unified_jobs.get().count == 1, timeout=1.5 * 60)
        job = unified_jobs.results.pop()
        job.wait_until_completed().assert_successful()
        assert json.loads(job.extra_vars) == {'var1': 'schedule', 'var2': '$encrypted$'}

        fields = [field for field in payload if field not in ('extra_data', 'rrule')]
        for field in fields:
            assert payload[field] == getattr(job, field)
        job_cred_ids = [cred.id for cred in job.related.credentials.get().results]
        assert set(cred.id for cred in creds) == set(job_cred_ids)

    @pytest.mark.parametrize('ujt_type', ['job_template', 'workflow_job_template'])
    def test_cannot_create_schedule_without_answering_required_survey_questions(self, factories, ujt_type):
        template = getattr(factories, ujt_type)()
        survey = [dict(required=True,
                       question_name='Q1',
                       variable='var1',
                       type='text',
                       default=''),
                  dict(required=True,
                       question_name='Q2',
                       variable='var2',
                       type='password',
                       default='')]
        template.add_survey(spec=survey)
        with pytest.raises(exc.BadRequest) as e:
            template.add_schedule(rrule=self.minutely_rrule())
        assert e.value[1] == e.value[1] == {'variables_needed_to_start': ["'var1' value missing", "'var2' value missing"]}

    @pytest.mark.parametrize('ujt_type', ['job_template', 'workflow_job_template'])
    def test_can_create_schedule_when_required_survey_questions_answered(self, factories, ujt_type):
        jt = factories.job_template(playbook='debug_extra_vars.yml')
        factories.host(inventory=jt.ds.inventory)

        survey = [dict(required=True,
                       question_name='Q1',
                       variable='var1',
                       type='text',
                       default=''),
                  dict(required=True,
                       question_name='Q2',
                       variable='var2',
                       type='password',
                       default='')]

        if ujt_type == 'job_template':
            survey_template = jt
        else:
            survey_template = factories.workflow_job_template()
            # jt needs survey applied so that it "prompts" for those variables
            jt.add_survey(spec=survey)
            factories.workflow_job_template_node(workflow_job_template=survey_template, unified_job_template=jt)

        survey_template.add_survey(spec=survey)
        schedule = survey_template.add_schedule(rrule=self.minutely_rrule(), extra_data={'var1': 'var1', 'var2': 'very_secret'})
        assert schedule.extra_data == {'var1': 'var1', 'var2': '$encrypted$'}

        unified_jobs = schedule.related.unified_jobs.get()
        utils.poll_until(lambda: unified_jobs.get().count == 1, interval=5, timeout=1.5 * 60)
        uj = unified_jobs.results.pop()
        uj.wait_until_completed().assert_successful()
        if ujt_type == 'workflow_job_template':
            job = uj.related.workflow_nodes.get().results.pop().related.job.get()
        else:
            job = uj
        assert json.loads(uj.extra_vars) == {'var1': 'var1', 'var2': '$encrypted$'}
        assert json.loads(job.extra_vars) == {'var1': 'var1', 'var2': '$encrypted$'}
        assert '"var1": "var1"' in job.result_stdout
        assert '"var2": "very_secret"' in job.result_stdout

    @pytest.mark.parametrize('ujt_type', ['job_template', 'workflow_job_template'])
    def test_can_create_schedule_when_optional_survey_questions_are_unanswered(self, factories, ujt_type):
        template = getattr(factories, ujt_type)()
        survey = [dict(required=False,
                       question_name='Q1',
                       variable='var1',
                       type='text',
                       default='var1'),
                  dict(required=False,
                       question_name='Q2',
                       variable='var2',
                       type='password',
                       default='var2')]
        template.add_survey(spec=survey)
        schedule = template.add_schedule(rrule=self.minutely_rrule())
        assert schedule.extra_data == {}

    @pytest.mark.parametrize('ujt_type', ['job_template', 'workflow_job_template'])
    def test_can_create_schedule_when_defaults_are_supplied_with_required_survey_questions_with_defaults(self, factories,
                                                                                                         ujt_type):
        template = getattr(factories, ujt_type)()
        survey = [dict(required=True,
                       question_name='Q1',
                       variable='var1',
                       type='text',
                       default='var1'),
                  dict(required=True,
                       question_name='Q2',
                       variable='var2',
                       type='password',
                       default='very_secret')]
        template.add_survey(spec=survey)
        schedule = template.add_schedule(rrule=self.minutely_rrule(), extra_data={'var1': 'var1', 'var2': '$encrypted$'})
        assert schedule.extra_data == {'var1': 'var1'}

    def test_schedule_spawned_jobs_source_survey_defaults(self, factories):
        jt = factories.job_template(playbook='debug_extra_vars.yml')
        factories.host(inventory=jt.ds.inventory)

        survey = [dict(required=False,
                       question_name='Q1',
                       variable='var1',
                       type='text',
                       default='survey'),
                  dict(required=False,
                       question_name='Q2',
                       variable='var2',
                       type='password',
                       default='very_secret')]
        jt.add_survey(spec=survey)
        schedule = jt.add_schedule(rrule=self.minutely_rrule())
        assert not schedule.extra_data

        unified_jobs = schedule.related.unified_jobs.get()
        utils.poll_until(lambda: unified_jobs.get().count == 1, interval=5, timeout=1.5 * 60)
        job = unified_jobs.results.pop()
        job.wait_until_completed().assert_successful()
        assert json.loads(job.extra_vars) == {'var1': 'survey', 'var2': '$encrypted$'}
        assert '"var1": "survey"' in job.result_stdout
        assert '"var2": "very_secret"' in job.result_stdout

    def test_schedule_spawned_jobs_source_schedule_variables(self, factories):
        jt = factories.job_template(playbook='debug_extra_vars.yml', ask_variables_on_launch=True)
        factories.host(inventory=jt.ds.inventory)

        survey = [dict(required=False,
                       question_name='Q1',
                       variable='var1',
                       type='text',
                       default='survey'),
                  dict(required=False,
                       question_name='Q2',
                       variable='var2',
                       type='password',
                       default='very_secret')]
        jt.add_survey(spec=survey)
        schedule = jt.add_schedule(rrule=self.minutely_rrule(),
                                   extra_data={'var1': 'schedule', 'var2': '$encrypted$'})
        assert schedule.extra_data == {'var1': 'schedule'}

        unified_jobs = schedule.related.unified_jobs.get()
        utils.poll_until(lambda: unified_jobs.get().count == 1, interval=5, timeout=1.5 * 60)
        job = unified_jobs.results.pop()
        job.wait_until_completed().assert_successful()
        assert json.loads(job.extra_vars) == {'var1': 'schedule', 'var2': '$encrypted$'}
        assert '"var1": "schedule"' in job.result_stdout
        assert '"var2": "very_secret"' in job.result_stdout

    def test_schedule_spawned_jobs_source_updated_survey_defaults(self, factories):
        jt = factories.job_template(playbook='debug_extra_vars.yml')
        factories.host(inventory=jt.ds.inventory)

        survey = [dict(required=False,
                       question_name='Q1',
                       variable='var1',
                       type='text',
                       default='old_survey'),
                  dict(required=False,
                       question_name='Q2',
                       variable='var2',
                       type='password',
                       default='old_survey')]
        jt.add_survey(spec=survey)
        schedule = jt.add_schedule(rrule=self.minutely_rrule())
        assert not schedule.extra_data

        for question in survey:
            question['default'] = 'new_survey'
        jt.add_survey(spec=survey)

        unified_jobs = schedule.related.unified_jobs.get()
        utils.poll_until(lambda: unified_jobs.get().count == 1, interval=5, timeout=1.5 * 60)
        job = unified_jobs.results.pop()
        job.wait_until_completed().assert_successful()
        assert json.loads(job.extra_vars) == {'var1': 'new_survey', 'var2': '$encrypted$'}
        assert '"var1": "new_survey"' in job.result_stdout
        assert '"var2": "new_survey"' in job.result_stdout

    def test_schedule_spawned_jobs_source_updated_survey_and_schedule(self, factories):
        jt = factories.job_template(playbook='debug_extra_vars.yml', ask_variables_on_launch=True)
        factories.host(inventory=jt.ds.inventory)

        survey = [dict(required=False,
                       question_name='Q1',
                       variable='var1',
                       type='text',
                       default='old_survey'),
                  dict(required=False,
                       question_name='Q2',
                       variable='var2',
                       type='password',
                       default='old_survey')]
        jt.add_survey(spec=survey)
        schedule = jt.add_schedule(rrule=self.minutely_rrule(),
                                   extra_data={'var1': 'old_schedule', 'var2': '$encrypted$'})
        assert schedule.extra_data == {'var1': 'old_schedule'}

        for question in survey:
            question['default'] = 'new_survey'
        jt.add_survey(spec=survey)
        schedule.extra_data = {'var1': 'new_schedule', 'var2': 'new_schedule'}

        unified_jobs = schedule.related.unified_jobs.get()
        utils.poll_until(lambda: unified_jobs.get().count == 1, interval=5, timeout=1.5 * 60)
        job = unified_jobs.results.pop()
        job.wait_until_completed().assert_successful()
        assert json.loads(job.extra_vars) == {'var1': 'new_schedule', 'var2': '$encrypted$'}
        assert '"var1": "new_schedule"' in job.result_stdout
        assert '"var1": "new_schedule"' in job.result_stdout

    def test_plaintext_survey_defaults_get_encrypted_when_question_types_are_changed(self, factories):
        jt = factories.job_template(playbook='debug_extra_vars.yml', ask_variables_on_launch=True)
        factories.host(inventory=jt.ds.inventory)

        survey = [dict(required=False,
                       question_name='Q1',
                       variable='var1',
                       type='text',
                       default='survey')]
        jt.add_survey(spec=survey)
        schedule = jt.add_schedule(rrule=self.minutely_rrule())
        assert not schedule.extra_data

        survey[0]['type'] = 'password'
        jt.add_survey(spec=survey)

        unified_jobs = schedule.related.unified_jobs.get()
        utils.poll_until(lambda: unified_jobs.get().count == 1, interval=5, timeout=1.5 * 60)
        job = unified_jobs.results.pop()
        job.wait_until_completed().assert_successful()
        assert json.loads(job.extra_vars) == {'var1': '$encrypted$'}
        assert '"var1": "survey"' in job.result_stdout

    def test_scheduled_jobs_fail_with_deleted_inventory(self, factories):
        jt = factories.job_template()
        schedule = jt.add_schedule(rrule=self.minutely_rrule())
        jt.ds.inventory.delete().wait_until_deleted()

        jobs = schedule.related.unified_jobs.get()
        utils.poll_until(lambda: jobs.get().count == 1, interval=5, timeout=1.5 * 60)
        job = jobs.results.pop().wait_until_completed()

        assert job.failed
        assert job.job_explanation == "Job could not start because it does not have a valid inventory."

    @pytest.mark.serial
    def test_awx_metavars_for_scheduled_workflow_jobs(self, v2, factories, update_setting_pg):
        update_setting_pg(
            v2.settings.get().get_endpoint('jobs'),
            dict(ALLOW_JINJA_IN_EXTRA_VARS='always')
        )
        wfjt = factories.workflow_job_template()
        schedule = wfjt.add_schedule(rrule=self.minutely_rrule())
        jt = factories.job_template(playbook='debug_extra_vars.yml',
                                       extra_vars='var1: "{{ awx_parent_job_schedule_id }}"\nvar2: "{{ awx_parent_job_schedule_name }}"\nvar3: "{{ tower_parent_job_schedule_id }}"\nvar4: "{{ tower_parent_job_schedule_name }}"')
        factories.host(inventory=jt.ds.inventory)
        factories.workflow_job_template_node(workflow_job_template=wfjt, unified_job_template=jt)
        utils.poll_until(lambda: wfjt.related.workflow_jobs.get().count == 1, interval=5, timeout=1.5 * 60)
        wf_job = wfjt.related.workflow_jobs.get().results.pop()
        wf_job.wait_until_completed().assert_successful()
        # Get job in node
        wfjns = wf_job.related.workflow_nodes.get().results
        wfjn = wfjns.pop()
        job = wfjn.get_related('job')
        job.assert_successful()
        assert '"var1": "{}"'.format(schedule.id) in job.result_stdout
        assert '"var2": "{}"'.format(schedule.name) in job.result_stdout
        assert '"var1": "{}"'.format(schedule.id) in job.result_stdout
        assert '"var2": "{}"'.format(schedule.name) in job.result_stdout
