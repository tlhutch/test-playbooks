import json

from towerkit import exceptions as exc
import fauxfactory
import pytest

from tests.api import Base_Api_Test


@pytest.mark.api
@pytest.mark.usefixtures('authtoken', 'install_enterprise_license_unlimited')
class TestUnifiedJobs(Base_Api_Test):

    @pytest.mark.parametrize('fixture, method', [('job_template', 'launch'),
                                                 ('workflow_job_template', 'launch'),
                                                 ('ad_hoc_command', None),
                                                 ('project', 'update'),
                                                 ('custom_inventory_source', 'update')],
                             ids=['job', 'workflow job', 'ad hoc command', 'project_update',
                                  'inventory_update', 'system job'])
    def test_delete_running_unified_job_forbidden(self, request, fixture, method):
        if method:
            resource = request.getfixturevalue(fixture)
            uj = getattr(resource, method)()
        else:
            uj = request.getfixturevalue(fixture)

        with pytest.raises(exc.Forbidden) as e:
            uj.delete()
        assert e.value[1]['detail'] == 'Cannot delete running job resource.'

        assert uj.wait_until_completed().is_successful

    @pytest.mark.parametrize('template', ['job', 'workflow_job'])
    def test_confirm_survey_password_defaults_censored_in_unified_job_extra_vars(self, factories, template):
        resource = getattr(factories, 'v2_' + template + '_template')()
        password = "don't expose me - {0}".format(fauxfactory.gen_utf8(3).encode('utf8'))
        survey = [dict(required=False,
                       question_name='Test',
                       variable='var',
                       type='password',
                       default=password)]
        resource.add_survey(spec=survey)

        uj = resource.launch().wait_until_completed()
        assert uj.is_successful
        assert uj.extra_vars == json.dumps(dict(var="$encrypted$"))

        relaunched_uj = uj.relaunch().wait_until_completed()
        assert relaunched_uj.is_successful
        assert relaunched_uj.extra_vars == json.dumps(dict(var="$encrypted$"))
