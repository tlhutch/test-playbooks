import fauxfactory
import pytest

pytestmark = [
    pytest.mark.ui,
    pytest.mark.nondestructive,
    pytest.mark.usefixtures(
        'authtoken',
        'install_basic_license',
        'maximized_window_size'
    )
]


@pytest.mark.usefixtures('authtoken')
def test_create_user(api_users_pg, ui_users_add):
    """Basic end-to-end verification for creating a user
    """
    # add user
    ui_users_add.details.first_name.set_text(fauxfactory.gen_alphanumeric())
    ui_users_add.details.last_name.set_text(fauxfactory.gen_alphanumeric())
    ui_users_add.details.email.set_text(fauxfactory.gen_email())

    un = fauxfactory.gen_alphanumeric()
    pw = 'ui_123_%s' % fauxfactory.gen_alphanumeric()

    ui_users_add.details.username.set_text(un)
    ui_users_add.details.password.set_text(pw)
    ui_users_add.details.confirm_password.set_text(pw)
    ui_users_add.details.organization.set_text('Default')

    ui_users_add.details.save.click()

    # search the table for the newly created user row
    results = ui_users_add.table.query(lambda r: r['username'].text == un)

    # verify newly created user row
    assert len(results) == 1, 'Expected table data not found'

    # verify that the newly created row is selected
    assert ui_users_add.table.row_is_selected(results[0]), (
        'Newly created user row unexpectedly unselected')

    # verify user data api side
    assert api_users_pg.get(username=un).count == 1, (
        'Unable to verify successful creation of user resource')


@pytest.mark.github('https://github.com/ansible/ansible-tower/issues/1199')
@pytest.mark.usefixtures('authtoken')
def test_update_user(api_users_pg, ui_users_edit):
    """Basic end-to-end functional test for updating an existing user
    """
    # get user data api side
    user_id = ui_users_edit.kwargs.get('index')
    api_user_data = api_users_pg.get(id=user_id).results[0]

    # query the table for the edited user
    results = ui_users_edit.table.query(
        lambda r: r['username'].text == api_user_data.username)

    # fail informatively if we don't find the row of the user we're editing
    assert len(results) == 1, 'Unable to find row of edited resource'

    # verify that the row selection indicator is displayed for the row
    # corresponding to the user we're editing
    assert ui_users_edit.table.row_is_selected(results[0]), (
        'Edited user row unexpectedly unselected')

    # make some data
    username = fauxfactory.gen_alphanumeric()
    password = 'UI_abc_123_%s' % fauxfactory.gen_alphanumeric()
    first_name = fauxfactory.gen_utf8()
    last_name = fauxfactory.gen_utf8()
    email = fauxfactory.gen_email()

    # update the user
    ui_users_edit.details.first_name.set_text(first_name)
    ui_users_edit.details.last_name.set_text(last_name)
    ui_users_edit.details.email.set_text(email)
    ui_users_edit.details.username.set_text(username)
    ui_users_edit.details.password.set_text(password)
    ui_users_edit.details.confirm_password.set_text(password)

    ui_users_edit.details.save.click()

    # get user data api side
    api_user_data = api_users_pg.get(id=user_id).results[0]

    # verify the update took place
    assert api_user_data.username == username, (
        'Unable to verify successful update of user resource')

    assert api_user_data.first_name == first_name, (
        'Unable to verify successful update of user resource')

    assert api_user_data.last_name == last_name, (
        'Unable to verify successful update of user resource')

    assert api_user_data.email == email, (
        'Unable to verify successful update of user resource')

    # query the table for the edited user
    results = ui_users_edit.table.query(
        lambda r: r['username'].text == api_user_data.username)

    # check that we find a row showing updated user data
    assert len(results) == 1, 'Unable to find row of updated resource'


@pytest.mark.skipif(True, reason='not implemented')
@pytest.mark.usefixtures('authtoken')
def test_delete_user(api_users_pg, ui_users):
    """Basic end-to-end verification for deleting a user
    """
    pass  # TODO: implement
