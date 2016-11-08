import time

import fauxfactory
import pytest

from towerkit.exceptions import NotFound

pytestmark = [
    pytest.mark.ui,
    pytest.mark.nondestructive,
    pytest.mark.usefixtures(
        'authtoken',
        'install_enterprise_license',
        'max_window',
    )
]


def test_inventory_search_persists_after_sorting_table(factories, ui_inventories):
    # create inventories that can be filtered / excluded by adding a search filter
    # for a specific organization
    org = factories.organization()
    factories.inventory(organization=org)
    factories.inventory(organization=org)
    factories.inventory()
    # filter the inventory list by organization name
    ui_inventories.list_search.add_filter('organization', org.name)
    # verify expected results count from filtering
    assert len(ui_inventories.list_table.rows) == 2
    # change the table sorting
    ui_inventories.list_table.header.set_sort_status(('name', 'ascending'))
    ui_inventories.list_table.header.set_sort_status(('name', 'descending'))
    # verify expected results count from filtering
    assert len(ui_inventories.list_table.rows) == 2
    # verify current search filter type is still organization
    assert ui_inventories.list_search.search_type == 'organization'


def test_edit_inventory(api_inventories_pg, ui_inventory_edit):
    """Basic end-to-end functional test for updating an existing inventory
    """
    # make some data
    name = fauxfactory.gen_alphanumeric()
    description = fauxfactory.gen_alphanumeric()
    # update the inventory
    ui_inventory_edit.details.name.value = name
    ui_inventory_edit.details.description.value = description
    # save the inventory
    time.sleep(5)
    ui_inventory_edit.details.save.click()
    ui_inventory_edit.list_table.wait_for_table_to_load()
    # get inventory data api-side
    time.sleep(5)
    api_inventory = api_inventories_pg.get(
        id=ui_inventory_edit.kw['id']).results[0]
    # verify the update took place
    assert api_inventory.name == name, (
        'Unable to verify successful update of inventory')
    assert api_inventory.description == description, (
        'Unable to verify successful update of inventory')
    # query the table for the edited inventory
    results = ui_inventory_edit.list_table.query(lambda r: r.name.text == name)
    # check that we find a row showing the updated inventory name
    assert len(results) == 1, 'Unable to find row of updated inventory'


def test_delete_inventory(factories, ui_inventories):
    """Basic end-to-end verification for deleting a inventory
    """
    inventory = factories.inventory()
    # add a search filter for the inventory
    ui_inventories.driver.refresh()
    ui_inventories.list_table.wait_for_table_to_load()
    ui_inventories.list_search.add_filter('name', inventory.name)
    # query the list for the newly created inventory
    results = ui_inventories.list_table.query(
        lambda r: r.name.text == inventory.name)
    # delete the inventory
    results.pop().delete.click()
    # confirm deletion
    ui_inventories.dialog.action.click()
    ui_inventories.list_table.wait_for_table_to_load()
    # verify deletion api-side
    with pytest.raises(NotFound):
        inventory.get()
    # verify that the deleted resource is no longer displayed
    results = ui_inventories.list_table.query(
        lambda r: r.name.text == inventory.name)
    assert not results


def test_create_inventory(factories, api_inventories_pg, ui_inventory_add):
    """Basic end-to-end verification for creating a inventory
    """
    # make some data
    org = factories.organization()
    name = fauxfactory.gen_alphanumeric()
    # populate the form
    ui_inventory_add.driver.refresh()
    ui_inventory_add.details.name.value = name
    ui_inventory_add.details.organization.value = org.name
    # save the inventory
    time.sleep(5)
    ui_inventory_add.details.save.click()
    ui_inventory_add.list_table.wait_for_table_to_load()
    # verify the update took place api-side
    api_results = api_inventories_pg.get(name=name).results
    assert api_results, 'unable to verify creation of inventory'
    # check for expected url content
    expected_url_content = '/#/inventories/{0}/manage'.format(api_results[0].id)
    assert expected_url_content in ui_inventory_add.driver.current_url
    # return to the inventories page
    ui_inventory_add.driver.back()
    # add a search filter for the inventory
    ui_inventory_add.list_search.add_filter('name', name)
    # check that we find a row showing the updated inventory name
    results = ui_inventory_add.list_table.query(lambda r: r.name.text == name)
    assert len(results) == 1, 'unable to verify creation of inventory'
