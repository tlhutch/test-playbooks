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

    def test_unable_to_create_host(self, factories):
        inventory = factories.v2_inventory(host_filter='name=localhost', kind='smart')
        with pytest.raises(exc.BadRequest) as e:
            factories.v2_host(inventory=inventory)
        assert e.value[1]['inventory'] == {'detail': 'Cannot create Host for Smart Inventory'}

    def test_unable_to_create_group(self, factories):
        inventory = factories.v2_inventory(host_filter='name=localhost', kind='smart')
        with pytest.raises(exc.BadRequest) as e:
            factories.v2_group(inventory=inventory)
        assert e.value[1]['inventory'] == {'detail': 'Cannot create Group for Smart Inventory'}

    def test_unable_to_create_root_group(self, factories):
        inventory = factories.v2_inventory(host_filter='name=localhost', kind='smart')

        with pytest.raises(exc.BadRequest) as e:
            inventory.related.root_groups.post()
        assert e.value[1]['inventory'] == {'detail': 'Cannot create Group for Smart Inventory'}

    def test_unable_to_create_inventory_source(self, factories):
        inventory = factories.v2_inventory(host_filter='name=localhost', kind='smart')
        with pytest.raises(exc.BadRequest) as e:
            factories.v2_inventory_source(inventory=inventory)
        assert e.value[1]['inventory'] == {'detail': 'Cannot create Inventory Source for Smart Inventory'}

    def test_unable_to_inventory_update(self, factories):
        inventory = factories.v2_inventory(host_filter='name=localhost', kind='smart')
        with pytest.raises(exc.BadRequest) as e:
            inventory.update_inventory_sources()
        assert e.value[1] == {'detail': 'No inventory sources to update.'}

    def test_unable_to_have_insights_credential(self, factories):
        credential = factories.v2_credential(kind='insights')
        expected_error = ['Assignment not allowed for Smart Inventory']

        with pytest.raises(exc.BadRequest) as e:
            factories.v2_inventory(host_filter='name=localhost', kind='smart', insights_credential=credential.id)
        assert e.value.message['insights_credential'] == expected_error

        inventory = factories.v2_inventory(host_filter='name=localhost', kind='smart')
        with pytest.raises(exc.BadRequest) as e:
            inventory.insights_credential = credential.id
        assert e.value.message['insights_credential'] == expected_error

    def test_unable_to_update_regular_inventory_into_smart_inventory(self, factories):
        inventory = factories.v2_inventory()
        with pytest.raises(exc.MethodNotAllowed):
            inventory.patch(host_filter="name=localhost", kind="smart")

    def test_able_to_update_smart_inventory_into_regular_inventory(self, factories):
        inventory = factories.v2_inventory(host_filter="name=localhost", kind="smart")
        assert inventory.related.hosts.get().count == 1  # source stock localhost

        inventory.patch(host_filter="", kind="")
        assert inventory.related.hosts.get().count == 0

    @pytest.mark.github('https://github.com/ansible/ansible-tower/issues/7377')
    def test_launch_ahc_with_smart_inventory(self, factories):
        """Verify against isolated host, host in parent group, and host in child group."""
        inventory = factories.v2_inventory()
        parent_group, child_group = [factories.v2_group(inventory=inventory) for _ in range(2)]
        parent_group.add_group(child_group)
        for group in (parent_group, child_group):
            host = factories.v2_host(name="test_host_{0}".format(group.name), inventory=inventory)
            group.add_host(host)
        factories.v2_host(name="test_host_root", inventory=inventory)

        smart_inventory = factories.v2_inventory(host_filter="search=test_host", kind="smart")
        hosts = smart_inventory.related.hosts.get().results
        assert len(hosts) == 3

        ahc = factories.v2_ad_hoc_command(inventory=smart_inventory).wait_until_completed()
        assert ahc.is_successful

        for host in hosts:
            assert host.get().last_job == ahc.id

    @pytest.mark.github('https://github.com/ansible/ansible-tower/issues/7487')
    def test_launch_job_template_with_smart_inventory(self, factories):
        """Verify against isolated host, host in parent group, and host in child group."""
        inventory = factories.v2_inventory()
        parent_group, child_group = [factories.v2_group(inventory=inventory) for _ in range(2)]
        parent_group.add_group(child_group)
        for group in (parent_group, child_group):
            host = factories.v2_host(name="test_host_{0}".format(group.name), inventory=inventory)
            group.add_host(host)
        factories.v2_host(name="test_host_root", inventory=inventory)

        smart_inventory = factories.v2_inventory(host_filter="search=test_host", kind="smart")
        hosts = smart_inventory.related.hosts.get().results
        assert len(hosts) == 3

        jt = factories.v2_job_template(inventory=smart_inventory)
        job = jt.launch().wait_until_completed()
        assert job.is_successful

        for host in hosts:
            assert host.get().last_job == job.id

    def test_smart_inventory_deletion_should_not_cascade_delete_hosts(self, factories):
        host = factories.v2_host()
        inventory = factories.v2_inventory(kind='smart', host_filter='name={0}'.format(host.name))
        assert inventory.related.hosts.get().count == 1

        inventory.delete().wait_until_deleted()
        host.get()
