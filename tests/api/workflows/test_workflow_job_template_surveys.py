import pytest

from tests.api import Base_Api_Test


@pytest.mark.api
@pytest.mark.skip_selenium
@pytest.mark.usefixtures('authtoken', 'install_enterprise_license_unlimited')
class TestWorkflowJobTemplateSurveys(Base_Api_Test):
    @pytest.mark.github('https://github.com/ansible/ansible-tower/issues/7769')
    def test_wfjt_survey_password_defaults_passed_to_jobs(self, factories):
        host = factories.v2_host()
        wfjt = factories.v2_workflow_job_template()
        jt = factories.v2_job_template(inventory=host.ds.inventory, playbook='debug_extra_vars.yml')
        factories.v2_workflow_job_template_node(workflow_job_template=wfjt, unified_job_template=jt)

        survey = [dict(required=False,
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

        wfj1 = wfjt.launch().wait_until_completed()
        job1 = jt.get().related.last_job.get()
        assert wfj1.is_successful
        assert job1.is_successful
        assert '\"var1\": \"var1_default\"' in job1.result_stdout
        assert '\"var2\": \"var2_default\"' in job1.result_stdout

        wfj2 = wfj1.relaunch().wait_until_completed()
        job2 = jt.related.last_job.get()
        assert wfj2.is_successful
        assert job2.is_successful
        assert '\"var1\": \"var1_default\"' in job2.result_stdout
        assert '\"var2\": \"var2_default\"' in job2.result_stdout
