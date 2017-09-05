from towerkit import exceptions as exc
import pytest

from tests.api import Base_Api_Test


@pytest.mark.api
@pytest.mark.skip_selenium
@pytest.mark.destructive
class TestInventorySource(Base_Api_Test):

    pytestmark = pytest.mark.usefixtures('authtoken', 'install_enterprise_license_unlimited')

    def test_v1_post_disallowed(self, api_inventory_sources_pg):
        with pytest.raises(exc.MethodNotAllowed):
            api_inventory_sources_pg.post()

    def test_disallowed_manual_source(self, factories):
        with pytest.raises(exc.BadRequest) as e:
            factories.v2_inventory_source(source="")
        assert e.value[1] == {'source': ['Manual inventory sources are created automatically when a group is created in the v1 API.']}

    def test_reject_invalid_credential_types_with_custom_source(self, factories):
        inventory = factories.v2_inventory()
        org = inventory.ds.organization
        inv_script = factories.v2_inventory_script(organization=org)

        kinds = ['vault', 'ssh', 'scm', 'insights']
        for kind in kinds:
            if kind == 'vault':
                cred = factories.v2_credential(organization=org, kind=kind, inputs=dict(vault_password='fake'))
            else:
                cred = factories.v2_credential(organization=org, kind=kind)

            error = {'credential': ['Credentials of type machine, source control, insights and vault are disallowed for custom inventory sources.']}
            with pytest.raises(exc.BadRequest) as e:
                factories.v2_inventory_source(inventory=inventory, inventory_script=inv_script, credential=cred)
            assert e.value[1] == error

            inv_source = factories.v2_inventory_source(inventory=inventory, inventory_script=inv_script)
            with pytest.raises(exc.BadRequest) as e:
                inv_source.credential = cred.id
            assert e.value[1] == error
