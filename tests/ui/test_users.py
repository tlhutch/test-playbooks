import time

import fauxfactory
import pytest

from towerkit.exceptions import NotFound


pytestmark = [pytest.mark.ui]


@pytest.fixture(scope='module')
def user(api_v1, session_org):
    obj = api_v1.users.create(organization=session_org)
    yield obj
    obj.silent_cleanup()


def test_edit_user(ui, user):
    """Basic end-to-end functional test for updating an existing user
    """
    edit = ui.user_edit.get(id=user.id)
    # these are indicators that the page is actually ready to be used
    edit.table.wait_for_table_to_load()
    edit.wait.until(lambda _: 'Normal User' in edit.details.user_type.options)
    # make some data and update the user
    username = fauxfactory.gen_alphanumeric()
    edit.details.username.value = username
    # save the user
    edit.details.save.click()
    edit.table.wait_for_table_to_load()
    # get user data api side
    user.get()
    # verify the update took place
    assert user.username == username, 'Unable to verify successful update of user'
    # query the table for the edited user
    edit.search(username)
    results = edit.table.query(lambda r: r.username.text == username)
    # check that we find a row showing the updated username
    assert len(results) == 1, 'Unable to find row of updated user'


def test_delete_user(ui, user):
    """End-to-end functional test for deleting a user
    """
    ui_users = ui.users.get()
    # add a search filter for the user
    ui_users.search(user.username)
    # query the list for the newly created user
    results = ui_users.table.query(lambda r: r.username.text == user.username)
    # delete the user
    with ui_users.handle_dialog(lambda d: d.action.click()):
        results.pop().delete.click()
    ui_users.table.wait_for_table_to_load()
    # verify deletion
    with pytest.raises(NotFound):
        user.get()
    # verify that the deleted resource is no longer displayed
    ui_users.search.clear()
    ui_users.search(user.username)
    results = ui_users.table.query(lambda r: r.username.text == user.username)
    assert len(results) == 0


def test_create_user(v1, ui, session_org):
    """End-to-end functional test for creating a user
    """
    add = ui.user_add.get()
    # these are indicators that the page is actually ready to be used
    add.table.wait_for_table_to_load()
    add.wait.until(lambda _: 'Normal User' in add.details.user_type.options)
    # make some data
    username = fauxfactory.gen_alphanumeric()
    password = fauxfactory.gen_alphanumeric().title() + '1'
    # populate the form
    add.details.organization.value = session_org.name
    add.details.first_name.randomize()
    add.details.last_name.randomize()
    add.details.email.randomize()
    add.details.username.value = username
    add.details.password.value = password
    add.details.password_confirm.value = password
    # save the user
    time.sleep(5)
    add.details.save.click()
    add.table.wait_for_table_to_load()
    # verify the update took place api-side
    add.passively_wait_until(lambda: v1.users.get(username=username).results)
    api_results = v1.users.get(username=username).results
    assert len(api_results) == 1, 'unable to verify creation of user'
    # check that we find a row showing the updated username
    add.search(username)
    ui_results = add.table.query(lambda r: r.username.text == username)
    assert len(ui_results) == 1, 'unable to verify creation of user'
