import types

import towerkit.exceptions
import fauxfactory
import pytest

from tests.api import Base_Api_Test


_memo = [None]


def random_suffix():
    if not _memo[0]:
        _memo[0] = 'xx' + fauxfactory.gen_alphanumeric()
    return _memo[0]


#  Randomness is needed for multiprocessing
host_a_name = 'hostA{}'.format(random_suffix())
host_aa_name = 'hostAA{}'.format(random_suffix())
host_b_name = 'hostB{}'.format(random_suffix())
host_dup_name = 'hostDup{}'.format(random_suffix())
group_a_name = 'groupA{}'.format(random_suffix())
group_aa_name = 'groupAA{}'.format(random_suffix())
group_b_name = 'groupB{}'.format(random_suffix())


@pytest.mark.api
@pytest.mark.skip_selenium
@pytest.mark.usefixtures('authtoken', 'install_enterprise_license_unlimited')
class TestHostFilter(Base_Api_Test):

    test_hosts = [host_a_name, host_aa_name, host_b_name, host_dup_name]

    def find_hosts(self, response):
        # filter the stock localhost as well as any hosts resulting from incomplete test teardown
        return set([host.name for host in response.results if host.name in self.test_hosts])

    @pytest.fixture(scope="class")
    def loaded_inventory(self, class_factories):
        """Setup for host filter tests."""
        inventory = class_factories.v2_inventory()

        groupA = class_factories.group(inventory=inventory, name=group_a_name)
        groupAA = class_factories.group(inventory=inventory, name=group_aa_name)
        groupB = class_factories.group(inventory=inventory, name=group_b_name)

        hostA = class_factories.host(inventory=inventory, name=host_a_name)
        hostAA = class_factories.host(inventory=inventory, name=host_aa_name)
        hostB = class_factories.host(inventory=inventory, name=host_b_name)
        hostDup = class_factories.host(inventory=inventory, name=host_dup_name)

        groupA.add_host(hostA)
        groupAA.add_host(hostAA)
        groupB.add_host(hostB)
        for group in [groupA, groupAA, groupB]:
            group.add_host(hostDup)
        groupA.add_group(groupAA)

        return inventory

    @pytest.fixture(scope='class')
    def populate_ansible_facts(self, class_factories, loaded_inventory):
        jt = class_factories.job_template(inventory=loaded_inventory, playbook='gather_facts.yml', use_fact_cache=True)
        assert jt.launch().wait_until_completed().is_successful

    @pytest.mark.mp_group('HostSearch', 'serial')
    @pytest.mark.parametrize('host_filter, expected_hosts',
        [
            ('name={}'.format(host_a_name), [host_a_name]),
            ('name=not_found', []),
            ('name={}'.format(host_dup_name), [host_dup_name]),
        ]
    )
    def test_basic_host_search(self, v2, loaded_inventory, host_filter, expected_hosts):
        response = v2.hosts.get(host_filter=host_filter, page_size=200)
        assert self.find_hosts(response) == set(expected_hosts)

    @pytest.mark.mp_group('HostSearchOr', 'serial')
    @pytest.mark.parametrize('host_filter, expected_hosts',
        [
            ('name={0} or name={1}'.format(host_a_name, host_b_name), [host_a_name, host_b_name]),
            ('name={} or name=not_found'.format(host_a_name), [host_a_name]),
            ('name=not_found or name=not_found', []),
            ('name={0} or name={0}'.format(host_a_name), [host_a_name]),
            ('name={0} or name={0}'.format(host_dup_name), [host_dup_name]),
            ('name={0} or name={1} or name=not_found'.format(host_a_name, host_aa_name), [host_a_name, host_aa_name])
        ]
    )
    def test_host_search_with_or(self, v2, loaded_inventory, host_filter, expected_hosts):
        response = v2.hosts.get(host_filter=host_filter, page_size=200)
        assert self.find_hosts(response) == set(expected_hosts)

    @pytest.mark.mp_group('HostSearch', 'serial')
    @pytest.mark.parametrize('host_filter, expected_hosts',
        [
            ('name={0} and name={1}'.format(host_a_name, host_b_name), []),
            ('name={0} and name={0}'.format(host_a_name), [host_a_name]),
            ('name=not_found and name=not_found', []),
            ('name={0} and name={0}'.format(host_dup_name), [host_dup_name]),
            ('name={0} and name={1} and name=not_found'.format(host_a_name, host_b_name), []),
        ]
    )
    def test_host_search_with_and(self, v2, loaded_inventory, host_filter, expected_hosts):
        response = v2.hosts.get(host_filter=host_filter, page_size=200)
        assert self.find_hosts(response) == set(expected_hosts)

    @pytest.mark.mp_group('GroupSearch', 'serial')
    @pytest.mark.parametrize('host_filter, expected_hosts',
        [
            ('groups__name={}'.format(group_a_name), [host_a_name, host_dup_name]),
            ('groups__name={}'.format(group_aa_name), [host_aa_name, host_dup_name]),
            ('groups__name=not_found', []),
        ]
    )
    def test_basic_group_search(self, v2, loaded_inventory, host_filter, expected_hosts):
        response = v2.hosts.get(host_filter=host_filter, page_size=200)
        assert self.find_hosts(response) == set(expected_hosts)

    @pytest.mark.mp_group('GroupSearch', 'serial')
    @pytest.mark.parametrize('host_filter, expected_hosts',
        [
            ('groups__name={0} or groups__name={1}'.format(group_a_name, group_b_name),
             [host_a_name, host_b_name, host_dup_name]),
            ('groups__name={} or groups__name=not_found'.format(group_a_name), [host_a_name, host_dup_name]),
            ('groups__name=not_found or groups__name=not_found', []),
            ('groups__name={0} or groups__name={0}'.format(group_a_name), [host_a_name, host_dup_name]),
            ('groups__name={0} or groups__name={1} or groups__name=not_found'.format(group_a_name, group_aa_name),
             [host_a_name, host_aa_name, host_dup_name])
        ]
    )
    def test_group_search_with_or(self, v2, loaded_inventory, host_filter, expected_hosts):
        response = v2.hosts.get(host_filter=host_filter, page_size=200)
        assert self.find_hosts(response) == set(expected_hosts)

    @pytest.mark.mp_group('GroupSearch', 'serial')
    @pytest.mark.parametrize('host_filter, expected_hosts',
        [
            ('groups__name={0} and groups__name={1}'.format(group_a_name, group_b_name), [host_dup_name]),
            ('groups__name={0} and groups__name={0}'.format(group_a_name), [host_a_name, host_dup_name]),
            ('groups__name=not_found and groups__name=not_found', []),
            ('groups__name={0} and groups__name={1} and groups__name=not_found'.format(group_a_name, group_b_name), [])
        ]
    )
    def test_group_search_with_and(self, v2, loaded_inventory, host_filter, expected_hosts):
        response = v2.hosts.get(host_filter=host_filter, page_size=200)
        assert self.find_hosts(response) == set(expected_hosts)

    @pytest.mark.mp_group('HostFactSearch', 'serial')
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
    def test_dictionary_fact_search(self, v2, loaded_inventory, populate_ansible_facts, ansible_fact):
        host = loaded_inventory.related.hosts.get().results.pop()
        ansible_facts = host.related.ansible_facts.get()

        raw_value = getattr(ansible_facts, ansible_fact)
        expected_value = str(raw_value).lower() if isinstance(raw_value, types.BooleanType) else raw_value

        host_filter = "ansible_facts__{0}={1}".format(ansible_fact, expected_value)
        response = v2.hosts.get(host_filter=host_filter, page_size=200)
        assert self.find_hosts(response) == self.test_hosts

    @pytest.mark.mp_group('HostFactSearch', 'serial')
    def test_list_fact_search(self, v2, loaded_inventory, populate_ansible_facts):
        host = loaded_inventory.related.hosts.get().results.pop()
        ansible_interfaces = host.related.ansible_facts.get().ansible_interfaces

        for item in ansible_interfaces:
            host_filter = "ansible_facts__ansible_interfaces[]={0}".format(item)
            response = v2.hosts.get(host_filter=host_filter, page_size=200)
            assert self.find_hosts(response) == set(self.test_hosts)

    @pytest.mark.mp_group('HostFactSearch', 'serial')
    def test_nested_dictionary_fact_search(self, v2, loaded_inventory, populate_ansible_facts):
        host = loaded_inventory.related.hosts.get().results.pop()
        python_version = host.related.ansible_facts.get().ansible_python.version

        for item in python_version.items():
            host_filter = "ansible_facts__ansible_python__version__{0}={1}".format(item[0], item[1])
            response = v2.hosts.get(host_filter=host_filter, page_size=200)
            assert self.find_hosts(response) == set(self.test_hosts)

    @pytest.mark.mp_group('HostFactSearch', 'serial')
    def test_nested_list_fact_search(self, v2, loaded_inventory, populate_ansible_facts):
        host = loaded_inventory.related.hosts.get().results.pop()
        version_info = host.related.ansible_facts.get().ansible_python.version_info

        for item in version_info:
            host_filter = "ansible_facts__ansible_python__version_info[]={0}".format(item)
            response = v2.hosts.get(host_filter=host_filter, page_size=200)
            assert self.find_hosts(response) == set(self.test_hosts)

    @pytest.mark.mp_group('HostFactSearch', 'serial')
    @pytest.mark.parametrize('host_filter, expected_results',
        [
            ("ansible_facts__ansible_system=Linux or ansible_facts__ansible_system=Linux", True),
            ("ansible_facts__ansible_system=Linux or ansible_facts__ansible_system=not_found", True),
            ("ansible_facts__ansible_system=not_found or ansible_facts__ansible_system=not_found", False),
            ("ansible_facts__ansible_system=Linux or ansible_facts__ansible_system=Linux \
                or ansible_facts__ansible_system=not_found", True)
        ]
    )
    def test_fact_search_with_or(self, v2, populate_ansible_facts, host_filter, expected_results):
        response = v2.hosts.get(host_filter=host_filter)
        if expected_results:
            assert self.find_hosts(response) == set(self.test_hosts)
        else:
            assert not self.find_hosts(response)

    @pytest.mark.mp_group('HostFactSearch', 'serial')
    @pytest.mark.parametrize('host_filter, expected_results',
        [
            ("ansible_facts__ansible_system=Linux and ansible_facts__ansible_system=Linux", True),
            ("ansible_facts__ansible_system=Linux and ansible_facts__ansible_system=not_found", False),
            ("ansible_facts__ansible_system=not_found and ansible_facts__ansible_system=not_found", False),
            ("ansible_facts__ansible_system=Linux and ansible_facts__ansible_system=Linux \
                and ansible_facts__ansible_system=not_found", False)
        ]
    )
    def test_fact_search_with_and(self, v2, populate_ansible_facts, host_filter, expected_results):
        response = v2.hosts.get(host_filter=host_filter)
        if expected_results:
            assert self.find_hosts(response) == set(self.test_hosts)
        else:
            assert not self.find_hosts(response)

    @pytest.mark.mp_group('HostFactSearch', 'serial')
    @pytest.mark.parametrize('host_filter, expected_hosts',
        [
            ('name={0} or groups__name={1} or ansible_facts__ansible_system=Linux'.format(host_a_name, group_a_name),
             [host_a_name, host_aa_name, host_b_name, host_dup_name]),
            ('name={0} or groups__name={1} or ansible_facts__ansible_system=not_found'
             .format(host_a_name, group_a_name), [host_a_name, host_dup_name]),
            ('name={} or groups__name=not_found or ansible_facts__ansible_system=not_found'.format(host_a_name),
             [host_a_name]),
            ('name=not_found or groups__name=not_found or ansible_facts__ansible_system=not_found', []),
            ('name={0} and groups__name={1} and ansible_facts__ansible_system=Linux'.format(host_a_name, group_a_name),
             [host_a_name]),
            ('name={0} and groups__name={1} and ansible_facts__ansible_system=not_found'
             .format(host_a_name, group_a_name), []),
            ('name={} and groups__name=not_found and ansible_facts__ansible_system=not_found'.format(host_a_name), []),
            ('name=not_found and groups__name=not_found and ansible_facts__ansible_system=not_found', []),
        ]
    )
    def test_basic_hyrid_search(self, v2, populate_ansible_facts, host_filter, expected_hosts):
        response = v2.hosts.get(host_filter=host_filter, page_size=200)
        assert self.find_hosts(response) == set(expected_hosts)

    @pytest.mark.mp_group('HostFactSearch', 'serial')
    @pytest.mark.parametrize('host_filter, expected_hosts',
        [
            ('name={0} or (groups__name={1} and ansible_facts__ansible_system=not_found)'
             .format(host_a_name, group_aa_name), [host_a_name]),
            ('name={} or (groups__name=not_found and ansible_facts__ansible_system=Linux)'.format(host_a_name),
             [host_a_name]),
            ('name=not_found or (groups__name={} and ansible_facts__ansible_system=Linux)'.format(group_aa_name),
             [host_aa_name, host_dup_name]),
            ('(name={0} or groups__name={1}) and ansible_facts__ansible_system=not_found'
             .format(host_a_name, group_aa_name), []),
            ('(name={} or groups__name=not_found) and ansible_facts__ansible_system=Linux'.format(host_a_name),
             [host_a_name]),
            ('(name=not_found or groups__name={}) and ansible_facts__ansible_system=Linux'.format(group_aa_name),
             [host_aa_name, host_dup_name]),
        ]
    )
    def test_advanced_hybrid_search(self, v2, populate_ansible_facts, host_filter, expected_hosts):
        response = v2.hosts.get(host_filter=host_filter, page_size=200)
        assert self.find_hosts(response) == set(expected_hosts)

    @pytest.mark.mp_group('HostSearch', 'serial')
    @pytest.mark.parametrize('host_filter',
        [
            ('name={0} or (groups__name={1} and ansible_facts__ansible_system=not_found)'
             .format(host_a_name, group_aa_name)),
            'name={} or (groups__name=not_found and ansible_facts__ansible_system=Linux)'.format(host_a_name),
            'name=not_found or (groups__name={} and ansible_facts__ansible_system=Linux)'.format(group_aa_name),
            ('(name={0} or groups__name={1}) and ansible_facts__ansible_system=not_found'
             .format(host_a_name, group_aa_name)),
            '(name={} or groups__name=not_found) and ansible_facts__ansible_system=Linux'.format(host_a_name),
            '(name=not_found or groups__name={}) and ansible_facts__ansible_system=Linux'.format(group_aa_name),
        ]
    )
    def test_smart_inventory(self, factories, v2, loaded_inventory, host_filter):
        """host_filter should determine a smart inventory's hosts."""
        inventory = factories.v2_inventory(organization=loaded_inventory.ds.organization, kind='smart',
                                           host_filter=host_filter)
        hosts = inventory.related.hosts.get()

        response = v2.hosts.get(host_filter=host_filter, page_size=200)
        assert self.find_hosts(response) == self.find_hosts(hosts)

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
