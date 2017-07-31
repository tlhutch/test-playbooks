from towerkit import exceptions as exc
import fauxfactory
import pytest

from tests.api import Base_Api_Test


@pytest.mark.api
@pytest.mark.skip_selenium
@pytest.mark.destructive
class TestSmartInventory(Base_Api_Test):

    pytestmark = pytest.mark.usefixtures('authtoken', 'install_enterprise_license_unlimited')

    def test_host_update(self, factories):
        """Smart inventory hosts should reflect host changes."""
        host = factories.host()
        inventory = factories.v2_inventory(kind='smart', host_filter="name={0}".format(host.name))
        hosts = inventory.related.hosts.get()

        host.description = fauxfactory.gen_utf8()
        assert hosts.get().results.pop().description == host.description

        host.delete()
        assert hosts.get().count == 0

    def test_manual_host_creation(self, factories):
        inventory = factories.v2_inventory(host_filter='name=localhost', kind='smart')
        with pytest.raises(exc.BadRequest) as e:
            factories.v2_host(inventory=inventory)
        assert e.value[1]['inventory'] == {'detail': 'Cannot create Host for Smart Inventory'}

    def test_manual_group_creation(self, factories):
        inventory = factories.v2_inventory(host_filter='name=localhost', kind='smart')
        with pytest.raises(exc.BadRequest) as e:
            factories.v2_group(inventory=inventory)
        assert e.value[1]['inventory'] == {'detail': 'Cannot create Group for Smart Inventory'}

    def test_manual_inventory_source_creation(self, factories):
        inventory = factories.v2_inventory(host_filter='name=localhost', kind='smart')
        with pytest.raises(exc.BadRequest) as e:
            factories.v2_inventory_source(inventory=inventory)
        assert e.value[1]['inventory'] == {'detail': 'Cannot create Inventory Source for Smart Inventory'}

    def test_smart_inventories_cannot_inventory_update(self, factories):
        """Smart inventories should reject a POST to /api/v2/inventories/N/update_inventory_sources/."""
        inventory = factories.v2_inventory(host_filter='name=localhost', kind='smart')
        with pytest.raises(exc.BadRequest) as e:
            inventory.update_inventory_sources()
        assert e.value[1] == {'error': 'Inventory Update cannot be completed with Smart Inventory.'}

    def test_smart_inventories_cannot_have_insights_credentials(self, factories):
        """Smart inventories should not have Insights credentials."""
        credential = factories.v2_credential(kind='insights')
        expected_error = ['Assignment not allowed for Smart Inventory']

        with pytest.raises(exc.BadRequest) as e:
            factories.v2_inventory(host_filter='name=localhost', kind='smart', insights_credential=credential.id)
        assert e.value.message['insights_credential'] == expected_error

        inventory = factories.v2_inventory(host_filter='name=localhost', kind='smart')
        with pytest.raises(exc.BadRequest) as e:
            inventory.insights_credential = credential.id
        assert e.value.message['insights_credential'] == expected_error
