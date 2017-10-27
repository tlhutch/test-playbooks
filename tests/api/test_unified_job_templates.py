from towerkit import exceptions as exc
import fauxfactory
import pytest

from tests.api import Base_Api_Test


@pytest.mark.api
@pytest.mark.skip_selenium
@pytest.mark.usefixtures('authtoken', 'install_enterprise_license_unlimited')
class TestUnifiedJobTemplates(Base_Api_Test):

    @pytest.mark.parametrize('ujt_type, ujt_type_name',
                             [('v2_job_template', 'JobTemplate'),
                              ('v2_workflow_job_template', 'WorkflowJobTemplate'),
                              ('v2_project', 'Project'),
                              ('v2_inventory_source', 'InventorySource')],
                             ids=('Job Template', 'Workflow Job Template', 'Project', 'Inventory Source'))
    def test_unique_together_violating_duplicates_disallowed(self, factories, ujt_type, ujt_type_name):
        ujt_factory = getattr(factories, ujt_type)
        ujt_factory_kwargs = dict(name=fauxfactory.gen_utf8())

        if ujt_type == 'v2_job_template':
            unique_together = '(name)'
        elif ujt_type == 'v2_inventory_source':
            org = factories.v2_organization()
            ujt_factory_kwargs['inventory'] = factories.v2_inventory(organization=org)
            ujt_factory_kwargs['inventory_script'] = (True, dict(organization=org))
            unique_together = '(inventory, name)'
        else:
            ujt_factory_kwargs['organization'] = factories.v2_organization()
            unique_together = '(organization, name)'

        ujt_factory(**ujt_factory_kwargs)

        with pytest.raises(exc.BadRequest) as e:
            ujt_factory(**ujt_factory_kwargs)
        assert e.value.message['__all__'] == ['{0} with this {1} combination already exists.'
                                              .format(ujt_type_name, unique_together)]
