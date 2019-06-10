import pytest

from tests.api import APITest


@pytest.mark.api
@pytest.mark.mp_group('Jinja2', 'isolated_serial')
@pytest.mark.usefixtures('authtoken', 'install_enterprise_license_unlimited')
class TestJinja2(APITest):

    target_text = 'TARGET_TEXT'
    jinja2_text = '"var1": "{{ \'target_text\'|upper }}"'

    @pytest.mark.parametrize('allow_jinja', ['always', 'template', 'never'])
    def test_jt_with_jinja2_extra_vars(self, v2, factories, update_setting_pg, allow_jinja):
        jobs_settings = v2.settings.get().get_endpoint('jobs')
        payload = dict(ALLOW_JINJA_IN_EXTRA_VARS=allow_jinja)
        update_setting_pg(jobs_settings, payload)

        jt = factories.job_template(playbook='debug_extra_vars.yml',
                                       extra_vars="var1: \"{{ 'target_text'|upper }}\"")
        factories.host(inventory=jt.ds.inventory)

        job = jt.launch().wait_until_completed()
        job.assert_successful()

        if allow_jinja in ('always', 'template'):
            assert self.target_text in job.result_stdout
        else:
            assert self.jinja2_text in job.result_stdout

    @pytest.mark.parametrize('allow_jinja', ['always', 'template', 'never'])
    def test_jt_with_jinja2_launch_time_extra_vars(self, v2, factories, update_setting_pg, allow_jinja):
        jobs_settings = v2.settings.get().get_endpoint('jobs')
        payload = dict(ALLOW_JINJA_IN_EXTRA_VARS=allow_jinja)
        update_setting_pg(jobs_settings, payload)

        jt = factories.job_template(playbook='debug_extra_vars.yml', ask_variables_on_launch=True,
                                       extra_vars="var1: \"{{ 'target_text'|upper }}\"")
        factories.host(inventory=jt.ds.inventory)

        job = jt.launch(dict(extra_vars="var1: \"{{ 'target_text'|upper }}\"")).wait_until_completed()
        job.assert_successful()

        if allow_jinja in ('always', 'template'):
            assert self.target_text in job.result_stdout
        else:
            assert self.jinja2_text in job.result_stdout

    @pytest.mark.parametrize('allow_jinja', ['always', 'template', 'never'])
    def test_jt_with_sourced_jinja2_survey_default_extra_vars(self, v2, factories, update_setting_pg, allow_jinja):
        jobs_settings = v2.settings.get().get_endpoint('jobs')
        payload = dict(ALLOW_JINJA_IN_EXTRA_VARS=allow_jinja)
        update_setting_pg(jobs_settings, payload)

        survey = [dict(required=False,
                       question_name='Q1',
                       variable='var1',
                       type='text',
                       default="{{ 'target_text'|upper }}"),
                  dict(required=False,
                       question_name='Q2',
                       variable='var2',
                       type='password',
                       default="{{ 'target_text'|upper }}")]

        jt = factories.job_template(playbook='debug_extra_vars.yml', ask_variables_on_launch=True)
        jt.add_survey(spec=survey)
        factories.host(inventory=jt.ds.inventory)

        job = jt.launch().wait_until_completed()
        job.assert_successful()

        if allow_jinja == 'always':
            assert self.target_text in job.result_stdout
        else:
            assert self.jinja2_text in job.result_stdout

    @pytest.mark.parametrize('allow_jinja', ['always', 'template', 'never'])
    def test_jt_with_answered_jinja2_survey_extra_vars(self, v2, factories, update_setting_pg, allow_jinja):
        jobs_settings = v2.settings.get().get_endpoint('jobs')
        payload = dict(ALLOW_JINJA_IN_EXTRA_VARS=allow_jinja)
        update_setting_pg(jobs_settings, payload)

        survey = [dict(required=False,
                       question_name='Q1',
                       variable='var1',
                       type='text',
                       default="{{ 'target_text'|lower }}"),
                  dict(required=False,
                       question_name='Q2',
                       variable='var2',
                       type='password',
                       default="{{ 'target_text'|lower }}")]

        jt = factories.job_template(playbook='debug_extra_vars.yml', ask_variables_on_launch=True)
        jt.add_survey(spec=survey)
        factories.host(inventory=jt.ds.inventory)

        payload = dict(extra_vars=dict(var1="{{ 'target_text'|upper }}", var2="{{ 'target_text'|upper }}"))
        job = jt.launch(payload).wait_until_completed()
        job.assert_successful()

        if allow_jinja == 'always':
            assert self.target_text in job.result_stdout
        else:
            assert self.jinja2_text in job.result_stdout

    @pytest.mark.parametrize('allow_jinja', ['always', 'template', 'never'])
    def test_wfjt_with_jinja2_extra_vars(self, v2, factories, update_setting_pg, allow_jinja):
        jobs_settings = v2.settings.get().get_endpoint('jobs')
        payload = dict(ALLOW_JINJA_IN_EXTRA_VARS=allow_jinja)
        update_setting_pg(jobs_settings, payload)

        host = factories.host()
        wfjt = factories.workflow_job_template(extra_vars="var1: \"{{ 'target_text'|upper }}\"")
        jt = factories.job_template(inventory=host.ds.inventory, playbook='debug_extra_vars.yml')
        factories.workflow_job_template_node(workflow_job_template=wfjt, unified_job_template=jt)

        wfj = wfjt.launch().wait_until_completed()
        job = jt.get().related.last_job.get()
        wfj.assert_successful()
        job.assert_successful()

        if allow_jinja == 'always':
            assert self.target_text in job.result_stdout
        else:
            assert self.jinja2_text in job.result_stdout

    @pytest.mark.parametrize('allow_jinja', ['always', 'template', 'never'])
    def test_wfjt_with_jinja2_survey_extra_vars(self, v2, factories, update_setting_pg, allow_jinja):
        jobs_settings = v2.settings.get().get_endpoint('jobs')
        payload = dict(ALLOW_JINJA_IN_EXTRA_VARS=allow_jinja)
        update_setting_pg(jobs_settings, payload)

        host = factories.host()
        wfjt = factories.workflow_job_template(extra_vars="var1: \"{{ 'target_text'|upper }}\"")
        jt = factories.job_template(inventory=host.ds.inventory, playbook='debug_extra_vars.yml')
        factories.workflow_job_template_node(workflow_job_template=wfjt, unified_job_template=jt)

        survey = [dict(required=False,
                       question_name='Q1',
                       variable='var1',
                       type='text',
                       default="{{ 'target_text'|upper }}"),
                  dict(required=False,
                       question_name='Q2',
                       variable='var2',
                       type='password',
                       default="{{ 'target_text'|upper }}")]
        wfjt.add_survey(spec=survey)

        wfj = wfjt.launch().wait_until_completed()
        job = jt.get().related.last_job.get()
        wfj.assert_successful()
        job.assert_successful()

        if allow_jinja == 'always':
            assert self.target_text in job.result_stdout
        else:
            assert self.jinja2_text in job.result_stdout

    @pytest.mark.parametrize('allow_jinja', ['always', 'template', 'never'])
    def test_ahc_with_jinja2_module_args(self, v2, factories, update_setting_pg, allow_jinja):
        jobs_settings = v2.settings.get().get_endpoint('jobs')
        payload = dict(ALLOW_JINJA_IN_EXTRA_VARS=allow_jinja)
        update_setting_pg(jobs_settings, payload)

        host = factories.host()
        ahc = factories.ad_hoc_command(inventory=host.ds.inventory, module_name='shell',
                                          module_args="echo {{ 'target_text'|upper }}").wait_until_completed()

        if allow_jinja == 'always':
            ahc.assert_successful()
            assert self.target_text in ahc.result_stdout
        else:
            assert ahc.status == 'error'
            assert ahc.failed
            assert 'ValueError: Inline Jinja variables are not allowed.' in ahc.result_traceback

    def test_jt_with_jinja2_machine_credential_fails(self, v2, factories, update_setting_pg):
        jobs_settings = v2.settings.get().get_endpoint('jobs')
        payload = dict(ALLOW_JINJA_IN_EXTRA_VARS='always')
        update_setting_pg(jobs_settings, payload)

        cred = factories.credential(inputs=dict(username="{{ 'target_text'|upper }}",
                                                   become_username="{{ 'target_text'|upper }}",
                                                   password="{{ 'target_text'|upper }}",
                                                   become_password="{{ 'target_text'|upper }}"))
        jt = factories.job_template(credential=cred)
        factories.host(inventory=jt.ds.inventory)

        job = jt.launch().wait_until_completed()
        assert job.status == 'error'
        assert job.failed
        assert 'ValueError: Inline Jinja variables are not allowed.' in job.result_traceback
