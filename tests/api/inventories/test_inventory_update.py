import json

from pprint import pformat

from towerkit.config import config
from dateutil.parser import parse
from towerkit.utils import load_json_or_yaml, poll_until
from towerkit import exceptions as exc
import pytest

from tests.api import APITest

# this will get us to whatever python3 is on the box,
# regarless of what distro it is
CUSTOM_VENVS = [
                {
                'name': 'python3_ansible_devel',
                'packages': 'psutil git+https://github.com/ansible/ansible@devel#egg=ansible_devel openstacksdk boto botocore requests>=2.18.4 google-auth>=1.3.0 openstacksdk azure>=2.0.0',
                'python_interpreter': 'python3'
                },
                ]


def assert_expected_hostvars(inv_source,
    inv_update,
    cloud_inventory_hostvars,
    cloud_hostvars_that_create_groups,
    azure_bug
    ):
    """For given inventory source and inventory update, assert expected hostvars found on hosts.

    While looping over hostvars, generate any group names that we expect to be created based
    on the values of the hostvars.

    Return set of expected groups to be constructed.
    """
    kind = inv_source.summary_fields.credential.kind
    expected_hostvars = cloud_inventory_hostvars.get(kind, {})
    missing_hostvars = dict()
    hosts_missing_vars = dict()
    constructed_groups = set()
    hostvars_that_create_groups = cloud_hostvars_that_create_groups.get(kind, {})

    def generate_dynamic_expected_groups(found_dict):
        for key in hostvars_that_create_groups:
            # We will return constructed groups that are created from hostvars
            if key in found_dict and found_dict.get(key):
                value = found_dict.get(key, '')
                if isinstance(value, dict):
                    for k, v in value.items():
                        constructed_groups.add(hostvars_that_create_groups[key](k))
                        constructed_groups.add(hostvars_that_create_groups[key](f'{k}_{v}'))

                elif isinstance(value, list):
                    for item in value:
                        if value:
                            constructed_groups.add(hostvars_that_create_groups[key](item))
                elif isinstance(value.split(','), list):
                    for item in value.split(','):
                        if value:
                            constructed_groups.add(hostvars_that_create_groups[key](item))
                else:
                    constructed_groups.add(hostvars_that_create_groups[key](value))

    def assert_keys(found_dict, expected_dict, parent_found_dict, host, parent_key=''):
        for key in expected_dict:
            if key not in found_dict:
                missing_hostvars[key] = missing_hostvars.get(key, set())
                missing_hostvars[key].add(host.name)
                hosts_missing_vars[host.name] = parent_found_dict
            if isinstance(expected_dict.get(key), dict):
                expected_subdict = expected_dict.get(key)
                found_subdict = found_dict.get(key, {})
                if parent_key:
                    parent_key = '{}:{}'.format(parent_key, key)
                assert_keys(found_subdict, expected_subdict, parent_found_dict, host, key)

    if expected_hostvars or hostvars_that_create_groups:
        for host in inv_update.related.inventory.get().related.hosts.get().results:
            hostvars = host.related.variable_data.get()
            # Need to turn into proper dictionary object to access with get()
            hostvars = json.loads(str(hostvars))
            generate_dynamic_expected_groups(hostvars)
            if host.name == 'demo-dj' and azure_bug:
                # There is a bug with old imports https://github.com/ansible/awx/issues/3448
                # we have chosen to ignore it
                continue
            else:
                assert_keys(hostvars, expected_hostvars, hostvars, host)

    assert len(missing_hostvars) == 0, f'The {kind} inventory update failed to\n' \
        'provide the following keys in the hostvars of the listed hosts: \n' \
        f'{pformat(missing_hostvars)}\n' \
        'The hosts that were missing data have their complete hostvars listed here:\n'\
        f'{pformat(hosts_missing_vars)}\n'

    return constructed_groups


def assert_expected_hostgroups(inv_source, inv_update, cloud_inventory_hostgroups, constructed_groups):
    """For given inventory source and inventory update, assert expected groups were created."""
    kind = inv_source.summary_fields.credential.kind
    inventory = inv_source.related.inventory.get()
    expected_hostgroups = cloud_inventory_hostgroups.get(kind, {})
    expected_hostgroups.update({k: '' for k in constructed_groups})
    missing_groups = set()

    def assert_groups(inventory, expected_dict, parent_key=''):
        for key in expected_dict:
            found_group = inv_source.get_related('groups', name__in=key).results
            found_group = found_group.pop() if found_group else None
            if not found_group or found_group.name != key:
                missing_groups.add(key)
            if key == 'ec2':
                # special attribute of aws_ec2 imports, all hosts should be a member
                assert found_group.get_related('hosts').count == inv_source.get_related('hosts').count
            if isinstance(expected_dict.get(key), dict):
                expected_subgroups = expected_dict.get(key)
                for subkey in expected_subgroups:
                    found_subgroup = found_group.get_related('children', name__in=subkey).results if found_group else None
                    if not found_subgroup or found_subgroup.pop().name != subkey:
                        missing_groups.add(f'{key}:{subkey}')

    if expected_hostgroups:
        assert_groups(inventory, expected_hostgroups)

    assert len(missing_groups) == 0, f'The {kind} inventory update failed to\n' \
        'provide the following groups: \n' \
        f'{pformat(missing_groups)}\n' \



def assert_expected_hostnames(inv_source, cloud_hostvars_that_create_host_names):
    """For given inventory, assert expected host names were created."""
    kind = inv_source.summary_fields.credential.kind
    inventory = inv_source.related.inventory.get()
    expected_host_name_vars = cloud_hostvars_that_create_host_names.get(kind, [])

    if expected_host_name_vars:
        for host in inventory.get_related('hosts', page_size=200).results:
            # https://github.com/ansible/awx/issues/3448
            if host.name == 'demo-dj':
                continue  # host and group name conflict, known to be broken
            for hostvar in expected_host_name_vars:
                if host.name == host.variables.get(hostvar, None):
                    break  # host passes
            else:
                raise AssertionError(
                    'Host {} name did not match vars {} in hostvars, values: {}, variables:\n{}'.format(
                        host.name, expected_host_name_vars,
                        [host.variables.get(v, None) for v in expected_host_name_vars],
                        json.dumps(host.variables, indent=2)
                    )
                )


@pytest.mark.api
@pytest.mark.destructive
@pytest.mark.usefixtures(
    'authtoken',
    'install_enterprise_license_unlimited',
    'skip_if_openshift',
    'shared_custom_venvs'
)
@pytest.mark.mp_group('CustomVirtualenv', 'isolated_serial')
@pytest.mark.fixture_args(venvs=CUSTOM_VENVS)
class TestInventoryUpdateWithVenvs(APITest):
    """Test inventory updates in the default as well as other venvs.

    This provides ability to test different versions of anisble side by side on
    the same Tower as well as test different versions of python.
    """
    ALL_VENVS = [{'name': 'default'}]
    ALL_VENVS.extend(CUSTOM_VENVS)
    @pytest.fixture(params=ALL_VENVS, ids=[venv.get('name', 'default') for venv in ALL_VENVS])
    def custom_venv_path(self, request, venv_path):
        if request.param['name'] != 'default':
            return venv_path(request.param['name'])
        else:
            return None

    @pytest.mark.custom_venvs
    @pytest.mark.ansible_integration
    def test_v2_update_inventory_source(self,
            ansible_version_cmp,
            cloud_inventory,
            custom_venv_path,
            cloud_inventory_hostvars,
            cloud_inventory_hostgroups,
            cloud_hostvars_that_create_groups,
            cloud_hostvars_that_create_host_names
            ):
        """Verify successful inventory import using /api/v2/inventory_sources/N/update/."""
        inv_source = cloud_inventory.related.inventory_sources.get().results.pop()
        # Set venv to use
        # Will use venvs defined in CUSTOM_VENVS as well as the default venv
        inv_source.custom_virtualenv = custom_venv_path
        kind = inv_source.summary_fields.credential.kind
        if kind == 'azure_rm':
            inv_source.source_vars = json.dumps({
                'group_by_location': True,
                'group_by_os_family': True,
                'group_by_resource_group': True,
                'group_by_security_group': True,
                'group_by_tag': True
                })
        inv_update = inv_source.update().wait_until_completed()
        inv_update.assert_successful()
        # Assert we used the right venv for the update
        if custom_venv_path:
            assert inv_update.custom_virtualenv == custom_venv_path
            assert custom_venv_path in inv_update.job_args
        # There is a bug with old imports https://github.com/ansible/awx/issues/3448
        # we have chosen to ignore it
        # TODO: when Azure_rm plugin is enabled, add this back in
        # azure_bug = True if ansible_version_cmp('2.8.0') < 1 else False
        azure_bug = True
        constructed_groups = assert_expected_hostvars(inv_source, inv_update, cloud_inventory_hostvars, cloud_hostvars_that_create_groups, azure_bug)
        assert_expected_hostgroups(inv_source, inv_update, cloud_inventory_hostgroups, constructed_groups)
        assert_expected_hostnames(inv_source, cloud_hostvars_that_create_host_names)


@pytest.mark.api
@pytest.mark.usefixtures(
    'authtoken',
    'install_enterprise_license_unlimited',
)
class TestInventoryUpdate(APITest):

    def test_v1_update_inventory_source(self, cloud_group):
        """Verify successful inventory import using /api/v1/inventory_sources/N/update/."""
        inv_source = cloud_group.get_related('inventory_source')
        inv_update = inv_source.update().wait_until_completed()
        inv_update.assert_successful()

    def test_v2_update_all_inventory_sources_with_functional_sources(self, factories):
        """Verify behavior when inventory has functional inventory sources."""
        inventory = factories.v2_inventory()
        azure_cred, aws_cred = [factories.v2_credential(kind=kind) for kind in ('azure_rm', 'aws')]
        azure_source = factories.v2_inventory_source(inventory=inventory, source='azure_rm', credential=azure_cred)
        ec2_source = factories.v2_inventory_source(inventory=inventory, source='ec2', credential=aws_cred)
        scm_source = factories.v2_inventory_source(inventory=inventory, source='scm',
                                                   source_path='inventories/inventory.ini')

        prelaunch = inventory.related.update_inventory_sources.get()
        assert dict(can_update=True, inventory_source=azure_source.id) in prelaunch
        assert dict(can_update=True, inventory_source=ec2_source.id) in prelaunch
        assert dict(can_update=True, inventory_source=scm_source.id) in prelaunch
        assert len(prelaunch.json) == 3

        postlaunch = inventory.related.update_inventory_sources.post()
        azure_update, ec2_update, scm_update = [source.wait_until_completed(timeout=240).related.last_update.get()
                                                for source in (azure_source, ec2_source, scm_source)]
        filtered_postlaunch = []
        for launched in postlaunch:
            filtered_postlaunch.append(dict(inventory_source=launched['inventory_source'],
                                            inventory_update=launched['inventory_update'],
                                            status=launched['status']))
        assert dict(inventory_source=azure_source.id, inventory_update=azure_update.id, status="started") in filtered_postlaunch
        assert dict(inventory_source=ec2_source.id, inventory_update=ec2_update.id, status="started") in filtered_postlaunch
        assert dict(inventory_source=scm_source.id, inventory_update=scm_update.id, status="started") in filtered_postlaunch
        assert len(postlaunch.json) == 3

        azure_update.assert_successful()
        ec2_update.assert_successful()
        scm_update.assert_successful()

    def test_v2_update_all_inventory_sources_with_semifunctional_sources(self, factories):
        """Verify behavior when inventory has an inventory source that is ready for update
        and one that is not.
        """
        inv_source1 = factories.v2_inventory_source()
        inv_source1.ds.inventory_script.delete()
        inventory = inv_source1.ds.inventory
        inv_source2 = factories.v2_inventory_source(inventory=inventory)

        prelaunch = inventory.related.update_inventory_sources.get()
        assert dict(can_update=False, inventory_source=inv_source1.id) in prelaunch
        assert dict(can_update=True, inventory_source=inv_source2.id) in prelaunch
        assert len(prelaunch.json) == 2

        postlaunch = inventory.related.update_inventory_sources.post()
        inv_update = inv_source2.wait_until_completed().related.last_update.get()
        for launched in postlaunch:
            if launched['inventory_source'] == inv_source1.id:
                assert launched['status'] == "Could not start because `can_update` returned False"
            elif launched['inventory_source'] == inv_source2.id:
                assert launched['status'] == "started"
                assert launched['inventory_update'] == inv_update.id
            else:
                pytest.fail('Found unexpected inventory source update: {}'.format(launched))
        assert len(postlaunch.json) == 2

        assert not inv_source1.last_updated
        inv_update.assert_successful()
        inv_source2.assert_successful()

    def test_v2_update_all_inventory_sources_with_nonfunctional_sources(self, factories):
        """Verify behavior when inventory has nonfunctional inventory sources."""
        inventory = factories.v2_inventory()
        inv_source1, inv_source2 = [factories.v2_inventory_source(inventory=inventory) for _ in range(2)]

        inv_source1.ds.inventory_script.delete()
        inv_source2.ds.inventory_script.delete()

        prelaunch = inventory.related.update_inventory_sources.get()
        assert dict(can_update=False, inventory_source=inv_source1.id) in prelaunch
        assert dict(can_update=False, inventory_source=inv_source2.id) in prelaunch
        assert len(prelaunch.json) == 2

        with pytest.raises(exc.BadRequest) as e:
            inventory.update_inventory_sources()
        assert dict(status='Could not start because `can_update` returned False', inventory_source=inv_source1.id) in e.value[1]
        assert dict(status='Could not start because `can_update` returned False', inventory_source=inv_source2.id) in e.value[1]
        assert len(e.value[1]) == 2

        assert not inv_source1.last_updated
        assert not inv_source2.last_updated

    def test_v2_update_duplicate_inventory_sources(self, factories):
        """Verify updating custom inventory sources under the same inventory with
        the same custom script."""
        inv_source1 = factories.v2_inventory_source()
        inventory = inv_source1.ds.inventory
        inv_source2 = factories.v2_inventory_source(inventory=inventory,
                                                    inventory_script=inv_source1.ds.inventory_script)

        inv_updates = inventory.update_inventory_sources(wait=True)

        for update in inv_updates:
            update.assert_successful()
        inv_source1.get().assert_successful()
        inv_source2.get().assert_successful()

    def test_v2_update_with_no_inventory_sources(self, factories):
        inventory = factories.v2_inventory()
        with pytest.raises(exc.BadRequest) as e:
            inventory.update_inventory_sources()
        assert e.value[1] == {'detail': 'No inventory sources to update.'}

    def _contents_same(self, *args):
        """Given list1 and list2 which are both lists of pages of API objects
        this asserts that both lists contain the same objects by name
        """
        assert len(args) > 1
        compare_list = []
        for arg in args:
            if isinstance(arg, (list, tuple)):
                # is a results list
                compare_list.append(set([item.name for item in arg]))
            elif hasattr(arg, 'results'):
                # is a page object
                compare_list.append(set(item.name for item in arg.results))
            else:
                # is a single object
                compare_list.append(set([arg.name]))
        for item in compare_list[1:]:
            assert item == compare_list[0]

    def test_empty_groups_child_of_all_group(self, v2, factories):
        shared_org = factories.organization()
        parent_inv = factories.inventory(organization=shared_org)
        custom_script = """#!/usr/bin/env python
# -*- coding: utf-8 -*-
import json
print(json.dumps({
    "_meta": {
        "hostvars": {
            "old_host": {}
        }
    },
    "ungrouped": {
        "hosts": ["old_host"]
    },
    "ghost": {
        "hosts": [],
        "vars": {
            "foobar": "hello_world"
        }
    },
    "ghost2": {
        "hosts": []
    },
    "all": {
        "children": ["ghost3"]
    }
}))"""
        inv_script = factories.v2_inventory_script(
            script=custom_script,
            organization=shared_org,
        )
        inv_source = factories.v2_inventory_source(
            inventory_script=inv_script,
            organization=shared_org,
            inventory=parent_inv
        )
        inv_source.update().wait_until_completed().assert_successful()
        groups = parent_inv.related.groups.get().results
        assert len(groups) == 3
        group_names = [group.name for group in groups]
        assert set(group_names) == set(['ghost', 'ghost2', 'ghost3'])

    @pytest.mark.yolo
    def test_update_with_overwrite_attempt_deadlock(self, v2, factories):
        """Update an inventory with multiple sources that update same groups and hosts.'

        In past, this could result in bad clobbering behavior or a database lock.
        See https://github.com/ansible/tower/issues/3212.
        """
        source_scripts = []
        inv_sources = []
        shared_org = factories.organization()
        shared_parent_inv = factories.inventory(organization=shared_org)
        custom_script = """#!/usr/bin/env python
# -*- coding: utf-8 -*-
import json
import uuid
unique_name = str(uuid.uuid4())
host_1 = 'host_{}'.format(unique_name)
host_2 = 'host_2_{}'.format(unique_name)
print(json.dumps({
'_meta': {'hostvars': {
    '{}'.format(host_1): {'name':'{}'.format(host_1)},
    '{}'.format(host_2): {'name':'{}'.format(host_2)},
    'all_have': {'name':'all_have'},
    'all_have2': {'name':'all_have2'},
    'all_have3': {'name':'all_have3'},
    }},
'ungrouped': {'hosts': ['groupless']},
'child_group': {'hosts': ['{}'.format(host_1), 'all_have']},
'child_group2': {'hosts': ['{}'.format(host_1), 'all_have2']},
'parent_group': {'hosts': ['{}'.format(host_2), 'all_have3'], 'children': ['child_group', 'child_group2']}
}))"""
        for i in range(3):
            inv_script = factories.v2_inventory_script(
                script=custom_script,
                organization=shared_org,
            )
            inv_source = factories.v2_inventory_source(
                overwrite=True,
                overwrite_vars=True,
                inventory_script=inv_script,
                organization=shared_org,
                inventory=shared_parent_inv
            )
            source_scripts.append(inv_script)
            inv_sources.append(inv_source)
            inv_source.update().wait_until_completed().assert_successful()
        shared_parent_inv = shared_parent_inv.get()
        assert shared_parent_inv.total_inventory_sources == 3, "Not all sources were added correctly from independently run updates"
        # Now try and update all inventories simultaneously
        # in the past would have run into database lock from race on shared groups and hosts
        updates = shared_parent_inv.related.update_inventory_sources.post()
        for update in updates:
            update_page = v2.inventory_updates.get(id=update['id']).results.pop()
            update_page.wait_until_completed().assert_successful()

        shared_parent_inv = shared_parent_inv.get()
        # Each has 2 unique hosts, which makes 6 hosts
        # Then the three invs all share 4 other hosts, all_have, all_have2, all_have3, and groupless
        assert shared_parent_inv.total_hosts == 10, 'Should have had 6 unique hosts and 4 shared hosts'
        assert shared_parent_inv.total_groups == 3, 'Should have had parent group, child_group, and child_group2'
        # make assertions about group membership
        groups = shared_parent_inv.related.groups.get().results
        for group in groups:
            assert group.name in ['child_group', 'child_group2', 'parent_group']
            hosts = group.related.hosts.get().results
            host_names = [host.name for host in hosts]
            assert len(hosts) == 4, 'Should have 3 unique hosts, one from each inventory, and one shared host'
            if group.name == 'child_group':
                assert 'all_have' in host_names
            if group.name == 'child_group2':
                assert 'all_have2' in host_names
            if group.name == 'parent_group':
                assert 'all_have3' in host_names
            for host in hosts:
                assert host.name == host.related.variable_data.get()['name']

    def test_update_with_overwrite_deletion(self, factories):
        """Verify inventory update with overwrite will not persist old stuff that it imported.
        * Memberships created within our script-spawned group should removed by a 2nd import.
        * Hosts, groups, and memberships created outside of our custom group should persist.
        """
        inv_script = factories.v2_inventory_script(script="""#!/usr/bin/env python
# -*- coding: utf-8 -*-
import json
print(json.dumps({
    '_meta': {'hostvars': {'host_1': {}, 'host_2': {}}},
    'ungrouped': {'hosts': ['will_remove_host']},
    'child_group': {'hosts': ['host_of_child']},
    'child_group2': {'hosts': ['host_of_child']},
    'not_child': {'hosts': ['host_of_not_child']},
    'switch1': {'hosts': ['host_switch1']},
    'switch2': {'hosts': ['host_switch2']},
    'parent_switch1': {'children': ['switch1']},
    'parent_switch2': {'children': ['switch2']},
    'will_remove_group': {'hosts': ['host_2']},
    'parent_group': {'hosts': ['host_1', 'host_2'], 'children': ['child_group', 'child_group2']}
}))""")
        inv_source = factories.v2_inventory_source(
            overwrite=True,
            inventory_script=inv_script
        )

        # update and load objects into in-memory dictionaries
        inv_source.update().wait_until_completed().assert_successful()
        groups = {}
        for group in inv_source.related.groups.get().results:
            groups[group.name] = group
        hosts = {}
        for host in inv_source.related.hosts.get().results:
            hosts[host.name] = host

        # make sure content was imported
        assert 'will_remove_host' in hosts
        assert 'will_remove_group' in groups
        self._contents_same(groups['switch1'].get_related('hosts'), hosts['host_switch1'])
        self._contents_same(groups['switch2'].get_related('hosts'), hosts['host_switch2'])
        self._contents_same(groups['parent_switch1'].get_related('children'), groups['switch1'])
        self._contents_same(groups['parent_switch2'].get_related('children'), groups['switch2'])
        self._contents_same(groups['parent_group'].get_related('hosts'), (hosts['host_1'], hosts['host_2']))
        self._contents_same(groups['parent_group'].get_related('children'), (groups['child_group'], groups['child_group2']))

        # manually add not_child to parent_group
        groups['parent_group'].add_group(groups['not_child'])
        # manually remove child group from parent_group
        groups['parent_group'].remove_group(groups['child_group'])

        # Change script to modify relationships
        # changes made:
        # - host_1 is removed from parent group (but still present in import)
        # - child_group2 is removed from parent group (but still present in import)
        # - switch1 and switch2 trade hosts
        # - child_switch1 and 2 trade child groups
        # - "will remove" host / group are removed
        inv_script.script = """#!/usr/bin/env python
# -*- coding: utf-8 -*-
import json
print(json.dumps({
    '_meta': {'hostvars': {'host_1': {}, 'host_2': {}}},
    'child_group': {'hosts': ['host_of_child']},
    'child_group2': {'hosts': ['host_of_child']},
    'not_child': {'hosts': ['host_of_not_child']},
    'switch1': {'hosts': ['host_switch2']},
    'switch2': {'hosts': ['host_switch1']},
    'parent_switch1': {'children': ['switch2']},
    'parent_switch2': {'children': ['switch1']},
    'parent_group': {'hosts': ['host_2'], 'children': ['child_group']}
}))"""

        # update and load objects into in-memory dictionaries, again
        inv_source.update().wait_until_completed().assert_successful()
        groups = {}
        for group in inv_source.related.groups.get().results:
            groups[group.name] = group
        hosts = {}
        for host in inv_source.related.hosts.get().results:
            hosts[host.name] = host

        # verify changes
        assert 'will_remove_host' not in hosts
        assert 'will_remove_group' not in groups
        self._contents_same(groups['switch1'].get_related('hosts'), hosts['host_switch2'])
        self._contents_same(groups['switch2'].get_related('hosts'), hosts['host_switch1'])
        self._contents_same(groups['parent_switch1'].get_related('children'), groups['switch2'])
        self._contents_same(groups['parent_switch2'].get_related('children'), groups['switch1'])
        self._contents_same(groups['parent_group'].get_related('hosts'), hosts['host_2'])  # should have removed host_1
        self._contents_same(groups['parent_group'].get_related('children'), groups['child_group'])

    def test_update_without_overwrite(self, factories):
        """Verify inventory update without overwrite.
        * Hosts and groups created within our script-spawned group should persist.
        * Hosts and groups created outside of our custom group should persist.
        """
        inv_source = factories.v2_inventory_source()
        inventory = inv_source.ds.inventory
        inv_source.update().wait_until_completed()
        spawned_group = inv_source.related.groups.get().results.pop()
        spawned_host_ids = [host.id for host in spawned_group.related.hosts.get().results]

        # associate group and host with script-spawned group
        included_group = factories.group(inventory=inventory)
        included_host = factories.host(inventory=inventory)
        spawned_group.add_group(included_group)
        for group in [spawned_group, included_group]:
            group.add_host(included_host)

        # create additional inventory resources
        excluded_group = factories.group(inventory=inventory)
        excluded_host, isolated_host = [factories.host(inventory=inventory) for _ in range(2)]
        excluded_group.add_host(excluded_host)

        inv_source.update().wait_until_completed().assert_successful()

        # verify our script-spawned group contents
        spawned_group_children = spawned_group.related.children.get()
        assert spawned_group_children.count == 1
        assert spawned_group_children.results.pop().id == included_group.id
        assert set(spawned_host_ids) | set([included_host.id]) == set([host.id for host in spawned_group.related.hosts.get().results])

        # verify that additional inventory resources persist
        for resource in [included_group, included_host, excluded_group, excluded_host, isolated_host]:
            resource.get()

        # verify associations between additional inventory resources
        included_group_hosts = included_group.related.hosts.get()
        assert included_group_hosts.count == 1
        assert included_host.id == included_group_hosts.results.pop().id

        excluded_group_hosts = excluded_group.related.hosts.get()
        assert excluded_group_hosts.count == 1
        assert excluded_host.id == excluded_group_hosts.results.pop().id

    def test_update_with_overwrite_vars(self, factories, ansible_version_cmp):
        """Verify manually inserted group and host variables get deleted when
        enabled. Final group and host variables should be those sourced from
        the script. Inventory variables should persist.
        """
        inv_source = factories.v2_inventory_source(overwrite_vars=True)
        inventory = inv_source.ds.inventory
        inv_source.update().wait_until_completed().assert_successful()
        custom_group = inv_source.related.groups.get().results.pop()

        inserted_variables = "{'overwrite_me': true}"
        for resource in [inventory, custom_group]:
            resource.variables = inserted_variables
        hosts = custom_group.related.hosts.get()
        for host in hosts.results:
            host.variables = inserted_variables

        inv_source.update().wait_until_completed().assert_successful()

        assert inventory.get().variables == load_json_or_yaml(inserted_variables)
        expected_vars = {'ansible_host': '127.0.0.1', 'ansible_connection': 'local'}
        if ansible_version_cmp('2.4.0') < 1:
            # ansible 2.4 doesn't set group variables
            # https://github.com/ansible/ansible/issues/30877
            assert custom_group.get().variables == expected_vars
        for host in hosts.results:
            assert set(host.get().variables[custom_group.name]['hosts']) == set([host.name for host in hosts.results])
            assert host.variables[custom_group.name]['vars'] == expected_vars

    def test_update_without_overwrite_vars(self, factories, ansible_version_cmp):
        """Verify manually inserted group and host variables persist when disabled. Final
        group and host variables should be a union of those sourced from the inventory
        script and those manually inserted. Inventory variables should persist.
        """
        inv_source = factories.v2_inventory_source()
        inventory = inv_source.ds.inventory
        inv_source.update().wait_until_completed().assert_successful()
        custom_group = inv_source.related.groups.get().results.pop()

        inserted_variables = "{'overwrite_me': false}"
        for resource in [inventory, custom_group]:
            resource.variables = inserted_variables
        hosts = custom_group.related.hosts.get()
        for host in hosts.results:
            host.variables = inserted_variables

        inv_source.update().wait_until_completed().assert_successful()

        assert inventory.get().variables == load_json_or_yaml(inserted_variables)
        expected_vars = {'overwrite_me': False, 'ansible_host': '127.0.0.1', 'ansible_connection': 'local'}
        if ansible_version_cmp('2.4.0') < 1:
            # ansible 2.4 doesn't set group variables
            # https://github.com/ansible/ansible/issues/30877
            assert custom_group.get().variables == expected_vars
        for host in hosts.results:
            assert host.get().variables['overwrite_me'] is False
            assert set(host.variables[custom_group.name]['hosts']) == set([host.name for host in hosts.results])
            # update once https://github.com/ansible/ansible/issues/30877 lands
            # assert host.variables[custom_group.name]['vars'] == expected_vars
            assert host.variables[custom_group.name]['vars'] == {'ansible_host': '127.0.0.1', 'ansible_connection': 'local'}

    @pytest.mark.yolo
    @pytest.mark.ansible_integration
    def test_update_with_stdout_injection(self, factories, ansible_version_cmp):
        """Verify that we can inject text to update stdout through our script."""
        if ansible_version_cmp('2.4.0') >= 1 and ansible_version_cmp('2.5.1') < 1:
            # this doesn't work with ansible-inventory from 2.4 through 2.5.1
            pytest.skip('https://github.com/ansible/ansible/issues/33776')
        inv_script = factories.v2_inventory_script(script=("#!/usr/bin/env python\n"
                                                           "from __future__ import print_function\nimport sys\n"
                                                           "print('TEST', file=sys.stderr)\nprint('{}')"))
        inv_source = factories.v2_inventory_source(inventory_script=inv_script)

        inv_update = inv_source.update().wait_until_completed()
        inv_update.assert_successful()
        assert "TEST" in inv_update.result_stdout

    def test_update_with_custom_credential(self, factories, ansible_version_cmp):
        if ansible_version_cmp('2.4.0') >= 1 and ansible_version_cmp('2.5.1') < 1:
            # this doesn't work with ansible-inventory from 2.4 through 2.5.1
            pytest.skip('https://github.com/ansible/ansible/issues/33776')
        org = factories.organization()
        inv = factories.v2_inventory(organization=org)
        credential_type = factories.credential_type(
            inputs={
                'fields': [{
                    'id': 'password',
                    'type': 'string',
                    'label': 'Password',
                    'secret': True
                }]
            },
            injectors={
                'file': {'template': '[secrets]\npassword={{ password }}'},
                'env': {'AWX_CUSTOM_INI': '{{ tower.filename }}'}
            }
        )
        inv_script = factories.v2_inventory_script(
            organization=org,
            script=("#!/usr/bin/env python\n"
                    "from __future__ import print_function\nimport os, sys\n"
                    "print(open(os.environ['AWX_CUSTOM_INI']).read(), file=sys.stderr)\nprint('{}')")
        )
        inv_source = factories.v2_inventory_source(
            inventory=inv,
            inventory_script=inv_script,
            credential=factories.v2_credential(
                credential_type=credential_type,
                inputs={'password': 'SECRET123'}
            ),
            verbosity=2
        )
        inv_update = inv_source.update().wait_until_completed()
        assert 'password=SECRET123' in inv_update.result_stdout

    @pytest.mark.parametrize('verbosity, stdout_lines',
                             [(0, ['Re-calling script for hostvars individually.']),
                              (1, ['Loaded 1 groups, 5 hosts',
                                   'Inventory import completed']),
                              (2, ['Reading Ansible inventory source',
                                   'Finished loading from source',
                                   'Loaded 1 groups, 5 hosts',
                                   'Inventory variables unmodified',
                                   'Inventory import completed',
                                   'Adding host host_', ' to group group-',
                                   'Adding child group group-', ' to parent all'])],
                             ids=['0-warning', '1-info', '2-debug'])
    def test_update_verbosity(self, is_docker, ansible_version_cmp, factories, verbosity, stdout_lines):
        """Verify inventory source verbosity."""
        if is_docker and verbosity == 0:
            pytest.skip('Dev Container has debug logging so this test will likely fail')

        inv_source = factories.v2_inventory_source(verbosity=verbosity)
        inv_update = inv_source.update().wait_until_completed()

        inv_update.assert_successful()
        assert inv_update.verbosity == inv_source.verbosity
        if verbosity == 0 and ansible_version_cmp('2.4.0') >= 1:
            if (ansible_version_cmp('2.8.0') >= 1):
                for line in inv_update.result_stdout.split('\n'):
                    if 'ERROR' in line:
                        pass
                    else:
                        assert line == ''
            else:
                # https://github.com/ansible/awx/issues/792
                assert inv_update.result_stdout == ''
        else:
            for line in stdout_lines:
                assert line in inv_update.result_stdout

    def test_update_with_source_region(self, region_choices, cloud_group_supporting_source_regions):
        """Assess inventory imports with all possible choices for source_regions.

        Note: we expect inventory imports with certain regions to fail. For more context,
        please see https://github.com/ansible/ansible-tower/issues/545.
        """
        # provide list of values for source_regions given each provider
        cloud_provider = cloud_group_supporting_source_regions.get_related('inventory_source').get_related('credential').kind
        if cloud_provider == 'aws':
            source_regions = region_choices['ec2']
        elif cloud_provider == 'azure_rm':
            source_regions = region_choices['azure']
        elif cloud_provider == 'gce':
            source_regions = region_choices['gce']
        else:
            raise NotImplementedError("Unexpected cloud_provider: %s." % cloud_provider)
        unsupported_source_regions = ['cn-north-1', 'us-gov-west-1', 'LON']

        for source_region in source_regions:
            # patch inv_source_pg and launch update
            inv_source_pg = cloud_group_supporting_source_regions.get_related('inventory_source')
            inv_source_pg.patch(source_regions=source_region)
            assert inv_source_pg.source_regions.lower() == source_region.lower(), \
                "Unexpected value for inv_source_pg.source_regions after patching the inv_source_pg with %s." % source_region
            update_pg = inv_source_pg.update().wait_until_completed()

            # assert that the update was successful if used with supported source region
            if source_region not in unsupported_source_regions:
                update_pg.assert_successful()
                inv_source_pg.get().assert_successful()

            # assert that update fails if used with unsupported source region
            else:
                assert update_pg.status == "failed", \
                    "inventory_update %s did not fail with unsupported region %s." % (update_pg, source_region)
                assert inv_source_pg.get().status == "failed", \
                    "An inventory_update failed, but the inventory_source did not fail - %s" % inv_source_pg

            # TODO: Assert specific cloud instance is now listed in group

    def test_update_with_populated_source_region(self, cloud_group_supporting_source_regions):
        """Tests that hosts are imported when applying source regions containing hosts.

        NOTE: test may fail if our expected test hosts are down.
        """
        # TODO: Once we populate all regions with an instance, don't think we'll need a test
        # tailored to a subset of regions with instances.

        # provide test source_region given each provider
        cloud_provider = cloud_group_supporting_source_regions.get_related('inventory_source').get_related('credential').kind
        if cloud_provider == 'aws':
            source_region = "us-east-1"
        elif cloud_provider == 'azure_rm':
            source_region = "eastus"
        elif cloud_provider == 'gce':
            source_region = "all"
        else:
            raise NotImplementedError("Unexpected cloud_provider: %s." % cloud_provider)

        # patch inv_source_pg
        inv_source_pg = cloud_group_supporting_source_regions.get_related('inventory_source')

        inv_source_pg.patch(source_regions=source_region)
        assert inv_source_pg.source_regions.lower() == source_region.lower(), \
            "Unexpected value for inv_source_pg.source_regions after patching the inv_source_pg with %s." % source_region

        # assert that the update was successful
        update_pg = inv_source_pg.update().wait_until_completed()
        update_pg.assert_successful()
        inv_source_pg.get().assert_successful()

        # assert that hosts were imported
        assert cloud_group_supporting_source_regions.ds.inventory.get().total_hosts > 0, \
            "Unexpected number of hosts returned %s." % cloud_group_supporting_source_regions.total_hosts

    @pytest.mark.ansible_integration
    def test_update_with_unpopulated_source_region(self, cloud_group_supporting_source_regions):
        """Tests that hosts are not imported when applying source regions not containing hosts.

        NOTE: test may fail if someone spins up an instance in one of these regions. Regions correspond as follow:
        * sa-east-1    => South America (Sao Paulo)
        * HKG          => Hong Kong
        * West_Japan   => Japan West
        * asia-east1-c => Asia East (C)
        """
        # TODO: Once we populate all regions with an instance, don't think we'll need a test
        # geared towards empty regions.

        # provide test source_region given each provider
        cloud_provider = cloud_group_supporting_source_regions.get_related('inventory_source').get_related('credential').kind
        if cloud_provider == 'aws':
            source_region = "sa-east-1"
        elif cloud_provider == 'azure_rm':
            source_region = "japanwest"
        elif cloud_provider == 'gce':
            source_region = "asia-east1-c"
        else:
            raise NotImplementedError("Unexpected cloud_provider: %s." % cloud_provider)

        # patch inv_source_pg
        inv_source_pg = cloud_group_supporting_source_regions.get_related('inventory_source')

        inv_source_pg.patch(source_regions=source_region)
        assert inv_source_pg.source_regions.lower() == source_region.lower(), \
            "Unexpected value for inv_source_pg.source_regions after patching the inv_source_pg with %s." % source_region

        # assert that the update was successful
        update_pg = inv_source_pg.update().wait_until_completed()
        update_pg.assert_successful()
        inv_source_pg.get().assert_successful()

        # assert that no hosts were imported
        assert cloud_group_supporting_source_regions.ds.inventory.get().total_hosts == 0, \
            "Unexpected number of hosts returned (%s != 0)." % cloud_group_supporting_source_regions.total_hosts

    @pytest.mark.parametrize("instance_filter", ["tag-key=Name", "key-name=jenkins", "tag:Name=*"])
    @pytest.mark.ansible_integration
    def test_update_with_matched_aws_instance_filter(self, factories, instance_filter, aws_credential):
        """Tests inventory imports with matched AWS instance filters. NOTE: test may fail
        if our expected test hosts are down.
        """
        aws_inventory_source = factories.v2_inventory_source(source='ec2', instance_filters=instance_filter, credential=aws_credential)
        update = aws_inventory_source.update().wait_until_completed()
        update.assert_successful()
        aws_inventory_source.get().assert_successful()

        assert aws_inventory_source.ds.inventory.related.hosts.get().count > 0

    @pytest.mark.parametrize("instance_filter", ["tag-key=UNMATCHED", "key-name=UNMATCHED", "tag:Name=UNMATCHED"])
    @pytest.mark.ansible_integration
    def test_update_with_unmatched_aws_instance_filter(self, aws_group, instance_filter):
        """Tests inventory imports with unmatched AWS instance filters

        NOTE: test may fail if someone spins up an unexpected instance.
        """
        # patch the inv_source_pg and launch the update
        inv_source_pg = aws_group.get_related('inventory_source')
        inv_source_pg.patch(instance_filters=instance_filter)
        update_pg = inv_source_pg.update().wait_until_completed()

        # assert that the update was successful
        update_pg.assert_successful()
        inv_source_pg.get().assert_successful()

        # assert whether hosts were imported
        assert aws_group.get().total_hosts == 0, "Unexpected number of hosts returned (%s != 0)." % aws_group.total_hosts

    @pytest.mark.ansible_integration
    @pytest.mark.parametrize("only_group_by, expected_group_names",
                             [("", ["accounts", "ec2", "images", "instance_states", "keys", "platforms", "regions",
                                    "security_groups", "tags", "types", "vpcs", "zones"],),
                              ("availability_zone", ["ec2", "zones"],),
                              ("ami_id", ["ec2", "images"],),
                              ("instance_id", ["ec2", "instances"],),
                              ("instance_type", ["ec2", "types"],),
                              ("key_pair", ["ec2", "keys"],),
                              ("region", ["ec2", "regions"],),
                              ("security_group", ["ec2", "security_groups"],),
                              ("availability_zone,ami_id", ["ec2", "zones", "images"],),
                              ("platform", ["ec2", "platforms"],)],
                             ids=['""', "availability_zone", "ami_id", "instance_id", "instance_type", "key_pair",
                                  "region", "security_group", "availability_zone,ami_id", "platform"])
    def test_aws_update_with_only_group_by(self, aws_group, only_group_by, expected_group_names):
        """Tests that expected groups are created when supplying value for only_group_by."""
        inv_source = aws_group.get_related('inventory_source')
        inv_source.compatibility_mode = True
        inv_source.group_by = only_group_by

        update = inv_source.update().wait_until_completed()
        update.assert_successful()
        inv_source.get().assert_successful()

        groups = aws_group.ds.inventory.related.root_groups.get()
        actual_group_names = set([group.name for group in groups.results if group.name != aws_group.name])
        # extra group name returned by the plugin
        if 'aws_ec2' in actual_group_names:
            actual_group_names.remove('aws_ec2')
        assert actual_group_names == set(expected_group_names)

        # confirm desired auth env vars are in update context
        assert 'AWS_ACCESS_KEY_ID' in update.job_env
        assert 'AWS_SECRET_ACCESS_KEY' in update.job_env

    @pytest.mark.ansible_integration
    @pytest.mark.parametrize("only_group_by", [None, 'location', 'os_family', 'resource_group', 'security_group'])
    def test_azure_update_with_only_group_by(self, factories, only_group_by):
        """Azure does not support group_by, but will apply options if given."""
        group_by_dict = {
            "group_by_resource_group": False,
            "group_by_location": False,
            "group_by_security_group": False,
            "group_by_tag": False,
            "group_by_os_family": False
        }
        if only_group_by:
            group_by_dict['group_by_{}'.format(only_group_by)] = True
        inv_source = factories.v2_inventory_source(
            source='azure_rm',
            credential=factories.credential(kind='azure_rm'),
            source_vars=json.dumps(group_by_dict)
        )

        update = inv_source.update().wait_until_completed()
        update.assert_successful()

        groups = inv_source.get_related('groups', parents__isnull=True).results  # root groups
        actual_group_names = set(group.name for group in groups)

        if only_group_by == 'location':
            actual_group_names.remove('azure')
            for group_name in actual_group_names:
                assert 'us' in group_name  # assuming all servers are in USA...
        elif only_group_by == 'os_family':
            assert actual_group_names == set(['azure', 'linux'])  # assuming no windows servers running
        elif only_group_by == 'resource_group':
            # potentially flaky if Azure resources are modified
            assert actual_group_names == set(['azure', 'demo-dj', 'mperz', 'qe'])  # Azure users could change
        elif only_group_by == 'security_group':
            actual_group_names.remove('azure')
            actual_group_names.remove('demo-dj')
            for group_name in actual_group_names:
                assert group_name.startswith('mperz') or group_name.startswith('towerqe')  # assuming no one else sets these up
        else:
            assert actual_group_names == set(['azure'])

    def test_azure_use_private_ip(self, factories, ansible_version_cmp):
        source_vars = {"use_private_ip": True}
        inv_source = factories.v2_inventory_source(
            source='azure_rm',
            credential=factories.credential(kind='azure_rm'),
            source_vars=json.dumps(source_vars)
        )

        update = inv_source.update().wait_until_completed()
        update.assert_successful()

        host_results = inv_source.get_related('hosts')
        assert host_results.count > 0  # this did an unfiltered import, so this should not fail
        for host in host_results.results:
            if (ansible_version_cmp('2.8.0') < 1) and host.name == 'demo-dj':
                # Fix for bug was merged into 2.8 https://github.com/ansible/ansible/pull/54099
                # Bug in previous ansible versions caused host with same name as group to have hostvars stolen
                continue
            hostvars = host.variables
            priv_ip = hostvars.get('private_ip', 'NO KEY private_ip FOUND')
            ansible_host = hostvars.get('ansible_host', 'NO KEY ansible_host FOUND')
            # normally this is the public IP, not the private IP
            assert priv_ip == ansible_host, 'private_ip and ansible host do not match!\n' \
                f'the source var to customize the anisble host was not respected! {priv_ip} != {ansible_host}\n' \
                f' All host vars were as follows {pformat(hostvars)}'

    def test_azure_use_resource_group_filters(self, skip_if_pre_ansible28, factories, ansible_version_cmp):
        # Fix for bug was merged into 2.8 https://github.com/ansible/ansible/pull/54099
        # Bug in previous ansible versions caused host with same name as group to have hostvars stolen
        res_group = "demo-dj"
        source_vars = {"resource_groups": res_group}
        inv_source = factories.v2_inventory_source(
            source='azure_rm',
            credential=factories.credential(kind='azure_rm'),
            source_vars=json.dumps(source_vars)
        )

        update = inv_source.update().wait_until_completed()
        update.assert_successful()

        host_results = inv_source.get_related('hosts')
        assert host_results.count > 0  # test could be failing because account changed content
        for host in host_results.results:
            hostvars = host.variables
            found_res_group = hostvars.get('resource_group', 'NO KEY resource_group FOUND')
            assert found_res_group == res_group, f'Resource group {res_group} not found, only found \n {found_res_group}. All hostvars found were {pformat(hostvars)}'

    @pytest.mark.ansible_integration
    def test_aws_replace_dash_in_groups_source_variable(self, factories):
        """Tests that AWS inventory groups will be registered with underscores instead of hyphens
        when using "replace_dash_in_groups" source variable
        """
        inv_source = factories.v2_inventory_source(
            source='ec2',
            source_regions='us-east-1',  # region where the flag is located, to reduce import size
            group_by='tag_keys',  # assure the tag groups are returned in all cases
            credential=factories.v2_credential(kind='aws'),
            source_vars=json.dumps(dict(replace_dash_in_groups=True))
        )

        # Update and assert that the inventory_update is marked as successful
        inv_update = inv_source.update().wait_until_completed()
        inv_update.assert_successful()

        # Assert that hyphen containing tag groups are registered with underscores
        flag_like_group_names = set(
            group.name for group in inv_source.get_related('groups', name__icontains='flag').results
        )
        assert flag_like_group_names, 'Inventory update produced no group corresponding to expected tag'
        for group_name in ['tag_Test_Flag_2202', 'tag_Test_Flag_2202_Replace_Dash_In_Groups']:
            assert group_name in flag_like_group_names, (
                'An inventory sync was launched with "replace_dash_in_groups: true", '
                'but desired group with sanitized tag "{0}" not found.'.format(group_name))

    @pytest.mark.ansible_integration
    @pytest.mark.parametrize('timeout, status, job_explanation', [
        (0, 'successful', ''),
        (60, 'successful', ''),
        (1, 'failed', 'Job terminated due to timeout'),
    ], ids=['no timeout', 'under timeout', 'over timeout'])
    def test_update_with_timeout(self, custom_inventory_source, timeout, status, job_explanation):
        """Tests inventory updates with timeouts."""
        custom_inventory_source.patch(timeout=timeout)

        # launch inventory update and assess spawned update
        update_pg = custom_inventory_source.update().wait_until_completed()
        assert update_pg.status == status, \
            "Unexpected inventory update status. Expected '{0}' but received '{1}.'".format(status, update_pg.status)
        assert update_pg.job_explanation == job_explanation, \
            "Unexpected update job_explanation. Expected '{0}' but received '{1}.'".format(job_explanation, update_pg.job_explanation)
        assert update_pg.timeout == custom_inventory_source.timeout, \
            "Update_pg has a different timeout value ({0}) than its inv_source ({1}).".format(update_pg.timeout, custom_inventory_source.timeout)

    @pytest.mark.parametrize('inventory_source', ['azure_rm', None], ids=['azure', 'custom'])
    def test_environment_variables_sourced_with_inventory_update_with_azure_credential(self, factories, inventory_source):
        azure_cred = factories.v2_credential(kind='azure_rm', client='SomeClient', cloud_environment='SomeCloudEnvironment',
                                             password='SomePassword', secret='SomeSecret', subscription='SomeSubscription',
                                             tenant='SomeTenant', username='SomeUsername')
        if inventory_source:
            azure = factories.v2_inventory_source(credential=azure_cred, inventory_source=inventory_source)
        else:
            # custom inventory script created when no inventory_source specified
            azure = factories.v2_inventory_source(credential=azure_cred)
        update = azure.update().wait_until_completed()
        job_env = update.job_env
        assert job_env.AZURE_CLIENT_ID == 'SomeClient'
        assert job_env.AZURE_CLOUD_ENVIRONMENT == 'SomeCloudEnvironment'
        assert job_env.AZURE_SECRET == '**********'
        assert job_env.AZURE_SUBSCRIPTION_ID == 'SomeSubscription'
        assert job_env.AZURE_TENANT == 'SomeTenant'

    @pytest.mark.parametrize('source, cred_type', {
        'cloudforms': 'Red Hat CloudForms',
        'rhv': 'Red Hat Virtualization',
        'satellite6': 'Red Hat Satellite 6',
        'vmware': 'VMware vCenter',
    }.items())
    def test_config_parser_properly_escapes_special_characters_in_passwords(self, v2, factories, source, cred_type):
        cred_type = v2.credential_types.get(managed_by_tower=True, name=cred_type).results.pop()
        cred = factories.v2_credential(
            credential_type=cred_type,
            inputs={'host': 'http://example.org', 'username': 'xyz', 'password': 'pass%word'}
        )
        source = factories.v2_inventory_source(source=source, credential=cred)
        inv_update = source.update().wait_until_completed()
        assert 'ERROR! No inventory was parsed, please check your configuration and options' in inv_update.result_stdout
        assert 'SyntaxError' not in inv_update.result_stdout

    # Skip for Openshift because of Github Issue: https://github.com/ansible/tower-qa/issues/2591
    def test_inventory_events_are_inserted_in_the_background(self, factories):
        aws_cred = factories.v2_credential(kind='aws')
        ec2_source = factories.v2_inventory_source(source='ec2', credential=aws_cred)
        inv_update = ec2_source.update().wait_until_completed()

        # the first few events should be created/inserted *after* the job
        # created date and _before_ the job's finished date; this means that
        # events are being asynchronously inserted into the database _while_
        # the job is in "running" state
        events = inv_update.related.events.get(order='id').results
        assert len(events) > 0, "Problem with fixture, AWS inventory update did not produce any events"
        '''
        Check for correctness, events should only be created after the job is created.
        '''
        assert all(parse(event.created) > parse(inv_update.created) for event in events)

        '''
        Ensure there is at least 1 event that is saved before the job finishes.
        Note: This isn't gauranteed, but we are pretty sure we can find at least 1 event.
        '''
        assert any(parse(event.created) < parse(inv_update.finished) for event in events)

    def test_inventory_events_are_searchable(self, factories):
        aws_cred = factories.v2_credential(kind='aws')
        ec2_source = factories.v2_inventory_source(source='ec2', credential=aws_cred)
        inv_update = ec2_source.update().wait_until_completed()
        assert inv_update.related.events.get().count > 0
        assert inv_update.related.events.get(search='Updating inventory').count > 0
        assert inv_update.related.events.get(search='SOME RANDOM STRING THAT IS NOT PRESENT').count == 0

    @pytest.mark.ansible_integration
    def test_inventory_hosts_cannot_be_deleted_during_sync(self, factories):
        aws_cred = factories.v2_credential(kind='aws')
        aws_inventory_source = factories.v2_inventory_source(source='ec2', credential=aws_cred, verbosity=2)

        inv_update = aws_inventory_source.update().wait_until_completed()
        inv_update.assert_successful()

        inv_update = aws_inventory_source.update()
        poll_until(
            lambda: inv_update.get().status == 'running',
            interval=1,
            timeout=15
        )

        hosts = aws_inventory_source.ds.inventory.related.hosts.get()
        host = hosts.results.pop()
        with pytest.raises(exc.Conflict):
            host.delete()

    def test_tower_inventory_sync_success(self, factories):
        target_host = factories.v2_host()
        target_inventory = target_host.ds.inventory
        tower_cred = factories.v2_credential(
            kind='tower',
            inputs={
                'host': config.base_url,
                'username': config.credentials.users.admin.username,
                'password': config.credentials.users.admin.password,
                'verify_ssl': False
            }
        )
        tower_source = factories.v2_inventory_source(
            source='tower', credential=tower_cred,
            instance_filters=target_inventory.id
        )
        inv_update = tower_source.update().wait_until_completed()
        inv_update.assert_successful()
        assert 'Loaded 0 groups, 1 hosts' in inv_update.result_stdout

        loaded_hosts = tower_source.ds.inventory.related.hosts.get()
        assert loaded_hosts.count == 1
        assert loaded_hosts.results[0].name == target_host.name

    def test_tower_inventory_incorrect_password(self, ansible_version_cmp, factories):
        tower_cred = factories.v2_credential(
            kind='tower',
            inputs={
                'host': config.base_url,
                'username': config.credentials.users.admin.username,
                'password': 'INVALID!',
                'verify_ssl': False
            }
        )
        tower_source = factories.v2_inventory_source(
            source='tower', credential=tower_cred,
            instance_filters='123',
        )
        inv_update = tower_source.update().wait_until_completed()
        assert inv_update.status == 'failed'
        if ansible_version_cmp('2.8.0') >= 1:
            inv_update.assert_text_in_stdout('HTTP Error 401: Unauthorized')
        else:
            inv_update.assert_text_in_stdout('Failed to validate the license')

    @pytest.mark.parametrize('hostname, error', [
        ['https://###/', ('Invalid URL', 'error no host given')],
        ['example.org', ('Failed to validate the license', 'HTTP Error 404')],
    ])
    def test_tower_inventory_sync_failure_has_descriptive_error_message(self, ansible_version_cmp, factories, hostname, error):
        if ansible_version_cmp('2.8.0') >= 1:
            error = error[1]
        else:
            error = error[0]
        tower_cred = factories.v2_credential(kind='tower', inputs={
            'host': hostname,
            'username': 'x',
            'password': 'y'
        })
        tower_source = factories.v2_inventory_source(
            source='tower', credential=tower_cred,
            instance_filters='123'
        )
        inv_update = tower_source.update().wait_until_completed()
        assert inv_update.status == 'failed'
        inv_update.assert_text_in_stdout(error)
