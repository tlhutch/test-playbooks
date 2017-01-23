import fauxfactory
import pytest

from towerkit.exceptions import NotFound


pytestmark = [pytest.mark.ui]


@pytest.fixture(scope='module')
def org_cred(api_v1, session_org):
    cred = api_v1.credentials.create(user=None, organization=session_org, team=None)
    yield cred
    cred.silent_cleanup()


@pytest.fixture(scope='module')
def private_cred(api_v1, session_user):
    cred = api_v1.credentials.create(user=session_user, organization=None, team=None)
    yield cred
    cred.silent_cleanup()


@pytest.mark.github('https://github.com/ansible/ansible-tower/issues/4184')
def test_permissions_tab_is_disabled_for_private_credentials(ui, private_cred):
    edit = ui.credential_edit.get(id=private_cred.id)
    # check that the tab is disabled initially
    assert not edit.permissions_tab.is_enabled()
    # check that clicking the tab does not enable it
    edit.permissions_tab.click()
    assert not edit.permissions_tab.is_enabled()
    assert 'permission' not in edit.driver.current_url


def test_edit_credential(ui, org_cred):
    """Basic end-to-end functional test for updating an existing credential"""
    edit = ui.credential_edit.get(id=org_cred.id)
    # make some data
    name = fauxfactory.gen_alphanumeric()
    description = fauxfactory.gen_alphanumeric()
    # update the credential
    edit.details.name.value = name
    edit.details.description.value = description
    # save the credential
    edit.details.scroll_save_into_view().click()
    edit.table.wait_for_table_to_load()
    # verify the update took place
    assert edit.passively_wait_until(lambda: org_cred.get().name == name), (
        'Unable to verify successful update of credential')
    assert org_cred.description == description, (
        'Unable to verify successful update of credential')
    # query the table for the edited credential
    edit.details.scroll_save_into_view()
    edit.search(name)
    results = edit.table.query(lambda r: r.name.text == name)
    # check that we find a row showing the updated credential name
    assert len(results) == 1, 'Unable to find row of updated credential'


def test_delete_credential(v1, ui, org_cred):
    """End-to-end functional test for deleting a credential"""
    cred_name = org_cred.name
    cred_page = ui.credentials.get()
    # add a search filter for the credential
    cred_page.search(cred_name)
    # query the list for the newly created credential
    results = cred_page.table.query(lambda r: r.name.text == cred_name)
    # delete the credential
    with cred_page.handle_dialog(lambda d: d.action.click()):
        results.pop().delete.click()
    # verify deletion
    cred_page.table.wait_for_table_to_load()
    # verify deletion api-side
    with pytest.raises(NotFound):
        org_cred.get()
    # verify that the deleted resource is no longer displayed
    cred_page.search.clear()
    cred_page.search(cred_name)
    cred_page.table.wait_for_table_to_load()
    results = cred_page.table.query(lambda r: r.name.text == cred_name)
    assert not results


def test_create_user_credential(v1, ui):
    """End-to-end functional test for creating a user credential"""
    add = ui.credential_add.get()
    add.table.wait_for_table_to_load()
    # make some data
    name = fauxfactory.gen_alphanumeric()
    # populate the form and save
    machine_details = add.details.machine
    machine_details.name.value = name
    machine_details.scroll_save_into_view().click()
    # verify the update took place api-side
    add.passively_wait_until(lambda: v1.credentials.get(name=name).results)
    api_results = v1.credentials.get(name=name).results
    assert len(api_results) == 1, 'unable to verify creation of credential'
    # add a search filter for the credential
    add.search(name)
    # check that we find a row showing the updated credential name
    results = add.table.query(lambda r: r.name.text == name)
    assert len(results) == 1, 'unable to verify creation of credential'


@pytest.mark.github('https://github.com/ansible/ansible-tower/issues/4840')
def test_create_org_credential(v1, ui, session_org):
    """End-to-end functional test for creating an org credential"""
    add = ui.credential_add.get()
    add.table.wait_for_table_to_load()
    # make some data
    name = fauxfactory.gen_alphanumeric()
    # populate the form and save
    add.details.machine.name.value = name
    add.details.machine.organization.value = session_org.name
    add.details.machine.scroll_save_into_view().click()
    # verify the update took place api-side
    add.passively_wait_until(lambda: v1.credentials.get(name=name).results)
    api_results = v1.credentials.get(name=name).results
    assert len(api_results) == 1, 'unable to verify creation of credential'
    # add a search filter for the credential
    add.search(name)
    # check that we find a row showing the updated credential name
    results = add.table.query(lambda r: r.name.text == name)
    assert len(results) == 1, 'unable to verify creation of credential'
    # verify org association to credential
    row = results.pop()
    assert session_org.name.lower() in [e.text.lower() for e in row.owner_list]
