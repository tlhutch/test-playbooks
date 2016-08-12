import time

import fauxfactory
import pytest

from common.exceptions import NotFound_Exception

pytestmark = [
    pytest.mark.ui,
    pytest.mark.nondestructive,
    pytest.mark.usefixtures(
        'authtoken',
        'install_enterprise_license',
        'max_window',
    )
]


def test_edit_user(api_users_pg, ui_user_edit):
    """Basic end-to-end functional test for updating an existing user
    """
    # make some data and update the user
    username = fauxfactory.gen_alphanumeric()
    ui_user_edit.details.username.set_value(username)
    # save the user
    time.sleep(5)
    ui_user_edit.details.save.click()
    ui_user_edit.list_table.wait_for_table_to_load()
    # get user data api side
    time.sleep(5)
    api_user = api_users_pg.get(id=ui_user_edit.kwargs['id']).results[0]
    # verify the update took place
    assert api_user.username == username, (
        'Unable to verify successful update of user')
    # query the table for the edited user
    results = ui_user_edit.list_table.query(
        lambda r: r.username.text == username)
    # check that we find a row showing the updated username
    assert len(results) == 1, 'Unable to find row of updated user'


def test_delete_user(factories, ui_users):
    """Basic end-to-end verification for deleting a user
    """
    user = factories.user()
    # add a search filter for the user
    ui_users.driver.refresh()
    ui_users.list_table.wait_for_table_to_load()
    ui_users.list_search.add_filter('username', user.username)
    # query the list for the newly created user
    results = ui_users.list_table.query(
        lambda r: r.username.text == user.username)
    # delete the user
    results.pop().delete.click()
    # confirm deletion
    ui_users.dialog.confirm.click()
    ui_users.list_table.wait_for_table_to_load()
    # verify deletion api-side
    with pytest.raises(NotFound_Exception):
        user.get()
    # verify that the deleted resource is no longer displayed
    results = ui_users.list_table.query(
        lambda r: r.username.text == user.username)
    assert not results


def test_create_user(factories, api_users_pg, ui_user_add):
    """Basic end-to-end verification for creating a user
    """
    # make some data
    organization = factories.organization()
    username = fauxfactory.gen_alphanumeric()
    password = fauxfactory.gen_alphanumeric().title() + '1'
    # populate the form
    ui_user_add.details.organization.set_value(organization.name)
    ui_user_add.details.first_name.set_value(fauxfactory.gen_alphanumeric())
    ui_user_add.details.last_name.set_value(fauxfactory.gen_alphanumeric())
    ui_user_add.details.email.set_value(fauxfactory.gen_email())
    ui_user_add.details.username.set_value(username)
    ui_user_add.details.password.set_value(password)
    ui_user_add.details.password_confirm.set_value(password)
    # save the user
    time.sleep(5)
    ui_user_add.details.save.click()
    ui_user_add.list_table.wait_for_table_to_load()
    # verify the update took place api-side
    api_results = api_users_pg.get(username=username).results
    assert api_results, 'unable to verify creation of user'
    # check for expected url content
    expected_url_content = '/#/users/{0}'.format(api_results[0].id)
    assert expected_url_content in ui_user_add.driver.current_url
    # check that we find a row showing the updated username
    results = ui_user_add.list_table.query(lambda r: r.username.text == username)
    assert len(results) == 1, 'unable to verify creation of user'
    # check that the newly created resource has the row selection indicator
    assert ui_user_add.list_table.selected_row.username.text == username
