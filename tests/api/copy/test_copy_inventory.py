from fauxfactory import gen_boolean, gen_alpha
from towerkit.utils import poll_until
import pytest

from tests.api import Base_Api_Test
from tests.lib.helpers.copy_utils import check_fields


@pytest.mark.api
@pytest.mark.usefixtures('authtoken', 'install_enterprise_license_unlimited')
class Test_Copy_Inventory(Base_Api_Test):

    identical_fields = ['type', 'description', 'organization', 'kind', 'host_filter', 'variables', 'total_hosts',
                        'total_groups', 'has_inventory_sources', 'total_inventory_sources']
    unequal_fields = ['id', 'created', 'modified']

    def check_group_fields(self, old_group, new_group, old_inventory, new_inventory):
        identical_fields = ['type', 'name', 'description', 'variables', 'total_hosts', 'total_groups',
                            'has_inventory_sources']
        unequal_fields = ['id', 'created', 'modified', 'inventory']

        assert old_group.inventory == old_inventory.id
        assert new_group.inventory == new_inventory.id
        check_fields(old_group, new_group, identical_fields, unequal_fields)

    def check_host_fields(self, old_host, new_host, old_inventory, new_inventory):
        identical_fields = ['type', 'name', 'description', 'enabled', 'instance_id', 'variables',
                            'has_inventory_sources', 'insights_system_id']
        unequal_fields = ['id', 'created', 'modified', 'inventory']

        assert old_host.inventory == old_inventory.id
        assert new_host.inventory == new_inventory.id
        check_fields(old_host, new_host, identical_fields, unequal_fields)

    def test_copy_normal_inventory_with_variables(self, factories, copy_with_teardown):
        inventory = factories.v2_inventory(variables='{"foo":"bar"}')
        new_inventory = copy_with_teardown(inventory)
        check_fields(inventory, new_inventory, self.identical_fields, self.unequal_fields)

    def test_copy_inventory_instance_groups(self, factories, copy_with_teardown):
        ig = factories.instance_group()
        inventory = factories.v2_inventory()
        inventory.add_instance_group(ig)
        new_inventory = copy_with_teardown(inventory)
        check_fields(inventory, new_inventory, self.identical_fields, self.unequal_fields)

        old_igs = inventory.related.instance_groups.get()
        new_igs = new_inventory.related.instance_groups.get()

        assert old_igs.count == 1
        assert new_igs.count == old_igs.count
        assert new_igs.results[0].id == old_igs.results[0].id

    def test_copy_smart_inventory(self, factories, copy_with_teardown):
        # Create one host
        organization = factories.v2_organization()
        inventory = factories.v2_inventory(organization=organization)
        factories.v2_host(inventory=inventory)

        smart_inventory = factories.v2_inventory(organization=organization, kind='smart', host_filter='id__gt=0')
        assert smart_inventory.total_hosts == 1

        new_inventory = smart_inventory.copy()
        check_fields(smart_inventory, new_inventory, self.identical_fields, self.unequal_fields)

    def test_copy_inventory_hosts_and_groups(self, factories, copy_with_teardown):
        # Create a DAG of groups and hosts
        inventory = factories.v2_inventory()
        groups = [factories.v2_group(inventory=inventory, variables='{"foo":"bar"}') for _ in range(4)]
        hosts = [factories.v2_host(inventory=inventory, enabled=gen_boolean(), variables='{"foo":"bar"}',
                                    instance_id=gen_alpha()) for _ in range(3)]
        groups[0].add_group(groups[1])
        groups[0].add_group(groups[2])
        groups[1].add_group(groups[2])
        groups[1].add_host(hosts[0])
        groups[2].add_host(hosts[0])
        groups[2].add_host(hosts[1])
        inventory.get()
        assert inventory.total_groups == len(groups)
        assert inventory.total_hosts == len(hosts)

        # Make a copy
        old_inventory = inventory
        new_inventory = inventory.copy()
        poll_until(lambda: check_fields(inventory, new_inventory.get(),
                                        self.identical_fields, self.unequal_fields, no_assert=True),
                   timeout=30)

        # Traverse the old & new graphs of groups & hosts
        visited = set() # set of visited node names
        old_frontier = sorted(old_inventory.related.root_groups.get().results, key=lambda n: n.name)
        new_frontier = sorted(new_inventory.related.root_groups.get().results, key=lambda n: n.name)

        assert len(old_frontier) == len(new_frontier)
        while old_frontier:
            old_group = old_frontier.pop()
            new_group = new_frontier.pop()
            self.check_group_fields(old_group, new_group, old_inventory, new_inventory)

            if old_group.name in visited:
                continue
            visited.add(old_group.name)

            old_children = sorted(old_group.related.children.get().results, key=lambda n: n.name)
            new_children = sorted(new_group.related.children.get().results, key=lambda n: n.name)
            assert len(old_children) == len(new_children)
            old_frontier.extend(old_children)
            new_frontier.extend(new_children)

            old_hosts = sorted(old_group.related.hosts.get().results, key=lambda n: n.name)
            new_hosts = sorted(new_group.related.hosts.get().results, key=lambda n: n.name)
            assert len(old_hosts) == len(new_hosts)
            for i in range(len(old_hosts)):
                self.check_host_fields(old_hosts[i], new_hosts[i], old_inventory, new_inventory)
        assert not new_frontier

    @pytest.mark.github('https://github.com/ansible/tower/issues/2303')
    def test_copy_inventory_with_sources(self, cloud_inventory, copy_with_teardown):
        assert cloud_inventory.get().has_inventory_sources
        new_inventory = copy_with_teardown(cloud_inventory)
        poll_until(lambda: check_fields(cloud_inventory, new_inventory.get(),
                                        self.identical_fields, self.unequal_fields, no_assert=True),
                   timeout=30)

    # TODO: test source from project
    # TODO: test credential of sources

    def test_copy_inventory_insights_credential_with_permission(self, factories, copy_with_teardown):
        insights_cred = factories.v2_credential(kind='insights')
        inventory = factories.v2_inventory(insights_credential=insights_cred.id)
        assert inventory.insights_credential == insights_cred.id

        new_inventory = copy_with_teardown(inventory)
        check_fields(inventory, new_inventory, self.identical_fields, self.unequal_fields)
        assert new_inventory.insights_credential == inventory.insights_credential

    @pytest.mark.github('https://github.com/ansible/tower/issues/2263')
    def test_copy_inventory_insights_credential_without_permission(self, factories, copy_with_teardown, set_test_roles):
        insights_cred = factories.v2_credential(kind='insights')
        organization = factories.v2_organization()
        inventory = factories.v2_inventory(organization=organization, insights_credential=insights_cred.id)
        user = factories.user()
        set_test_roles(user, organization, 'user', 'admin')

        with self.current_user(user):
            new_inventory = copy_with_teardown(inventory)
            check_fields(inventory, new_inventory, self.identical_fields, self.unequal_fields)
            assert not new_inventory.insights_credential
