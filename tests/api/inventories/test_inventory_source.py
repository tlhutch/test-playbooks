from towerkit import exceptions as exc
import pytest

from tests.api import Base_Api_Test


@pytest.mark.api
@pytest.mark.destructive
@ pytest.mark.usefixtures('authtoken', 'install_enterprise_license_unlimited')
class TestInventorySource(Base_Api_Test):

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

    @pytest.mark.github('https://github.com/ansible/tower/issues/837')
    def test_conflict_exception_with_running_inventory_update(self, factories):
        inv_source = factories.v2_inventory_source()
        inv_update = inv_source.update()

        with pytest.raises(exc.Conflict) as e:
            inv_source.delete()
        assert e.value[1] == {'conflict': 'Resource is being used by running jobs.', 'active_jobs': [{'type': 'inventory_update', u'id': inv_update.id}]}

        assert inv_source.wait_until_completed().is_successful
        assert inv_update.get().is_successful

    def test_delete_sublist_resources(self, factories):
        inv_source = factories.v2_inventory_source()
        assert inv_source.update().wait_until_completed().is_successful

        groups = inv_source.related.groups.get()
        hosts = inv_source.related.hosts.get()
        assert groups.count
        assert hosts.count

        groups.delete()
        hosts.delete()

        for group in groups.results:
            with pytest.raises(exc.NotFound):
                group.get()
        for host in hosts.results:
            with pytest.raises(exc.NotFound):
                host.get()
        assert groups.get().count == 0
        assert hosts.get().count == 0
