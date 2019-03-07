import json

from towerkit import exceptions as exc
from towerkit import utils
import fauxfactory
import pytest

from tests.api import APITest


# Ansible inventory variations for testing 'root' group removal
root_variations = [
    dict(name='children:0, hosts:0',
         inventory="""
[usa] # <------- DELETE
[fr]
fr-host-1
fr-host-2
[uk]
uk-host-1
[de]
"""),
    dict(name='children:m, hosts:0',
         inventory="""
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
[ca]
[pa]
[nc]
"""),
    dict(name='children:0, hosts:n',
         inventory="""
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
"""),
    dict(name='children:m, hosts:n',
         inventory="""
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
[ca]
[nc]
"""),
]


@pytest.fixture(scope="function", params=root_variations)
def root_variation(request, authtoken, inventory, ansible_runner):
    inv_filename = '/tmp/inventory_{}.ini'.format(fauxfactory.gen_alphanumeric())
    contacted = ansible_runner.copy(
        dest=inv_filename,
        force=True, mode='0644',
        content="""# --inventory-id %s %s""" % (inventory.id, request.param['inventory'])
    )
    for results in contacted.values():
        assert results.get('changed') and not results.get('failed'), "Failed to create inventory file: %s" % results

    contacted = ansible_runner.shell(
        "awx-manage inventory_import --overwrite --inventory-id {0.id} "
        "--source {1}".format(inventory, inv_filename)
    )
    for results in contacted.values():
        assert results['rc'] == 0, "awx-manage inventory_import failed: %s" % results

    # Re-GET the resource to populate host/group information
    inventory = inventory.get()
    assert inventory.get_related('groups').count > 0
    assert inventory.get_related('hosts').count > 0
    return inventory


# Ansible inventory variations for testing 'non-root' group removal.  These are
# the same as root_variations ... but they are nested a level deeper.
inventory_prefix = """
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
[af]
[an]
[as]
[eu]
[oc]
[sa]
[can]
[grl]
[mex]
"""


non_root_variations = [dict(name=item['name'], inventory=inventory_prefix + item['inventory']) for item in root_variations]


@pytest.fixture(scope="function", params=non_root_variations)
def non_root_variation(request, authtoken, inventory, ansible_runner):
    inv_filename = '/tmp/inventory_{}.ini'.format(fauxfactory.gen_alphanumeric())
    contacted = ansible_runner.copy(
        dest=inv_filename,
        force=True, mode='0644',
        content="""# --inventory-id %s %s""" % (inventory.id, request.param['inventory'])
    )
    for results in contacted.values():
        assert results.get('changed') and not results.get('failed'), \
            "Failed to create inventory file: %s" % \
            json.dumps(results, indent=2)

    contacted = ansible_runner.shell(
        "awx-manage inventory_import --overwrite --inventory-id {0.id} "
        "--source {1}".format(inventory, inv_filename)
    )
    for results in contacted.values():
        assert results['rc'] == 0, "awx-manage inventory_import failed: %s" % \
            json.dumps(results, indent=2)

    # Re-GET the resource to populate host/group information
    inventory = inventory.get()
    assert inventory.get_related('groups').count > 0
    assert inventory.get_related('hosts').count > 0
    return inventory


all_variations = root_variations + non_root_variations


@pytest.fixture(scope="function", params=all_variations)
def variation(request, authtoken, inventory, ansible_runner):
    inv_filename = '/tmp/inventory_{}.ini'.format(fauxfactory.gen_alphanumeric())
    contacted = ansible_runner.copy(
        dest=inv_filename, force=True,
        content="""# --inventory-id %s %s""" % (inventory.id, request.param['inventory']))
    for results in contacted.values():
        assert results.get('changed') and not results.get('failed'), "Failed to create inventory file: %s" % results

    contacted = ansible_runner.shell(
        "awx-manage inventory_import --overwrite --inventory-id {0.id} "
        "--source {1}".format(inventory, inv_filename)
    )
    for results in contacted.values():
        assert results['rc'] == 0, "awx-manage inventory_import failed: %s" % results

    # Re-GET the resource to populate host/group information
    inventory = inventory.get()
    assert inventory.get_related('groups').count > 0
    assert inventory.get_related('hosts').count > 0
    return inventory


@pytest.mark.api
@pytest.mark.destructive
@pytest.mark.ansible(host_pattern='tower[0]')  # target 1 normal instance
@pytest.mark.usefixtures('authtoken', 'install_enterprise_license_unlimited')
class TestGroup(APITest):
    """Verify DELETE and POST (disassociate) behaves as expected for groups and their hosts

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
    """
    def test_disassociate_root_group(self, skip_if_openshift, root_variation):
        """verify behavior of disassociate of a top-level group.
        POST {id=N, disassociate=True} to /inventories/N/groups
        """
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
        with utils.suppress(exc.NoContent):
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

    def test_disassociate_non_root_group(self, skip_if_openshift, non_root_variation):
        """verify behavior of disassociate of a child group
        POST {disassociate=True} /groups/N/children
        """
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
        with utils.suppress(exc.NoContent):
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

    def test_delete(self, skip_if_openshift, api_groups_pg, variation):
        """verify behavior of group delete
        DELETE /groups/N
        """
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

    def test_associate_with_root_group(self, skip_if_openshift, non_root_variation):
        """Verify expected behavior when disassociating a group from it's parent, thereby creating a root group.
        POST {id=M, disassociate=True} /groups/N/children
        """
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
        with utils.suppress(exc.NoContent):
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

    def test_associate_with_non_root_group(self, skip_if_openshift, root_variation):
        """Verify expected behavior for a group association
        POST {id=N} /group/<new_parent>/children
        """
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
        with utils.suppress(exc.NoContent):
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

    @pytest.mark.yolo
    def test_reassociate_with_non_root_group(self, skip_if_openshift, non_root_variation):
        """Verify expected behavior for moving a group from one non-root-group to another
        POST {id=M} /groups/<new_parent>/children
        POST {id=M, disassociate=True} /groups/<old_parent>/children
        """
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
        with utils.suppress(exc.NoContent):
            dest_group.get_related('children').post(payload)

        # Disassociate group from parent_group
        if parent_group:
            payload = dict(id=group.id, disassociate=True)
            with utils.suppress(exc.NoContent):
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

    def test_circular_association(self, factories):
        """Verify that child groups cannot list their parents and grandparents as a child."""
        parent_group = factories.v2_group()
        inventory = parent_group.ds.inventory
        child_group, grandchild_group = [factories.v2_group(inventory=inventory) for group in range(2)]
        parent_group.add_group(child_group)
        child_group.add_group(grandchild_group)

        with pytest.raises(exc.BadRequest) as e:
            for group in [child_group, grandchild_group]:
                group.add_group(parent_group)
        assert e.value.msg['error'] == 'Cyclical Group association.'

    def test_self_association(self, factories):
        """Verify that groups cannot list themselves as a child."""
        group = factories.v2_group()
        with pytest.raises(exc.BadRequest) as e:
            group.add_group(group)
        assert e.value[1] == {'error': 'Cyclical Group association.'}

    def test_duplicate_groups_allowed_in_different_inventories(self, factories):
        """Verify that duplicate groups are allowed in different inventories."""
        parent1 = factories.v2_group()
        child1 = factories.v2_group(inventory=parent1.ds.inventory)
        parent1.add_group(child1)

        inventory = factories.v2_inventory()
        parent2, child2 = [factories.v2_group(inventory=inventory, name=name) for name in (parent1.name, child1.name)]
        parent2.add_group(child2)

    def test_duplicate_groups_disallowed_in_same_inventory(self, factories):
        """Verify that duplicate groups are not allowed in the same inventory."""
        parent = factories.v2_group()
        inventory = parent.ds.inventory
        child = factories.v2_group(inventory=inventory)
        parent.add_group(child)

        for group in [parent, child]:
            with pytest.raises(exc.Duplicate):
                factories.v2_group(inventory=inventory, name=group.name)

    def test_reused_names(self, factories):
        """Verify that group names may be reused after group deletion."""
        group = factories.v2_group()
        inventory = group.ds.inventory

        group.delete()
        factories.v2_group(inventory=inventory, name=group.name)
