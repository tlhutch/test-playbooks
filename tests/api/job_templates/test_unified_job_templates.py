import re

from towerkit import exceptions as exc
import fauxfactory
import pytest

from tests.api import APITest


@pytest.mark.api
@pytest.mark.usefixtures('authtoken', 'install_enterprise_license_unlimited')
class TestUnifiedJobTemplates(APITest):

    @pytest.mark.parametrize('ujt_type, ujt_type_name',
                             [('job_template', 'JobTemplate'),
                              ('workflow_job_template', 'WorkflowJobTemplate'),
                              ('project', 'Project'),
                              ('inventory_source', 'InventorySource')],
                             ids=('Job Template', 'Workflow Job Template', 'Project', 'Inventory Source'))
    def test_unique_together_violating_duplicates_disallowed(self, factories, ujt_type, ujt_type_name):
        ujt_factory = getattr(factories, ujt_type)
        ujt_factory_kwargs = dict(name=fauxfactory.gen_utf8())

        if ujt_type == 'inventory_source':
            org = factories.organization()
            ujt_factory_kwargs['inventory'] = factories.inventory(organization=org)
            ujt_factory_kwargs['inventory_script'] = (True, dict(organization=org))
        else:
            ujt_factory_kwargs['organization'] = factories.organization()

        ujt_factory(**ujt_factory_kwargs)

        with pytest.raises(exc.Duplicate) as e:
            ujt_factory(**ujt_factory_kwargs)

        assert re.match(
            r'{0} with this \([^)]+\) combination already exists.'.format(
                ujt_type_name
            ),
            e.value.msg['__all__'][0]
        ) is not None, e.value.msg['__all__']
