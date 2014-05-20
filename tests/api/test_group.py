import pytest
import common.tower.inventory
import common.exceptions
from tests.api import Base_Api_Test

# Ansible inventory variations for testing 'root' group removal
root_variations = [
    dict(id='children:0, hosts:0',
         inventory='''
[usa] # <------- DELETE
[fr]
fr-host-1
fr-host-2
[uk]
uk-host-1
[de]
'''),
    dict(id='children:m, hosts:0',
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
    dict(id='children:0, hosts:n',
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
    dict(id='children:m, hosts:n',
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
def root_inventory(request, authtoken, random_inventory, ansible_runner):
    results = ansible_runner.copy(dest='/tmp/inventory.ini', content='''# --inventory-id %s
%s''' % (random_inventory.id, request.param['inventory']))
    assert results['changed'] and 'failed' not in results, "Failed to create inventory file: %s" % results

    results = ansible_runner.shell('awx-manage inventory_import --inventory-id %s --source /tmp/inventory.ini' % random_inventory.id)
    assert results['rc'] == 0, "awx-managed inventory_import failed: %s" % results
    print results['stdout']

    # Re-GET the resource to populate host/group information
    random_inventory = random_inventory.get()
    assert random_inventory.get_related('groups').count > 0
    assert random_inventory.get_related('hosts').count > 0
    return random_inventory

# Ansible inventory variations for testing 'non-root' group removal.  These are
# the same as root_variations ... but they are nested a level deeper.
inventory_prefix= '''
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
non_root_variations = [dict(id=k, inventory=inventory_prefix + v) for k,v in root_variations]

@pytest.fixture(scope="function", params=non_root_variations)
def non_root_inventory(request, authtoken, random_inventory, ansible_runner):
    results = ansible_runner.copy(dest='/tmp/inventory.ini', content='''# --inventory-id %s
%s''' % (random_inventory.id, request.param['inventory']))
    assert results['changed'] and 'failed' not in results, "Failed to create inventory file: %s" % results

    results = ansible_runner.shell('awx-manage inventory_import --inventory-id %s --source /tmp/inventory.ini' % random_inventory.id)
    assert results['rc'] == 0, "awx-managed inventory_import failed: %s" % results
    print results['stdout']

    # Re-GET the resource to populate host/group information
    random_inventory = random_inventory.get()
    assert random_inventory.get_related('groups').count > 0
    assert random_inventory.get_related('hosts').count > 0
    return random_inventory

@pytest.mark.skip_selenium
@pytest.mark.destructive
class Test_Group_Disassociate(Base_Api_Test):
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

    pytestmark = pytest.mark.usefixtures('authtoken', 'install_license_1000')

    def test_root_group(self, root_inventory):
        '''verify behavior of disassociate of a top-level group'''

        # Locate top-level group
        root_groups_pg = root_inventory.get_related('root_groups', name='usa')
        assert root_groups_pg.count == 1
        group = root_groups_pg.results[0]

        # Record group counts
        total_inv_groups = root_inventory.get_related('groups').count
        total_inv_root_groups = root_inventory.get_related('root_groups').count
        total_inv_hosts = root_inventory.get_related('hosts').count
        total_group_children = group.get_related('children').count

        # disassociate top-level group
        payload = dict(id=group.id, disassociate=True)
        with pytest.raises(common.exceptions.NoContent_Exception):
            root_inventory.get_related('groups').post(payload)

        # Verify top-level group deleted
        assert root_inventory.get_related('root_groups', name=group.name).count == 0
        assert root_inventory.get_related('groups', name=group.name).count == 0

        # Verify root_group count adjusts properly (one removed, and children promoted)
        assert root_inventory.get_related('root_groups').count == total_inv_root_groups + total_group_children - 1

        # Verify group counts decremented properly
        assert root_inventory.get_related('groups').count == total_inv_groups - 1

        # Verify no hosts were removed
        assert root_inventory.get_related('hosts').count == total_inv_hosts

    def test_non_root_group(self, non_root_inventory):
        '''verify behavior of disassociate of a child group with children:0 and hosts:0 (leaf group)'''

        # Locate parent and child group
        assert non_root_inventory.get_related('groups', name='na').count == 1
        parent_group = non_root_inventory.get_related('groups', name='na').results.pop()
        assert non_root_inventory.get_related('groups', name='usa').count == 1
        child_group = non_root_inventory.get_related('groups', name='usa').results.pop()

        # Record before counts
        total_inv_groups = non_root_inventory.get_related('groups').count
        total_inv_root_groups = non_root_inventory.get_related('root_groups').count
        total_inv_hosts = non_root_inventory.get_related('hosts').count
        total_group_children = child_group.get_related('children').count
        total_group_hosts = child_group.get_related('hosts').count
        total_parent_children = parent_group.get_related('children').count
        total_parent_hosts = parent_group.get_related('hosts').count

        # disassociate all matching child_group
        payload = dict(id=child_group.id, disassociate=True)
        with pytest.raises(common.exceptions.NoContent_Exception):
            # non_root_inventory.get_related('groups').post(payload)
            parent_group.get_related('children').post(payload)

        # FIXME - test disassociate a single group - /groups/N/children
        # FIXME - test disassociate a all matching groups - /inventory/N/groups

        # Verify group deleted
        assert non_root_inventory.get_related('root_groups', name=child_group.name).count == 0
        assert non_root_inventory.get_related('groups', name=child_group.name).count == 0

        # Verify root_group count stays the same
        assert non_root_inventory.get_related('root_groups').count == total_inv_root_groups

        # Verify group counts decremented properly
        assert non_root_inventory.get_related('groups').count == total_inv_groups - 1

        # Verify no hosts were removed
        assert non_root_inventory.get_related('hosts').count == total_inv_hosts

        # Verify groups were promoted
        assert parent_group.get_related('children').count == total_parent_children + total_group_children - 1

        # Verify hosts were promoted
        assert parent_group.get_related('hosts').count == total_parent_hosts + total_group_hosts

    def test_circular_dependency(self, random_inventory):
        '''verify unable to add a circular dependency (top -> ... -> leaf -> top)'''

        # Add parent_group
        payload = dict(name="root-%s" % common.utils.random_ascii(), inventory=random_inventory.id)
        parent_group = random_inventory.get_related('groups').post(payload)

        # Add child_group
        payload = dict(name="child-%s" % common.utils.random_ascii(), inventory=random_inventory.id)
        child_group = parent_group.get_related('children').post(payload)

        # Add grandchild_group
        payload = dict(name="grandchild-%s" % common.utils.random_ascii(), inventory=random_inventory.id)
        grandchild_group = child_group.get_related('children').post(payload)

        # Attempt to create circular dependency
        payload = dict(name=parent_group.name, inventory=random_inventory.id)
        with pytest.raises(common.exceptions.Duplicate_Exception):
            grandchild_group.get_related('children').post(payload)

        # Attempt to associate circular dependency
        payload = dict(id=parent_group.id)
        with pytest.raises(common.exceptions.Forbidden_Exception):
            grandchild_group.get_related('children').post(payload)

