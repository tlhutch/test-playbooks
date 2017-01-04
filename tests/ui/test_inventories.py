import fauxfactory
import pytest

from towerkit.exceptions import NotFound


pytestmark = [pytest.mark.ui]


@pytest.fixture(scope='module')
def shared_org(api_v1):
    org = api_v1.organizations.create(name=fauxfactory.gen_alphanumeric())
    yield org
    org.silent_cleanup()


@pytest.fixture(scope='module')
def shared_org_inventories(api_v1, shared_org):
    invs = [api_v1.inventory.create(organization=shared_org) for _ in xrange(2)]
    yield invs
    [obj.silent_cleanup() for obj in invs]


@pytest.mark.usefixtures('inventory', 'shared_org_inventories')
def test_inventory_search_persists_after_sorting(ui, shared_org):
    # create inventories that can be filtered / excluded by adding a search filter
    # for a specific organization
    inventories = ui.inventories.get()
    # there should be at least three inventories visible
    assert len(inventories.table.rows) >= 3
    # filter the inventory list by organization name
    inventories.search('or:organization:name:icontains:{0}'.format(shared_org.name))
    # verify expected results count from filtering
    assert len(inventories.table.rows) == 2
    # change the table sorting
    inventories.table.header.set_sort_status(('name', 'ascending'))
    inventories.table.header.set_sort_status(('name', 'descending'))
    # verify expected results count from filtering
    assert len(inventories.table.rows) == 2


def test_edit_inventory(v1, ui, inventory):
    """End-to-end functional test for updating an inventory"""
    # make some data
    name = fauxfactory.gen_alphanumeric()
    description = fauxfactory.gen_alphanumeric()
    # update the inventory
    edit = ui.inventory_edit.get(id=inventory.id)
    edit.details.name.value = name
    edit.details.description.value = description
    # save the inventory
    edit.details.save.click()
    edit.table.wait_for_table_to_load()
    # verify the update took place
    inventory.get()
    assert inventory.name == name, (
        'Unable to verify successful update of inventory')
    assert inventory.description == description, (
        'Unable to verify successful update of inventory')
    edit.search(name)
    results = edit.table.query(lambda r: r.name.text == name)
    # check that we find a row showing the updated inventory name
    assert len(results) == 1, 'Unable to find row of updated inventory'


def test_delete_inventory(ui, inventory):
    """End-to-end functional test for deleting an inventory"""
    ui_inventories = ui.inventories.get()
    # add a search filter for the inventory
    ui_inventories.search(inventory.name)
    # query the list for the newly created inventory
    results = ui_inventories.table.query(lambda r: r.name.text == inventory.name)
    # delete the inventory
    with ui_inventories.handle_dialog(lambda d: d.action.click()):
        results.pop().delete.click()
    # verify deletion api-side
    with pytest.raises(NotFound):
        inventory.get()
    # verify that the deleted resource is no longer displayed
    ui_inventories.search.clear()
    ui_inventories.search(inventory.name)
    results = ui_inventories.table.query(lambda r: r.name.text == inventory.name)
    assert len(results) == 0


def test_create_inventory(v1, ui, session_org):
    """End-to-end functional test for creating an inventory"""
    add = ui.inventory_add.get()
    # make some data
    name = fauxfactory.gen_alphanumeric()
    # populate the form
    add.details.name.value = name
    add.details.organization.value = session_org.name
    # save the inventory
    add.wait.until(lambda _: add.details.save.is_enabled())
    add.details.save.click()
    add.passively_wait_until(lambda: v1.inventory.get(name=name).results)
    # verify the update took place api-side
    api_results = v1.inventory.get(name=name).results
    assert len(api_results) == 1, 'unable to verify creation of inventory'
    # return to the inventories page
    add.get().search(name)
    # check that we find a row showing the updated inventory name
    results = add.table.query(lambda r: r.name.text == name)
    assert len(results) == 1, 'unable to verify creation of inventory'
    api_results.pop().silent_cleanup()
