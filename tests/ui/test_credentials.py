import time

import fauxfactory
import pytest
from selenium.common.exceptions import TimeoutException

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


def test_permissions_tab_is_disabled_for_private_credentials(ui_private_credential):
    # check that the tab is disabled initially
    assert not ui_private_credential.permissions_tab.is_enabled()
    # check that clicking the tab does not enable it
    ui_private_credential.permissions_tab.click()
    assert not ui_private_credential.permissions_tab.is_enabled()


def test_edit_credential(api_credentials_pg, ui_credential_edit):
    """Basic end-to-end functional test for updating an existing credential
    """
    # make some data
    name = fauxfactory.gen_alphanumeric()
    description = fauxfactory.gen_alphanumeric()
    # update the credential
    ui_credential_edit.details.name.value = name
    ui_credential_edit.details.description.value = description
    # save the credential
    time.sleep(5)
    ui_credential_edit.details.save.click()
    ui_credential_edit.list_table.wait_for_table_to_load()
    # get credential data api side
    api_credential = api_credentials_pg.get(id=ui_credential_edit.kw['id']).results[0]
    # verify the update took place
    assert api_credential.name == name, (
        'Unable to verify successful update of credential')
    assert api_credential.description == description, (
        'Unable to verify successful update of credential')
    # query the table for the edited credential
    results = ui_credential_edit.list_table.query(lambda r: r.name.text == name)
    # check that we find a row showing the updated credential name
    assert len(results) == 1, 'Unable to find row of updated credential'


def test_delete_credential(factories, ui_credentials):
    """Basic end-to-end verification for deleting a credential
    """
    credential = factories.credential()
    # add a search filter for the credential
    ui_credentials.driver.refresh()
    ui_credentials.list_table.wait_for_table_to_load()
    ui_credentials.list_search.add_filter('name', credential.name)
    # query the list for the newly created credential
    results = ui_credentials.list_table.query(lambda r: r.name.text == credential.name)
    # delete the credential
    results.pop().delete.click()
    # confirm deletion
    ui_credentials.dialog.action.click()
    ui_credentials.list_table.wait_for_table_to_load()
    # verify deletion api-side
    with pytest.raises(NotFound):
        credential.get()
    # verify that the deleted resource is no longer displayed
    results = ui_credentials.list_table.query(lambda r: r.name.text == credential.name)
    assert not results


def test_create_credential(factories, api_credentials_pg, ui_credential_add):
    """Basic end-to-end verification for creating a credential
    """
    ui_credential_add.list_table.wait_for_table_to_load()
    # make some data
    name = fauxfactory.gen_alphanumeric()
    # populate the form and save
    machine_details = ui_credential_add.details.machine
    machine_details.name.value = name
    time.sleep(5)
    machine_details.scroll_save_into_view().click()
    # verify the update took place api-side
    try:
        ui_credential_add.wait.until(lambda _: api_credentials_pg.get(name=name).results)
    except TimeoutException:
        pytest.fail('unable to verify creation of credential')
    api_results = api_credentials_pg.get(name=name).results
    # check for expected url content
    expected_url_content = '/#/credentials/{0}'.format(api_results[0].id)
    assert expected_url_content in ui_credential_add.driver.current_url
    # add a search filter for the credential
    machine_details.cancel.click()
    ui_credential_add.driver.refresh()
    ui_credential_add.wait_until_loaded().list_search.add_filter('name', name)
    # check that we find a row showing the updated credential name
    results = ui_credential_add.list_table.query(lambda r: r.name.text == name)
    assert len(results) == 1, 'unable to verify creation of credential'
