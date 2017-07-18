from towerkit import exceptions as exc
import pytest

from tests.api import Base_Api_Test


@pytest.mark.api
@pytest.mark.ha_tower
@pytest.mark.skip_selenium
@pytest.mark.destructive
class TestInventorySource(Base_Api_Test):

    pytestmark = pytest.mark.usefixtures('authtoken', 'install_enterprise_license_unlimited')

    def test_disallowed_manual_source(self, factories):
        with pytest.raises(exc.BadRequest) as e:
            factories.v2_inventory_source(source="")
        assert e.value[1] == {'source': ['Manual inventory sources are created automatically when a group is created in the v1 API.']}
