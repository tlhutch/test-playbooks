import pytest

from tests.api import APITest
from tests.lib.helpers.copy_utils import check_fields


@pytest.mark.api
@pytest.mark.usefixtures('authtoken', 'install_enterprise_license_unlimited')
class Test_Copy_Inventory_Script(APITest):

    identical_fields = ['type', 'description', 'script', 'organization']
    unequal_fields = ['id', 'created', 'modified']

    def test_copy_normal(self, copy_with_teardown, factories):
        v2_inventory_script = factories.v2_inventory_script()
        new_inventory_script = copy_with_teardown(v2_inventory_script)
        check_fields(v2_inventory_script, new_inventory_script, self.identical_fields, self.unequal_fields)
