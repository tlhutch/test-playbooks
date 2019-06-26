import pytest

from tests.api import APITest


@pytest.mark.usefixtures('authtoken')
class TestHostFilterRBAC(APITest):

    def filter_response(self, response):
        return [host.id for host in response.results]

    def find_hosts(self, inventory):
        hosts = inventory.related.hosts.get()
        return [host.id for host in hosts.results]

    @pytest.fixture(scope="class")
    def loaded_inventories(self, class_factories):
        orgA, orgB = [class_factories.organization() for _ in range(2)]
        invA, invB = [class_factories.inventory(organization=org) for org in (orgA, orgB)]

        hostDupA = class_factories.host(name="hostDup", inventory=invA)
        hostDupB = class_factories.host(name="hostDup", inventory=invB)
        groupDupA = class_factories.group(name="groupDup", inventory=invA)
        groupDupB = class_factories.group(name="groupDup", inventory=invB)
        groupDupA.add_host(hostDupA)
        groupDupB.add_host(hostDupB)

        jtA = class_factories.job_template(inventory=invA, playbook='gather_facts.yml',
                                           use_fact_cache=True)
        jtB = class_factories.job_template(inventory=invB, playbook='gather_facts.yml',
                                           use_fact_cache=True)
        for jt in [jtA, jtB]:
            jt.launch().wait_until_completed().assert_successful()

        return invA, invB

    @pytest.mark.parametrize("host_filter",
        ["name=hostDup", "groups__name=groupDup", "ansible_facts__ansible_system=Linux"])
    def test_with_inventory_read(self, factories, v2, loaded_inventories, host_filter):
        invA, invB = loaded_inventories[0], loaded_inventories[1]
        userA, userB = factories.user(), factories.user()
        invA.set_object_roles(userA, 'read'), invB.set_object_roles(userB, 'read')

        with self.current_user(username=userA.username, password=userA.password):
            response = v2.hosts.get(host_filter=host_filter)
            assert self.filter_response(response) == self.find_hosts(invA)

        with self.current_user(username=userB.username, password=userB.password):
            response = v2.hosts.get(host_filter=host_filter)
            assert self.filter_response(response) == self.find_hosts(invB)

    @pytest.mark.parametrize("host_filter",
        ["name=hostDup", "groups__name=groupDup", "ansible_facts__ansible_system=Linux"])
    def test_with_org_admin(self, factories, v2, loaded_inventories, host_filter):
        invA, invB = loaded_inventories[0], loaded_inventories[1]
        userA, userB = factories.user(), factories.user()
        invA.ds.organization.add_admin(userA), invB.ds.organization.add_admin(userB)

        with self.current_user(username=userA.username, password=userA.password):
            response = v2.hosts.get(host_filter=host_filter)
            assert self.filter_response(response) == self.find_hosts(invA)

        with self.current_user(username=userB.username, password=userB.password):
            response = v2.hosts.get(host_filter=host_filter)
            assert self.filter_response(response) == self.find_hosts(invB)
