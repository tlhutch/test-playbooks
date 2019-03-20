import re

from towerkit import exceptions as exc
import fauxfactory
import pytest

from tests.api import APITest


@pytest.mark.api
@pytest.mark.usefixtures('authtoken', 'install_enterprise_license_unlimited')
class TestUnifiedJobTemplates(APITest):

    @pytest.mark.parametrize('ujt_type, ujt_type_name',
                             [('v2_job_template', 'JobTemplate'),
                              ('v2_workflow_job_template', 'WorkflowJobTemplate'),
                              ('v2_project', 'Project'),
                              ('v2_inventory_source', 'InventorySource')],
                             ids=('Job Template', 'Workflow Job Template', 'Project', 'Inventory Source'))
    def test_unique_together_violating_duplicates_disallowed(self, factories, ujt_type, ujt_type_name):
        ujt_factory = getattr(factories, ujt_type)
        ujt_factory_kwargs = dict(name=fauxfactory.gen_utf8())

        if ujt_type == 'v2_inventory_source':
            org = factories.v2_organization()
            ujt_factory_kwargs['inventory'] = factories.v2_inventory(organization=org)
            ujt_factory_kwargs['inventory_script'] = (True, dict(organization=org))
        else:
            ujt_factory_kwargs['organization'] = factories.v2_organization()

        ujt_factory(**ujt_factory_kwargs)

        with pytest.raises(exc.Duplicate) as e:
            ujt_factory(**ujt_factory_kwargs)

        assert re.match(
            r'{0} with this \([^)]+\) combination already exists.'.format(
                ujt_type_name
            ),
            e.value.msg['__all__'][0]
        ) is not None, e.value.msg['__all__']
