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


@pytest.mark.skipif(True, reason='not implemented')
@pytest.mark.usefixtures('authtoken')
def test_update_user(api_users_pg, ui_users_edit):
    """Basic end-to-end verification for updating a user
    """
    pass  # TODO: implement


@pytest.mark.skipif(True, reason='not implemented')
@pytest.mark.usefixtures('authtoken')
def test_delete_user(api_users_pg, ui_users):
    """Basic end-to-end verification for deleting a user
    """
    pass  # TODO: implement
