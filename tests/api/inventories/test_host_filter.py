import types

from towerkit.utils import random_title, PseudoNamespace
import towerkit.exceptions
import fauxfactory
import pytest

from tests.api import APITest


@pytest.mark.api
@pytest.mark.usefixtures('authtoken', 'install_enterprise_license_unlimited')
class TestHostFilter(APITest):

    @pytest.fixture(scope='class')
    def inventory_item_names(self):
        random_suffix = 'xx' + random_title(2, False)
        namespace = PseudoNamespace()
        namespace.host_a_name = 'hostA{}'.format(random_suffix)
        namespace.host_aa_name = 'hostAA{}'.format(random_suffix)
        namespace.host_b_name = 'hostB{}'.format(random_suffix)
        namespace.host_dup_name = 'hostDup{}'.format(random_suffix)
        namespace.group_a_name = 'groupA{}'.format(random_suffix)
        namespace.group_aa_name = 'groupAA{}'.format(random_suffix)
        namespace.group_b_name = 'groupB{}'.format(random_suffix)
        return namespace

    @pytest.fixture(scope='class')
    def test_hosts(self, inventory_item_names):
        return [inventory_item_names.host_a_name, inventory_item_names.host_aa_name,
                inventory_item_names.host_b_name, inventory_item_names.host_dup_name]

    @pytest.fixture(scope='class')
    def items_from_item_list(self, inventory_item_names):
        def _items_from_item_list(item_list):
            return set([getattr(inventory_item_names, item) for item in item_list])
        return _items_from_item_list

    @pytest.fixture(scope='class')
    def find_hosts(self, inventory_item_names, test_hosts):
        def _find_hosts(response):
            # filter the stock localhost as well as any hosts resulting from incomplete test teardown
            return set([host.name for host in response.results if host.name in test_hosts])
        return _find_hosts

    @pytest.fixture(scope="class")
    def loaded_inventory(self, class_factories, inventory_item_names):
        inventory = class_factories.v2_inventory()

        groupA = class_factories.group(inventory=inventory, name=inventory_item_names.group_a_name)
        groupAA = class_factories.group(inventory=inventory, name=inventory_item_names.group_aa_name)
        groupB = class_factories.group(inventory=inventory, name=inventory_item_names.group_b_name)

        hostA = class_factories.host(inventory=inventory, name=inventory_item_names.host_a_name)
        hostAA = class_factories.host(inventory=inventory, name=inventory_item_names.host_aa_name)
        hostB = class_factories.host(inventory=inventory, name=inventory_item_names.host_b_name)
        hostDup = class_factories.host(inventory=inventory, name=inventory_item_names.host_dup_name)

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
        jt.launch().wait_until_completed().assert_successful()

    @pytest.mark.mp_group('HostSearch', 'serial')
    @pytest.mark.parametrize('host_filter, expected_hosts',
        [
            ('name={host_a_name}', ['host_a_name']),
            ('name=not_found', []),
            ('name={host_dup_name}', ['host_dup_name']),
        ]
    )
    def test_basic_host_search(self, v2, loaded_inventory, inventory_item_names, find_hosts, items_from_item_list,
                               host_filter, expected_hosts):
        response = v2.hosts.get(host_filter=host_filter.format(**inventory_item_names), page_size=200)
        assert find_hosts(response) == items_from_item_list(expected_hosts)

    @pytest.mark.mp_group('HostSearchOr', 'serial')
    @pytest.mark.parametrize('host_filter, expected_hosts',
        [
            ('name={host_a_name} or name={host_b_name}', ['host_a_name', 'host_b_name']),
            ('name={host_a_name} or name=not_found', ['host_a_name']),
            ('name=not_found or name=not_found', []),
            ('name={host_a_name} or name={host_a_name}', ['host_a_name']),
            ('name={host_dup_name} or name={host_dup_name}', ['host_dup_name']),
            ('name={host_a_name} or name={host_aa_name} or name=not_found', ['host_a_name', 'host_aa_name'])
        ]
    )
    def test_host_search_with_or(self, v2, loaded_inventory, inventory_item_names, find_hosts, items_from_item_list,
                                 host_filter, expected_hosts):
        response = v2.hosts.get(host_filter=host_filter.format(**inventory_item_names), page_size=200)
        assert find_hosts(response) == items_from_item_list(expected_hosts)

    @pytest.mark.mp_group('HostSearch', 'serial')
    @pytest.mark.parametrize('host_filter, expected_hosts',
        [
            ('name={host_a_name} and name={host_b_name}', []),
            ('name={host_a_name} and name={host_a_name}', ['host_a_name']),
            ('name=not_found and name=not_found', []),
            ('name={host_dup_name} and name={host_dup_name}', ['host_dup_name']),
            ('name={host_a_name} and name={host_b_name} and name=not_found', []),
        ]
    )
    def test_host_search_with_and(self, v2, loaded_inventory, inventory_item_names, find_hosts, items_from_item_list,
                                  host_filter, expected_hosts):
        response = v2.hosts.get(host_filter=host_filter.format(**inventory_item_names), page_size=200)
        assert find_hosts(response) == items_from_item_list(expected_hosts)

    @pytest.mark.mp_group('GroupSearch', 'serial')
    @pytest.mark.parametrize('host_filter, expected_hosts',
        [
            ('groups__name={group_a_name}', ['host_a_name', 'host_dup_name']),
            ('groups__name={group_aa_name}', ['host_aa_name', 'host_dup_name']),
            ('groups__name=not_found', []),
        ]
    )
    def test_basic_group_search(self, v2, loaded_inventory, inventory_item_names, find_hosts, items_from_item_list,
                                host_filter, expected_hosts):
        response = v2.hosts.get(host_filter=host_filter.format(**inventory_item_names), page_size=200)
        assert find_hosts(response) == items_from_item_list(expected_hosts)

    @pytest.mark.mp_group('GroupSearch', 'serial')
    @pytest.mark.parametrize('host_filter, expected_hosts',
        [
            ('groups__name={group_a_name} or groups__name={group_b_name}',
             ['host_a_name', 'host_b_name', 'host_dup_name']),
            ('groups__name={group_a_name} or groups__name=not_found', ['host_a_name', 'host_dup_name']),
            ('groups__name=not_found or groups__name=not_found', []),
            ('groups__name={group_a_name} or groups__name={group_a_name}', ['host_a_name', 'host_dup_name']),
            ('groups__name={group_a_name} or groups__name={group_aa_name} or groups__name=not_found',
             ['host_a_name', 'host_aa_name', 'host_dup_name'])
        ]
    )
    def test_group_search_with_or(self, v2, loaded_inventory, inventory_item_names, find_hosts, items_from_item_list,
                                  host_filter, expected_hosts):
        response = v2.hosts.get(host_filter=host_filter.format(**inventory_item_names), page_size=200)
        assert find_hosts(response) == items_from_item_list(expected_hosts)

    @pytest.mark.mp_group('GroupSearch', 'serial')
    @pytest.mark.parametrize('host_filter, expected_hosts',
        [
            ('groups__name={group_a_name} and groups__name={group_b_name}', ['host_dup_name']),
            ('groups__name={group_a_name} and groups__name={group_a_name}', ['host_a_name', 'host_dup_name']),
            ('groups__name=not_found and groups__name=not_found', []),
            ('groups__name={group_a_name} and groups__name={group_b_name} and groups__name=not_found', [])
        ]
    )
    def test_group_search_with_and(self, v2, loaded_inventory, inventory_item_names, find_hosts, items_from_item_list,
                                   host_filter, expected_hosts):
        response = v2.hosts.get(host_filter=host_filter.format(**inventory_item_names), page_size=200)
        assert find_hosts(response) == items_from_item_list(expected_hosts)

    @pytest.mark.mp_group('HostFactSearch', 'serial')
    @pytest.mark.github('https://github.com/ansible/tower/issues/702')
    @pytest.mark.parametrize('ansible_fact',
        [
            "ansible_python_version", # string
            "ansible_processor_cores", # integer
            "ansible_fips", # boolean
            # FIXME: add in a simple empty list query
            "ansible_default_ipv6" # empty dictionary
        ]
    )
    def test_dictionary_fact_search(self, v2, loaded_inventory, populate_ansible_facts, inventory_item_names,
                                    find_hosts, test_hosts, ansible_fact):
        host = loaded_inventory.related.hosts.get().results.pop()
        ansible_facts = host.related.ansible_facts.get()

        raw_value = getattr(ansible_facts, ansible_fact)
        expected_value = str(raw_value).lower() if isinstance(raw_value, types.BooleanType) else raw_value

        host_filter = "ansible_facts__{0}={1}".format(ansible_fact, expected_value)
        response = v2.hosts.get(host_filter=host_filter.format(**inventory_item_names), page_size=200)
        assert find_hosts(response) == test_hosts

    @pytest.mark.mp_group('HostFactSearch', 'serial')
    def test_list_fact_search(self, skip_if_openshift, v2, loaded_inventory, populate_ansible_facts, inventory_item_names,
                              find_hosts, test_hosts):
        host = loaded_inventory.related.hosts.get().results.pop()
        ansible_interfaces = host.related.ansible_facts.get().ansible_interfaces

        for item in ansible_interfaces:
            host_filter = "ansible_facts__ansible_interfaces[]={0}".format(item)
            response = v2.hosts.get(host_filter=host_filter.format(**inventory_item_names), page_size=200)
            assert find_hosts(response) == set(test_hosts)

    @pytest.mark.mp_group('HostFactSearch', 'serial')
    def test_nested_dictionary_fact_search(self, v2, loaded_inventory, populate_ansible_facts, inventory_item_names,
                                           find_hosts, test_hosts):
        host = loaded_inventory.related.hosts.get().results.pop()
        python_version = host.related.ansible_facts.get().ansible_python.version

        for item in python_version.items():
            host_filter = "ansible_facts__ansible_python__version__{0}={1}".format(item[0], item[1])
            response = v2.hosts.get(host_filter=host_filter.format(**inventory_item_names), page_size=200)
            assert find_hosts(response) == set(test_hosts)

    @pytest.mark.mp_group('HostFactSearch', 'serial')
    def test_nested_list_fact_search(self, v2, loaded_inventory, populate_ansible_facts, inventory_item_names,
                                     find_hosts, test_hosts):
        host = loaded_inventory.related.hosts.get().results.pop()
        version_info = host.related.ansible_facts.get().ansible_python.version_info

        for item in version_info:
            host_filter = "ansible_facts__ansible_python__version_info[]={0}".format(item)
            response = v2.hosts.get(host_filter=host_filter.format(**inventory_item_names), page_size=200)
            assert find_hosts(response) == set(test_hosts)

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
    def test_fact_search_with_or(self, v2, populate_ansible_facts, inventory_item_names, find_hosts, test_hosts,
                                 host_filter, expected_results):
        response = v2.hosts.get(host_filter=host_filter.format(**inventory_item_names))
        if expected_results:
            assert find_hosts(response) == set(test_hosts)
        else:
            assert not find_hosts(response)

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
    def test_fact_search_with_and(self, v2, populate_ansible_facts, inventory_item_names, find_hosts, test_hosts,
                                  host_filter, expected_results):
        response = v2.hosts.get(host_filter=host_filter.format(**inventory_item_names))
        if expected_results:
            assert find_hosts(response) == set(test_hosts)
        else:
            assert not find_hosts(response)

    @pytest.mark.mp_group('HostFactSearch', 'serial')
    @pytest.mark.parametrize('host_filter, expected_hosts',
        [
            ('name={host_a_name} or groups__name={group_a_name} or ansible_facts__ansible_system=Linux',
             ['host_a_name', 'host_aa_name', 'host_b_name', 'host_dup_name']),
            ('name={host_a_name} or groups__name={group_a_name} or ansible_facts__ansible_system=not_found',
             ['host_a_name', 'host_dup_name']),
            ('name={host_a_name} or groups__name=not_found or ansible_facts__ansible_system=not_found',
             ['host_a_name']),
            ('name={host_a_name} and groups__name={group_a_name} and ansible_facts__ansible_system=not_found', []),
            ('name={host_a_name} and groups__name=not_found and ansible_facts__ansible_system=not_found', []),
            ('name=not_found and groups__name=not_found and ansible_facts__ansible_system=not_found', []),
        ]
    )
    def test_basic_hyrid_search(self, v2, populate_ansible_facts, find_hosts, inventory_item_names,
                                items_from_item_list, host_filter, expected_hosts):
        response = v2.hosts.get(host_filter=host_filter.format(**inventory_item_names), page_size=200)
        assert find_hosts(response) == items_from_item_list(expected_hosts)

    @pytest.mark.mp_group('HostFactSearch', 'serial')
    @pytest.mark.parametrize('host_filter, expected_hosts',
        [
            ('name={host_a_name} or (groups__name={group_aa_name} and ansible_facts__ansible_system=not_found)',
             ['host_a_name']),
            ('name={host_a_name} or (groups__name=not_found and ansible_facts__ansible_system=Linux)', ['host_a_name']),
            ('name=not_found or (groups__name={group_aa_name} and ansible_facts__ansible_system=Linux)',
             ['host_aa_name', 'host_dup_name']),
            ('(name={host_a_name} or groups__name={group_aa_name}) and ansible_facts__ansible_system=not_found', []),
            ('(name={host_a_name} or groups__name=not_found) and ansible_facts__ansible_system=Linux', ['host_a_name']),
            ('(name=not_found or groups__name={group_aa_name}) and ansible_facts__ansible_system=Linux',
             ['host_aa_name', 'host_dup_name']),
        ]
    )
    def test_advanced_hybrid_search(self, v2, populate_ansible_facts, inventory_item_names, find_hosts,
                                    items_from_item_list, host_filter, expected_hosts):
        response = v2.hosts.get(host_filter=host_filter.format(**inventory_item_names), page_size=200)
        assert find_hosts(response) == items_from_item_list(expected_hosts)

    @pytest.mark.mp_group('HostSearch', 'serial')
    @pytest.mark.parametrize('host_filter',
        [
            'name={host_a_name} or (groups__name={group_aa_name} and ansible_facts__ansible_system=not_found)',
            'name={host_a_name} or (groups__name=not_found and ansible_facts__ansible_system=Linux)',
            'name=not_found or (groups__name={group_aa_name} and ansible_facts__ansible_system=Linux)',
            '(name={host_a_name} or groups__name={group_aa_name}) and ansible_facts__ansible_system=not_found',
            '(name={host_a_name} or groups__name=not_found) and ansible_facts__ansible_system=Linux',
            '(name=not_found or groups__name={group_aa_name}) and ansible_facts__ansible_system=Linux'
        ]
    )
    def test_smart_inventory(self, factories, v2, loaded_inventory, inventory_item_names, find_hosts,
                             items_from_item_list, host_filter):
        """host_filter should determine a smart inventory's hosts."""
        inventory = factories.v2_inventory(organization=loaded_inventory.ds.organization, kind='smart',
                                           host_filter=host_filter.format(**inventory_item_names))
        hosts = inventory.related.hosts.get()

        response = v2.hosts.get(host_filter=host_filter.format(**inventory_item_names), page_size=200)
        assert find_hosts(response) == find_hosts(hosts)

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

    def test_nested_list_password_search(self, v2):
        host_filters = ['created_by__password__icontains=pas3w3rd',
                        'search=foo or created_by__password__icontains=pas3w3rd',
                        'created_by__password__icontains=passw3rd or search=foo']
        for host_filter in host_filters:
            with pytest.raises(towerkit.exceptions.BadRequest) as e:
                v2.hosts.get(host_filter=host_filter, page_size=200)
            assert "Filtering on password is not allowed." in str(e)

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
