from towerkit import exceptions as exc
import pytest

from tests.api import Base_Api_Test


@pytest.mark.api
@pytest.mark.skip_selenium
@pytest.mark.usefixtures('authtoken', 'install_enterprise_license_unlimited')
class TestUnifiedJobs(Base_Api_Test):

    @pytest.mark.parametrize('fixture, method', [('job_template', 'launch'),
                                                 ('workflow_job_template', 'launch'),
                                                 ('ad_hoc_command', None),
                                                 ('project', 'update'),
                                                 ('custom_inventory_source', 'update'),
                                                 ('cleanup_facts_template', 'launch')],
    ids=['job', 'workflow job', 'ad hoc command', 'project_update', 'inventory_update', 'system job'])
    def test_delete_running_unified_job_forbidden(self, request, fixture, method):
        if method:
            resource = request.getfixturevalue(fixture)
            uj = getattr(resource, method)()
        else:
            uj = request.getfixturevalue(fixture)

        with pytest.raises(exc.Forbidden) as e:
            uj.delete()
        assert e.value[1]['detail'] == 'Cannot delete running job resource.'
