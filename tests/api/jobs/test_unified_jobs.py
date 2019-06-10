import json

from towerkit import exceptions as exc
import fauxfactory
from towerkit.api import Connection
import pytest

from tests.api import APITest


@pytest.mark.api
@pytest.mark.usefixtures('authtoken', 'install_enterprise_license_unlimited')
class TestUnifiedJobs(APITest):

    @pytest.mark.parametrize('fixture, method', [('job_template_plain', 'launch'),
                                                 ('workflow_job_template', 'launch'),
                                                 ('ad_hoc_command', None),
                                                 ('project', 'update'),
                                                 ('custom_inventory_source', 'update'),
                                                 ('cleanup_jobs_template', 'launch')],
                             ids=['job', 'workflow job', 'ad hoc command', 'project_update',
                                  'inventory_update', 'system job'])
    def test_delete_running_unified_job_forbidden(self, request, factories, fixture, method):
        if method:
            resource = request.getfixturevalue(fixture)
            if fixture == 'workflow_job_template':
                # Workflow jobs run too fast for this test to reliably work while empty
                factories.workflow_job_template_node(
                    workflow_job_template=resource,
                    unified_job_template=factories.job_template()
                )
            uj = getattr(resource, method)()
        else:
            uj = request.getfixturevalue(fixture)

        with pytest.raises(exc.Forbidden) as e:
            uj.delete()
        assert e.value[1]['detail'] == 'Cannot delete running job resource.'

        uj.wait_until_completed().assert_successful()

    @pytest.mark.parametrize('template', ['job', 'workflow_job'])
    def test_confirm_survey_password_defaults_censored_in_unified_job_extra_vars(self, factories, template):
        resource = getattr(factories, template + '_template')()
        password = "don't expose me - {0}".format(fauxfactory.gen_utf8(3).encode('utf8'))
        survey = [dict(required=False,
                       question_name='Test',
                       variable='var',
                       type='password',
                       default=password)]
        resource.add_survey(spec=survey)

        uj = resource.launch().wait_until_completed()
        uj.assert_successful()
        assert uj.extra_vars == json.dumps(dict(var="$encrypted$"))

        relaunched_uj = uj.relaunch().wait_until_completed()
        relaunched_uj.assert_successful()
        assert relaunched_uj.extra_vars == json.dumps(dict(var="$encrypted$"))

    uj_with_stdout = ['job_template_plain',
                      'adhoc',
                      'inventory_source',
                      'project']

    @pytest.mark.parametrize('jobtype', uj_with_stdout)
    def test_job_stdout_can_be_downloaded(self, jobtype, factories, request):
        if jobtype == 'job_template_plain':
            job = factories.job_template().launch().wait_until_completed()
        if jobtype == 'adhoc':
            job = factories.ad_hoc_command().wait_until_completed()
        if jobtype == 'inventory_source':
            job = factories.inventory_source().update().wait_until_completed()
        if jobtype == 'project':
            job = factories.project().update().wait_until_completed()

        connection = Connection(self.connections['root'].server)
        connection.login(self.credentials.default['username'],
                         self.credentials.default['password'])
        stdout = connection.get(job.get().related.stdout,
                                query_parameters='format=txt_download')
        assert 'attachment; filename' in stdout.headers['Content-Disposition']
        assert len(stdout.content) > 0
