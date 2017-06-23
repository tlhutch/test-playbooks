import types

import towerkit.exceptions
import fauxfactory
import pytest

from tests.api import Base_Api_Test


@pytest.mark.api
@pytest.mark.skip_selenium
class Test_Host_Filter(Base_Api_Test):

    pytestmark = pytest.mark.usefixtures('authtoken', 'install_enterprise_license_unlimited', 'loaded_inventory')
    test_hosts = ['hostA', 'hostAA', 'hostB', 'hostDup']

    def find_hosts(self, response):
        # filter the stock localhost as well as any hosts resulting from incomplete test teardown
        return [host.name for host in response.results if host.name in self.test_hosts]

    @pytest.fixture(scope="class")
    def loaded_inventory(self, class_factories):
        """Setup for host filter tests."""
        inventory = class_factories.v2_inventory()

        groupA = class_factories.group(inventory=inventory, name="groupA")
        groupAA = class_factories.group(inventory=inventory, name="groupAA")
        groupB = class_factories.group(inventory=inventory, name="groupB")

        hostA = class_factories.host(inventory=inventory, name="hostA")
        hostAA = class_factories.host(inventory=inventory, name="hostAA")
        hostB = class_factories.host(inventory=inventory, name="hostB")
        hostDup = class_factories.host(inventory=inventory, name="hostDup")

        groupA.add_host(hostA)
        groupAA.add_host(hostAA)
        groupB.add_host(hostB)
        for group in [groupA, groupAA, groupB]:
            group.add_host(hostDup)
        groupA.add_group(groupAA)

        # populate hosts with ansible facts
        jt = class_factories.job_template(inventory=inventory, playbook='gather_facts.yml',
                                          use_fact_cache=True)
        assert jt.launch().wait_until_completed().is_successful
        return inventory

    @pytest.mark.parametrize('host_filter, expected_hosts',
        [
            ('name=hostA', ['hostA']),
            ('name=not_found', []),
            ('name=hostDup', ['hostDup']),
        ]
    )
    def test_basic_host_search(self, v2, host_filter, expected_hosts):
        response = v2.hosts.get(host_filter=host_filter, page_size=200)
        assert self.find_hosts(response) == expected_hosts

    @pytest.mark.parametrize('host_filter, expected_hosts',
        [
            ('name=hostA or name=hostB', ['hostA', 'hostB']),
            ('name=hostA or name=not_found', ['hostA']),
            ('name=not_found or name=not_found', []),
            ('name=hostA or name=hostA', ['hostA']),
            ('name=hostDup or name=hostDup', ['hostDup']),
            ('name=hostA or name=hostAA or name=not_found', ['hostA', 'hostAA'])
        ]
    )
    def test_host_search_with_or(self, v2, host_filter, expected_hosts):
        response = v2.hosts.get(host_filter=host_filter, page_size=200)
        assert self.find_hosts(response) == expected_hosts

    @pytest.mark.parametrize('host_filter, expected_hosts',
        [
            ('name=hostA and name=hostB', []),
            ('name=hostA and name=hostA', ['hostA']),
            ('name=not_found and name=not_found', []),
            ('name=hostDup and name=hostDup', ['hostDup']),
            ('name=hostA and name=hostB and name=not_found', []),
        ]
    )
    def test_host_search_with_and(self, v2, host_filter, expected_hosts):
        response = v2.hosts.get(host_filter=host_filter, page_size=200)
        assert self.find_hosts(response) == expected_hosts

    @pytest.mark.parametrize('host_filter, expected_hosts',
        [
            ('groups__name=groupA', ['hostA', 'hostDup']),
            ('groups__name=groupAA', ['hostAA', 'hostDup']),
            ('groups__name=not_found', []),
        ]
    )
    def test_basic_group_search(self, v2, host_filter, expected_hosts):
        response = v2.hosts.get(host_filter=host_filter, page_size=200)
        assert self.find_hosts(response) == expected_hosts

    @pytest.mark.github('https://github.com/ansible/ansible-tower/issues/6233')
    @pytest.mark.parametrize('host_filter, expected_hosts',
        [
            ('groups__name=groupA or groups__name=groupB', ['hostA', 'hostB', 'hostDup']), # 6233
            ('groups__name=groupA or groups__name=not_found', ['hostA', 'hostDup']),
            ('groups__name=not_found or groups__name=not_found', []),
            ('groups__name=groupA or groups__name=groupA', ['hostA', 'hostDup']),
            ('groups__name=groupA or groups__name=groupAA or groups__name=not_found', ['hostA', 'hostAA', 'hostDup']) # 6233
        ]
    )
    def test_group_search_with_or(self, v2, host_filter, expected_hosts):
        response = v2.hosts.get(host_filter=host_filter, page_size=200)
        assert self.find_hosts(response) == expected_hosts

    @pytest.mark.parametrize('host_filter, expected_hosts',
        [
            ('groups__name=groupA and groups__name=groupB', ['hostDup']),
            ('groups__name=groupA and groups__name=groupA', ['hostA', 'hostDup']),
            ('groups__name=non_found and groups__name=not_found', []),
            ('groups__name=groupA and groups__name=groupB and groups__name=not_found', [])
        ]
    )
    def test_group_search_with_and(self, v2, host_filter, expected_hosts):
        response = v2.hosts.get(host_filter=host_filter, page_size=200)
        assert self.find_hosts(response) == expected_hosts

    @pytest.mark.github('https://github.com/ansible/ansible-tower/issues/6015')
    @pytest.mark.parametrize('ansible_fact',
        [
            "ansible_python_version", # string
            "ansible_processor_cores", # integer
            "ansible_fips", # boolean
            # FIXME: add in a simple empty list query
            "ansible_default_ipv6" # empty dictionary
        ]
    )
    def test_dictionary_fact_search(self, v2, loaded_inventory, ansible_fact):
        host = loaded_inventory.related.hosts.get().results.pop()
        ansible_facts = host.related.ansible_facts.get()

        raw_value = getattr(ansible_facts, ansible_fact)
        expected_value = str(raw_value).lower() if isinstance(raw_value, types.BooleanType) else raw_value

        host_filter = "ansible_facts__{0}={1}".format(ansible_fact, expected_value)
        response = v2.hosts.get(host_filter=host_filter, page_size=200)
        assert self.find_hosts(response) == self.test_hosts

    def test_list_fact_search(self, v2, loaded_inventory):
        host = loaded_inventory.related.hosts.get().results.pop()
        ansible_interfaces = host.related.ansible_facts.get().ansible_interfaces

        for item in ansible_interfaces:
            host_filter = "ansible_facts__ansible_interfaces[]={0}".format(item)
            response = v2.hosts.get(host_filter=host_filter, page_size=200)
            assert self.find_hosts(response) == self.test_hosts

    def test_nested_dictionary_fact_search(self, v2, loaded_inventory):
        host = loaded_inventory.related.hosts.get().results.pop()
        python_version = host.related.ansible_facts.get().ansible_python.version

        for item in python_version.items():
            host_filter = "ansible_facts__ansible_python__version__{0}={1}".format(item[0], item[1])
            response = v2.hosts.get(host_filter=host_filter, page_size=200)
            assert self.find_hosts(response) == self.test_hosts

    def test_nested_list_fact_search(self, v2, loaded_inventory):
        host = loaded_inventory.related.hosts.get().results.pop()
        version_info = host.related.ansible_facts.get().ansible_python.version_info

        for item in version_info:
            host_filter = "ansible_facts__ansible_python__version_info[]={0}".format(item)
            response = v2.hosts.get(host_filter=host_filter, page_size=200)
            assert self.find_hosts(response) == self.test_hosts

    @pytest.mark.parametrize('host_filter, expected_results',
        [
            ("ansible_facts__ansible_system=Linux or ansible_facts__ansible_system=Linux", True),
            ("ansible_facts__ansible_system=Linux or ansible_facts__ansible_system=not_found", True),
            ("ansible_facts__ansible_system=not_found or ansible_facts__ansible_system=not_found", False),
            ("ansible_facts__ansible_system=Linux or ansible_facts__ansible_system=Linux \
                or ansible_facts__ansible_system=not_found", True)
        ]
    )
    def test_fact_search_with_or(self, v2, host_filter, expected_results):
        response = v2.hosts.get(host_filter=host_filter)
        if expected_results:
            assert self.find_hosts(response) == self.test_hosts
        else:
            assert not self.find_hosts(response)

    @pytest.mark.parametrize('host_filter, expected_results',
        [
            ("ansible_facts__ansible_system=Linux and ansible_facts__ansible_system=Linux", True),
            ("ansible_facts__ansible_system=Linux and ansible_facts__ansible_system=not_found", False),
            ("ansible_facts__ansible_system=not_found and ansible_facts__ansible_system=not_found", False),
            ("ansible_facts__ansible_system=Linux and ansible_facts__ansible_system=Linux \
                and ansible_facts__ansible_system=not_found", False)
        ]
    )
    def test_fact_search_with_and(self, v2, host_filter, expected_results):
        response = v2.hosts.get(host_filter=host_filter)
        if expected_results:
            assert self.find_hosts(response) == self.test_hosts
        else:
            assert not self.find_hosts(response)

    @pytest.mark.github('https://github.com/ansible/ansible-tower/issues/6233')
    @pytest.mark.parametrize('host_filter, expected_hosts',
        [
            ('name=hostA or groups__name=groupA or ansible_facts__ansible_system=Linux', ['hostA', 'hostAA', 'hostB', 'hostDup']),
            ('name=hostA or groups__name=groupA or ansible_facts__ansible_system=not_found', ['hostA', 'hostDup']),
            ('name=hostA or groups__name=not_found or ansible_facts__ansible_system=not_found', ['hostA']),
            ('name=not_found or groups__name=not_found or ansible_facts__ansible_system=not_found', []),
            ('name=hostA and groups__name=groupA and ansible_facts__ansible_system=Linux', ['hostA']),
            ('name=hostA and groups__name=groupA and ansible_facts__ansible_system=not_found', []),
            ('name=hostA and groups__name=not_found and ansible_facts__ansible_system=not_found', []),
            ('name=not_found and groups__name=not_found and ansible_facts__ansible_system=not_found', []),
        ]
    )
    def test_basic_hyrid_search(self, v2, host_filter, expected_hosts):
        response = v2.hosts.get(host_filter=host_filter, page_size=200)
        assert self.find_hosts(response) == expected_hosts

    @pytest.mark.parametrize('host_filter, expected_hosts',
        [
            ('name=hostA or (groups__name=groupAA and ansible_facts__ansible_system=not_found)', ['hostA']),
            ('name=hostA or (groups__name=not_found and ansible_facts__ansible_system=Linux)', ['hostA']),
            ('name=not_found or (groups__name=groupAA and ansible_facts__ansible_system=Linux)', ['hostAA', 'hostDup']),
            ('(name=hostA or groups__name=groupAA) and ansible_facts__ansible_system=not_found', []),
            ('(name=hostA or groups__name=not_found) and ansible_facts__ansible_system=Linux', ['hostA']),
            ('(name=not_found or groups__name=groupAA) and ansible_facts__ansible_system=Linux', ['hostAA', 'hostDup']),
        ]
    )
    def test_advanced_hybrid_search(self, v2, host_filter, expected_hosts):
        response = v2.hosts.get(host_filter=host_filter, page_size=200)
        assert self.find_hosts(response) == expected_hosts

    @pytest.mark.parametrize('host_filter',
        [
            ('name=hostA or (groups__name=groupAA and ansible_facts__ansible_system=not_found)'),
            ('name=hostA or (groups__name=not_found and ansible_facts__ansible_system=Linux)'),
            ('name=not_found or (groups__name=groupAA and ansible_facts__ansible_system=Linux)'),
            ('(name=hostA or groups__name=groupAA) and ansible_facts__ansible_system=not_found'),
            ('(name=hostA or groups__name=not_found) and ansible_facts__ansible_system=Linux'),
            ('(name=not_found or groups__name=groupAA) and ansible_facts__ansible_system=Linux'),
        ]
    )
    def test_smart_inventory(self, factories, v2, host_filter):
        """host_filter should determine a smart inventory's hosts."""
        inventory = factories.v2_inventory(kind='smart', host_filter=host_filter)
        hosts = inventory.related.hosts.get()

        response = v2.hosts.get(host_filter=host_filter, page_size=200)
        assert self.find_hosts(response) == self.find_hosts(hosts)

    def test_host_filter_update(self, factories, loaded_inventory):
        """host_filter changes should be immediately reflected in a
        smart inventory's hosts.
        """
        inventory = factories.v2_inventory(kind='smart', host_filter="name=hostA")
        hosts = inventory.related.hosts.get()
        assert self.find_hosts(hosts) == ['hostA']

        inventory.host_filter = "name=hostB"
        assert self.find_hosts(hosts.get()) == ['hostB']

    def test_smart_search(self, v2, factories):
        name, description = fauxfactory.gen_utf8(), fauxfactory.gen_utf8()
        host = factories.host(name=name, description=description)

        host_filters = [u"search={0}".format(name),
                        u"search={0}".format(description),
                        u"search={0}".format(name)[:10],
                        u"search={0}".format(description)[:10]]
        for host_filter in host_filters:
            response = v2.hosts.get(host_filter=host_filter)
            assert response.count == 1
            assert response.results.pop().id == host.id

    def test_unicode_search(self, v2, factories):
        host_name = fauxfactory.gen_utf8()
        group_name = fauxfactory.gen_utf8()
        group = factories.group(name=group_name)
        host = factories.host(name=host_name, inventory=group.ds.inventory)
        group.add_host(host)

        host_filters = [u"name={0}".format(host_name), u"groups__name={0}".format(group_name)]
        for host_filter in host_filters:
            response = v2.hosts.get(host_filter=host_filter, page_size=200)
            assert response.count == 1
            assert response.results.pop().id == host.id

    @pytest.mark.parametrize("invalid_search", ["string", 1, 1.0, (0, 0), [0], {"k": "v"}, True],
        ids=["string", "integer", "float", "tuple", "list", "dict", "bool"])
    def test_invalid_search(self, v2, invalid_search):
        with pytest.raises(towerkit.exceptions.BadRequest):
            v2.hosts.get(host_filter=invalid_search)
