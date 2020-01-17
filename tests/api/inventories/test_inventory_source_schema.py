import json
from pprint import pformat

import pytest

from tests.api import APITest


def assert_expected_hostvars(inv_source,
    inv_update,
    inventory_hostvars,
    hostvars_that_create_groups,
    azure_bug
    ):
    """For given inventory source and inventory update, assert expected hostvars found on hosts.

    While looping over hostvars, generate any group names that we expect to be created based
    on the values of the hostvars.

    Return set of expected groups to be constructed.
    """
    kind = inv_source.source
    expected_hostvars = inventory_hostvars.get(kind, {})
    missing_hostvars = dict()
    hosts_missing_vars = dict()
    constructed_groups = set()
    hostvars_that_create_groups = hostvars_that_create_groups.get(kind, {})

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

    # Due to https://github.com/ansible/tower/issues/3584 where a change in API response
    # caused GCE to have no enabled hosts, we are going to make the very loose requirement
    # that at least one enabled host exists in any source
    num_enabled_hosts = 0

    for host in inv_update.related.inventory.get().related.hosts.get().results:
        num_enabled_hosts += 1 if host.enabled else 0
        if expected_hostvars or hostvars_that_create_groups:
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

    assert num_enabled_hosts > 0

    assert len(missing_hostvars) == 0, f'The {kind} inventory update failed to\n' \
        'provide the following keys in the hostvars of the listed hosts: \n' \
        f'{pformat(missing_hostvars)}\n' \
        'The hosts that were missing data have their complete hostvars listed here:\n'\
        f'{pformat(hosts_missing_vars)}\n'

    return constructed_groups


def assert_expected_hostgroups(inv_source, inv_update, inventory_hostgroups, constructed_groups):
    """For given inventory source and inventory update, assert expected groups were created."""
    kind = inv_source.source
    inventory = inv_source.related.inventory.get()
    expected_hostgroups = inventory_hostgroups.get(kind, {})
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



def assert_expected_hostnames(inv_source, hostvars_that_create_host_names):
    """For given inventory, assert expected host names were created."""
    kind = inv_source.source
    inventory = inv_source.related.inventory.get()
    expected_host_name_vars = hostvars_that_create_host_names.get(kind, [])

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


@pytest.mark.usefixtures('authtoken')
class TestInventorySourceSchema(APITest):

    @pytest.mark.ansible_integration
    def test_inventory_source_schema(self,
            ansible_version_cmp,
            inventory_with_known_schema,
            inventory_hostvars,
            inventory_hostgroups,
            hostvars_that_create_groups,
            hostvars_that_create_host_names
            ):
        """Verify successful inventory import using /api/v2/inventory_sources/N/update/."""
        inv_source = inventory_with_known_schema.related.inventory_sources.get().results.pop()
        # Test that we don't regress on https://github.com/ansible/awx/issues/4059
        assert inv_source.credential == inv_source.summary_fields.credential.id
        inv_update = inv_source.related.last_update.get()
        inv_update.assert_successful()
        # There is a bug with old imports https://github.com/ansible/awx/issues/3448
        # we have chosen to ignore it
        # In fact, have chosed to keep behavior in plugin
        # https://github.com/ansible/ansible/pull/54060
        azure_bug = True
        constructed_groups = assert_expected_hostvars(inv_source, inv_update, inventory_hostvars, hostvars_that_create_groups, azure_bug)
        # Issue that require this to be done: https://github.com/ansible/awx/issues/5219
        constructed_groups = (group for group in constructed_groups if ' ' not in group)
        assert_expected_hostgroups(inv_source, inv_update, inventory_hostgroups, constructed_groups)
        assert_expected_hostnames(inv_source, hostvars_that_create_host_names)
