import json
import pytest
import fauxfactory
import qe.exceptions
from tests.api import Base_Api_Test


# Ansible inventory variations for testing 'root' group removal
root_variations = [
    dict(name='children:0, hosts:0',
         inventory='''
[usa] # <------- DELETE
[fr]
fr-host-1
fr-host-2
[uk]
uk-host-1
[de]
'''),
    dict(name='children:m, hosts:0',
         inventory='''
[usa] # <------- DELETE
[usa:children]
ca
pa
nc
[fr]
fr-host-1
fr-host-2
[uk]
uk-host-1
[de]
'''),
    dict(name='children:0, hosts:n',
         inventory='''
[usa] # <------- DELETE
usa-host-1
usa-host-2
usa-host-3
[fr]
fr-host-1
fr-host-2
[uk]
uk-host-1
[de]
'''),
    dict(name='children:m, hosts:n',
         inventory='''
[usa] # <------- DELETE
usa-host-1
usa-host-2
usa-host-3
[usa:children]
ca
pa
nc
[pa]
philadelphia
pittsburgh
erie
[fr]
fr-host-1
fr-host-2
[uk]
uk-host-1
[de]
'''),
]


@pytest.fixture(scope="function", params=root_variations)
def root_variation(request, authtoken, inventory, ansible_runner):
    contacted = ansible_runner.copy(
        dest='/tmp/inventory.ini',
        force=True, mode='0644',
        content='''# --inventory-id %s %s''' % (inventory.id, request.param['inventory'])
    )
    for results in contacted.values():
        assert results['changed'] and 'failed' not in results, "Failed to create inventory file: %s" % results

    contacted = ansible_runner.shell(
        "awx-manage inventory_import --overwrite --inventory-id %s "
        "--source /tmp/inventory.ini" % inventory.id
    )
    for results in contacted.values():
        assert results['rc'] == 0, "awx-managed inventory_import failed: %s" % results

    # Re-GET the resource to populate host/group information
    inventory = inventory.get()
    assert inventory.get_related('groups').count > 0
    assert inventory.get_related('hosts').count > 0
    return inventory


# Ansible inventory variations for testing 'non-root' group removal.  These are
# the same as root_variations ... but they are nested a level deeper.
inventory_prefix = '''
[continents]
content-host-1

[continents:children]
af # Africa
an # Antarctica
as # Asia
eu # Europe
na # North America
oc # Oceania
sa # South America

[na]
na-host-1
na-host-2
[na:children]
usa
can
grl
mex

[eu:children]
fr
uk
de
'''


non_root_variations = [dict(name=item['name'], inventory=inventory_prefix + item['inventory']) for item in root_variations]


@pytest.fixture(scope="function", params=non_root_variations)
def non_root_variation(request, authtoken, inventory, ansible_runner):
    contacted = ansible_runner.copy(
        dest='/tmp/inventory.ini',
        force=True, mode='0644',
        content='''# --inventory-id %s %s''' % (inventory.id, request.param['inventory'])
    )
    for results in contacted.values():
        assert results['changed'] and 'failed' not in results, \
            "Failed to create inventory file: %s" % \
            json.dumps(results, indent=2)

    contacted = ansible_runner.shell(
        "awx-manage inventory_import --overwrite --inventory-id %s "
        "--source /tmp/inventory.ini" % inventory.id
    )
    for results in contacted.values():
        assert results['rc'] == 0, "awx-managed inventory_import failed: %s" % \
            json.dumps(results, indent=2)

    # Re-GET the resource to populate host/group information
    inventory = inventory.get()
    assert inventory.get_related('groups').count > 0
    assert inventory.get_related('hosts').count > 0
    return inventory


all_variations = root_variations + non_root_variations


@pytest.fixture(scope="function", params=all_variations)
def variation(request, authtoken, inventory, ansible_runner):
    contacted = ansible_runner.copy(
        dest='/tmp/inventory.ini', force=True,
        content='''# --inventory-id %s %s''' % (inventory.id, request.param['inventory']))
    for results in contacted.values():
        assert results['changed'] and 'failed' not in results, "Failed to create inventory file: %s" % results

    contacted = ansible_runner.shell(
        "awx-manage inventory_import --overwrite --inventory-id %s "
        "--source /tmp/inventory.ini" % inventory.id
    )
    for results in contacted.values():
        assert results['rc'] == 0, "awx-managed inventory_import failed: %s" % results

    # Re-GET the resource to populate host/group information
    inventory = inventory.get()
    assert inventory.get_related('groups').count > 0
    assert inventory.get_related('hosts').count > 0
    return inventory


@pytest.fixture(scope="function")
def another_inventory(request, authtoken, api_inventories_pg, organization):
    payload = dict(name="inventory-%s" % fauxfactory.gen_alphanumeric(),
                   description="Another random inventory - %s" % fauxfactory.gen_utf8(),
                   organization=organization.id,)
    obj = api_inventories_pg.post(payload)
    request.addfinalizer(obj.delete)
    return obj


@pytest.fixture(scope="function")
def some_group(request, authtoken, inventory):
    payload = dict(name="group-%s" % fauxfactory.gen_utf8(),
                   inventory=inventory.id,)
    obj = inventory.get_related('groups').post(payload)
    request.addfinalizer(obj.silent_delete)
    return obj


@pytest.mark.api
@pytest.mark.skip_selenium
@pytest.mark.destructive
class Test_Group(Base_Api_Test):
    '''
    Verify DELETE and POST (disassociate) behaves as expected for groups and their hosts

    Top-level group
        verify top-level group with children:0, hosts:0 -> group deleted
        verify top-level group with children:0, hosts:M -> group deleted, hosts promote to parent
        verify top-level group with children:N, hosts:0 -> group deleted, children promote to parent
        verify top-level group with children:N, hosts:M -> group deleted, children and hosts promote to parent

    Child group
        verify child group with children:0, hosts:0 -> group deleted
        verify child group with children:0, hosts:M -> group deleted, hosts promote to parent
        verify child group with children:N, hosts:0 -> group deleted, children promote to parent
        verify child group with children:N, hosts:M -> group deleted, children and hosts promote to parent
    '''

    pytestmark = pytest.mark.usefixtures('authtoken', 'install_enterprise_license_unlimited')

    def test_disassociate_root_group(self, root_variation):
        '''verify behavior of disassociate of a top-level group.
           POST {id=N, disassociate=True} to /inventories/N/groups
        '''
        # For convenience, display the INI file
        root_variation.print_ini()

        # Locate top-level group
        assert root_variation.get_related('groups', name='usa').count == 1
        group = root_variation.get_related('groups', name='usa').results.pop()

        # record inventory data
        total_inv_groups = root_variation.get_related('groups').count
        total_inv_root_groups = root_variation.get_related('root_groups').count
        total_inv_hosts = root_variation.get_related('hosts').count
        # record group data
        total_group_children = group.get_related('children').count

        # disassociate top-level group
        payload = dict(id=group.id, disassociate=True)
        with pytest.raises(qe.exceptions.NoContent_Exception):
            # POST to /inventories/N/groups
            root_variation.get_related('groups').post(payload)

        # Verify top-level group deleted
        assert root_variation.get_related('root_groups', name=group.name).count == 0
        assert root_variation.get_related('groups', name=group.name).count == 0

        # Verify root_group count adjusts properly (one removed, and children promoted)
        assert root_variation.get_related('root_groups').count == total_inv_root_groups + total_group_children - 1

        # Verify group counts decremented properly
        assert root_variation.get_related('groups').count == total_inv_groups - 1

        # Verify no hosts were removed
        assert root_variation.get_related('hosts').count == total_inv_hosts

    @pytest.mark.github('https://github.com/ansible/ansible-tower/issues/3551')
    def test_disassociate_non_root_group(self, non_root_variation):
        '''verify behavior of disassociate of a child group
           POST {disassociate=True} /groups/N/children
        '''
        # For convenience, display the INI file
        non_root_variation.print_ini()

        # Locate parent and child group
        assert non_root_variation.get_related('groups', name='na').count == 1
        parent_group = non_root_variation.get_related('groups', name='na').results.pop()
        assert non_root_variation.get_related('groups', name='usa').count == 1
        group = non_root_variation.get_related('groups', name='usa').results.pop()

        # record inventory data
        total_inv_groups = non_root_variation.get_related('groups').count
        total_inv_root_groups = non_root_variation.get_related('root_groups').count
        total_inv_hosts = non_root_variation.get_related('hosts').count
        # record group data
        total_group_children = group.get_related('children').count
        total_group_hosts = group.get_related('hosts').count
        # record parent_group data
        total_parent_children = parent_group.get_related('children').count
        total_parent_hosts = parent_group.get_related('hosts').count

        # delete group, and promote it's children
        payload = dict(disassociate=True)
        with pytest.raises(qe.exceptions.NoContent_Exception):
            # 1) FIXME - disassociate all matching groups - /inventories/N/groups
            # Would need to add variations to verify the above scenario
            # non_root_variation.get_related('groups').post(payload)

            # 2) disassociate group from parent - /groups/N/children/
            # POST to /groups/N/children
            group.get_related('children').post(payload)

        # Verify group deleted
        assert non_root_variation.get_related('root_groups', name=group.name).count == 0
        assert non_root_variation.get_related('groups', name=group.name).count == 0

        # Verify root_group count stays the same
        assert non_root_variation.get_related('root_groups').count == total_inv_root_groups

        # Verify group counts decremented properly
        assert non_root_variation.get_related('groups').count == total_inv_groups - 1

        # Verify no hosts were removed
        assert non_root_variation.get_related('hosts').count == total_inv_hosts

        # Verify groups were promoted
        assert parent_group.get_related('children').count == total_parent_children + total_group_children - 1

        # Verify hosts were promoted
        assert parent_group.get_related('hosts').count == total_parent_hosts + total_group_hosts

    def test_delete(self, api_groups_pg, variation):
        '''verify behavior of group delete
           DELETE /groups/N
        '''
        # For convenience, display the INI file
        variation.print_ini()

        # Locate parent and child group
        assert variation.get_related('groups', name='usa').count == 1
        group = variation.get_related('groups', name='usa').results.pop()
        # If a child group, get the parent
        if not group.is_root_group:
            assert variation.get_related('groups', name='na').count == 1
            parent_group = variation.get_related('groups', name='na').results.pop()
        else:
            parent_group = None

        # Record before counts
        total_inv_groups = variation.get_related('groups').count
        total_matching_groups = variation.get_related('groups', name=group.name).count
        total_inv_root_groups = variation.get_related('root_groups').count
        total_matching_root_groups = variation.get_related('root_groups', name=group.name).count
        total_inv_hosts = variation.get_related('hosts').count
        total_group_children = group.get_related('children').count
        total_group_hosts = group.get_related('hosts').count
        total_group_all_hosts = group.get_related('all_hosts').count
        # FIXME - Count the number of children that exist *only* in this group
        total_exclusive_group_children = total_group_children  # NOQA
        # FIXME - Count the number of hosts that exist *only* in this group
        total_exclusive_group_hosts = total_group_hosts  # NOQA
        if parent_group is not None:
            total_parent_children = parent_group.get_related('children').count
            total_parent_hosts = parent_group.get_related('hosts').count
            total_parent_all_hosts = parent_group.get_related('all_hosts').count
            # FIXME - find all parents of this group
            # parents = []

        # DELETE the group
        group.delete()

        # Verify the group has been 'supa' deleted
        assert variation.get_related('root_groups', name=group.name).count == 0
        assert variation.get_related('groups', name=group.name).count == 0
        assert api_groups_pg.get(name=group.name, inventory=group.inventory).count == 0

        # Verify root_groups adjusts appropriately
        assert variation.get_related('root_groups').count == total_inv_root_groups - total_matching_root_groups

        # Verify total group counts decremented properly
        assert variation.get_related('groups').count == total_inv_groups - total_matching_groups - total_group_children

        # Verify exclusive hosts were removed
        assert variation.get_related('hosts').count == total_inv_hosts - total_group_all_hosts

        if parent_group:
            # Verify that a single child was removed from the parent group
            assert parent_group.get_related('children').count == total_parent_children - 1

            # Verify that the parent.hosts has not changed
            assert parent_group.get_related('hosts').count == total_parent_hosts

            # Verify that the parent.all_hosts has changed
            assert parent_group.get_related('all_hosts').count == total_parent_all_hosts - total_group_all_hosts

    def test_associate_with_root_group(self, non_root_variation):
        '''Verify expected behavior when disassociating a group from it's parent, thereby creating a root group.
           POST {id=M, disassociate=True} /groups/N/children
        '''

        # For convenience, display the INI file
        non_root_variation.print_ini()

        # Locate the source group
        assert non_root_variation.get_related('groups', name='usa').count == 1
        group = non_root_variation.get_related('groups', name='usa').results.pop()

        # Locate the parent_group (optional)
        if not group.is_root_group:
            assert non_root_variation.get_related('groups', name='na').count == 1
            parent_group = non_root_variation.get_related('groups', name='na').results.pop()
        else:
            parent_group = None

        # decord data on inventory
        total_inv_groups = non_root_variation.get_related('groups').count
        total_matching_groups = non_root_variation.get_related('groups', name=group.name).count  # NOQA
        total_inv_root_groups = non_root_variation.get_related('root_groups').count
        total_matching_root_groups = non_root_variation.get_related('root_groups', name=group.name).count  # NOQA
        total_inv_hosts = non_root_variation.get_related('hosts').count
        # record data on group
        total_group_children = group.get_related('children').count  # NOQA
        total_group_hosts = group.get_related('hosts').count  # NOQA
        total_group_all_hosts = group.get_related('all_hosts').count
        # record data on parent_group (optional)
        if parent_group is not None:
            total_parent_children = parent_group.get_related('children').count
            total_parent_hosts = parent_group.get_related('hosts').count
            total_parent_all_hosts = parent_group.get_related('all_hosts').count

        # To associate a root_group, dissociate the group from the parent_group
        payload = dict(id=group.id, disassociate=True)
        with pytest.raises(qe.exceptions.NoContent_Exception):
            parent_group.get_related('children').post(payload)

        # Verify root_groups adjusts appropriately
        assert non_root_variation.get_related('root_groups').count == total_inv_root_groups + 1

        # Verify total group counts haven't changed
        assert non_root_variation.get_related('groups').count == total_inv_groups

        # Verify host counts haven't changed
        assert non_root_variation.get_related('hosts').count == total_inv_hosts

        if parent_group:
            # Verify that a single child was removed from the parent group
            assert parent_group.get_related('children').count == total_parent_children - 1

            # Verify that the parent.hosts has not changed
            assert parent_group.get_related('hosts').count == total_parent_hosts

            # Verify that the parent.all_hosts has changed
            assert parent_group.get_related('all_hosts').count == total_parent_all_hosts - total_group_all_hosts

    def test_associate_with_non_root_group(self, root_variation):
        '''Verify expected behavior for a group association
           POST {id=N} /group/<new_parent>/children
        '''
        # For convenience, display the INI file
        root_variation.print_ini()

        # Locate the source group
        assert root_variation.get_related('groups', name='usa').count == 1
        group = root_variation.get_related('groups', name='usa').results.pop()

        # Locate the dest group
        assert root_variation.get_related('groups', name='de').count == 1
        dest_group = root_variation.get_related('groups', name='de').results.pop()

        # Locate the parent_group (optional)
        if not group.is_root_group:
            assert root_variation.get_related('groups', name='na').count == 1
            parent_group = root_variation.get_related('groups', name='na').results.pop()
        else:
            parent_group = None

        # decord data on inventory
        total_inv_groups = root_variation.get_related('groups').count
        total_matching_groups = root_variation.get_related('groups', name=group.name).count  # NOQA
        total_inv_root_groups = root_variation.get_related('root_groups').count
        total_matching_root_groups = root_variation.get_related('root_groups', name=group.name).count
        total_inv_hosts = root_variation.get_related('hosts').count
        # record data on group
        total_group_children = group.get_related('children').count  # NOQA
        total_group_hosts = group.get_related('hosts').count  # NOQA
        total_group_all_hosts = group.get_related('all_hosts').count
        # record data on dest_group
        total_dest_group_children = dest_group.get_related('children').count
        total_dest_group_hosts = dest_group.get_related('hosts').count
        total_dest_group_all_hosts = dest_group.get_related('all_hosts').count
        # record data on parent_group (optional)
        if parent_group is not None:
            total_parent_children = parent_group.get_related('children').count
            total_parent_hosts = parent_group.get_related('hosts').count
            total_parent_all_hosts = parent_group.get_related('all_hosts').count

        # Associate group with dest_group
        payload = dict(id=group.id)
        with pytest.raises(qe.exceptions.NoContent_Exception):
            dest_group.get_related('children').post(payload)

        # Verify root_groups adjusts appropriately
        assert root_variation.get_related('root_groups').count == total_inv_root_groups - total_matching_root_groups

        # Verify total group counts haven't changed
        assert root_variation.get_related('groups').count == total_inv_groups

        # Verify host counts haven't changed
        assert root_variation.get_related('hosts').count == total_inv_hosts

        # Verify that a single child was added to dest_group
        assert dest_group.get_related('children').count == total_dest_group_children + 1

        # Verify that the dest_group.hosts has not changed
        assert dest_group.get_related('hosts').count == total_dest_group_hosts

        # Verify that the parent.all_hosts has changed
        assert dest_group.get_related('all_hosts').count == total_dest_group_all_hosts + total_group_all_hosts

        if parent_group:
            # Verify that a the number of parent_group children is unchanged
            assert parent_group.get_related('children').count == total_parent_children

            # Verify that the parent.hosts has not changed
            assert parent_group.get_related('hosts').count == total_parent_hosts

            # Verify that the parent.all_hosts has changed
            assert parent_group.get_related('all_hosts').count == total_parent_all_hosts

    def test_reassociate_with_non_root_group(self, non_root_variation):
        '''Verify expected behavior for moving a group from one non-root-group to another
           POST {id=M} /groups/<new_parent>/children
           POST {id=M, disassociate=True} /groups/<old_parent>/children
        '''
        # For convenience, display the INI file
        non_root_variation.print_ini()

        # Locate the source group
        assert non_root_variation.get_related('groups', name='usa').count == 1
        group = non_root_variation.get_related('groups', name='usa').results.pop()

        # Locate the dest group
        assert non_root_variation.get_related('groups', name='de').count == 1
        dest_group = non_root_variation.get_related('groups', name='de').results.pop()

        # Locate the parent_group (optional)
        if not group.is_root_group:
            assert non_root_variation.get_related('groups', name='na').count == 1
            parent_group = non_root_variation.get_related('groups', name='na').results.pop()
        else:
            parent_group = None

        # decord data on inventory
        total_inv_groups = non_root_variation.get_related('groups').count
        total_matching_groups = non_root_variation.get_related('groups', name=group.name).count  # NOQA
        total_inv_root_groups = non_root_variation.get_related('root_groups').count
        total_matching_root_groups = non_root_variation.get_related('root_groups', name=group.name).count
        total_inv_hosts = non_root_variation.get_related('hosts').count
        # record data on group
        total_group_children = group.get_related('children').count  # NOQA
        total_group_hosts = group.get_related('hosts').count  # NOQA
        total_group_all_hosts = group.get_related('all_hosts').count
        # record data on dest_group
        total_dest_group_children = dest_group.get_related('children').count
        total_dest_group_hosts = dest_group.get_related('hosts').count
        total_dest_group_all_hosts = dest_group.get_related('all_hosts').count
        # record data on parent_group (optional)
        if parent_group is not None:
            total_parent_children = parent_group.get_related('children').count
            total_parent_hosts = parent_group.get_related('hosts').count
            total_parent_all_hosts = parent_group.get_related('all_hosts').count

        # Associate group with dest_group
        payload = dict(id=group.id)
        with pytest.raises(qe.exceptions.NoContent_Exception):
            dest_group.get_related('children').post(payload)

        # Disassociate group from parent_group
        if parent_group:
            payload = dict(id=group.id, disassociate=True)
            with pytest.raises(qe.exceptions.NoContent_Exception):
                parent_group.get_related('children').post(payload)

        # Verify root_groups adjusts appropriately
        assert non_root_variation.get_related('root_groups').count == total_inv_root_groups - total_matching_root_groups

        # Verify total group counts haven't changed
        assert non_root_variation.get_related('groups').count == total_inv_groups

        # Verify host counts haven't changed
        assert non_root_variation.get_related('hosts').count == total_inv_hosts

        # Verify that a single child was added to dest_group
        assert dest_group.get_related('children').count == total_dest_group_children + 1

        # Verify that the dest_group.hosts has not changed
        assert dest_group.get_related('hosts').count == total_dest_group_hosts

        # Verify that the parent.all_hosts has changed
        assert dest_group.get_related('all_hosts').count == total_dest_group_all_hosts + total_group_all_hosts

        if parent_group:
            # Verify that a single child was removed from the parent group
            assert parent_group.get_related('children').count == total_parent_children - 1

            # Verify that the parent.hosts has not changed
            assert parent_group.get_related('hosts').count == total_parent_hosts

            # Verify that the parent.all_hosts has changed
            assert parent_group.get_related('all_hosts').count == total_parent_all_hosts - total_group_all_hosts

    def test_circular_dependency(self, inventory):
        '''verify unable to add a circular dependency (top -> ... -> leaf -> top)'''

        # Add parent_group
        payload = dict(name="root-%s" % fauxfactory.gen_alphanumeric(), inventory=inventory.id)
        parent_group = inventory.get_related('groups').post(payload)

        # Add child_group
        payload = dict(name="child-%s" % fauxfactory.gen_alphanumeric(), inventory=inventory.id)
        child_group = parent_group.get_related('children').post(payload)

        # Add grandchild_group
        payload = dict(name="grandchild-%s" % fauxfactory.gen_alphanumeric(), inventory=inventory.id)
        grandchild_group = child_group.get_related('children').post(payload)

        # Attempt to associate circular dependency
        payload = dict(id=parent_group.id)
        with pytest.raises(qe.exceptions.Forbidden_Exception):
            grandchild_group.get_related('children').post(payload)

    def test_unique(self, inventory, another_inventory):
        '''verify duplicate group names are allowed if in a different inventory'''

        # Create inventory.parent_group
        payload = dict(name="root-%s" % fauxfactory.gen_alphanumeric(), inventory=inventory.id)
        parent_group = inventory.get_related('groups').post(payload)

        # Create inventory.child_group
        payload = dict(name="child-%s" % fauxfactory.gen_alphanumeric(), inventory=inventory.id)
        child_group = parent_group.get_related('children').post(payload)

        # Create another_inventory.parent_group (duplicate name, but different inventory)
        payload = dict(name=parent_group.name, inventory=another_inventory.id)
        new_parent = another_inventory.get_related('groups').post(payload)

        # Create another_inventory.child_group (duplicate name, but different inventory)
        # Create a child group with a duplicate name, in another inventory
        payload = dict(name=child_group.name, inventory=another_inventory.id)
        new_parent.get_related('children').post(payload)

    def test_duplicate(self, inventory):
        '''verify duplicate group names, in the same inventory, are not allowed'''

        # Add parent_group
        payload = dict(name="root-%s" % fauxfactory.gen_alphanumeric(), inventory=inventory.id)
        parent_group = inventory.get_related('groups').post(payload)

        # Add child_group
        payload = dict(name="child-%s" % fauxfactory.gen_alphanumeric(), inventory=inventory.id)
        child_group = parent_group.get_related('children').post(payload)

        # Attempt to create duplicate group as a root_group
        payload = dict(name=child_group.name, inventory=inventory.id)
        with pytest.raises(qe.exceptions.Duplicate_Exception):
            inventory.get_related('groups').post(payload)

        # Attempt to create duplicate group as a child_group
        payload = dict(name=parent_group.name, inventory=inventory.id)
        with pytest.raises(qe.exceptions.Duplicate_Exception):
            parent_group.get_related('children').post(payload)

    def test_name_reuse(self, some_group):
        '''verify one can re-use the name of a previously deleted group'''

        groups_pg = some_group.get_related('inventory').get_related('groups')

        # Delete the group
        some_group.delete()

        # The group should immediately be marked as inactive (aka deleted) by Tower
        with pytest.raises(qe.exceptions.NotFound_Exception):
            some_group.get()

        # Create a new group, with the same name
        # NOTE: Tower processes group DELETE's asynchronously, so it can take a
        # bit for the group actually delete.  We'll attempt to create a new
        # group, with the same name.  This should eventually succeed.
        payload = dict(name=some_group.name, inventory=some_group.inventory)
        tries = 1
        max_tries = 10
        while True:
            try:
                groups_pg.post(payload)
            except qe.exceptions.Duplicate_Exception:
                if tries > max_tries:
                    raise Exception("The group '%s' (id: %s) wasn't cleaned up after %d attempts" % (some_group.name, some_group.id, tries))
                tries += 1
            else:
                break
