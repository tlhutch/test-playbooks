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


@pytest.mark.skipif(True, reason='not implemented')
def test_delete_credential(inventory, api_inventories_pg, ui_credentials):
    """Basic end-to-end verification for deleting a credential
    """
    pass  # TODO: implement


@pytest.mark.skipif(True, reason='not implemented')
def test_create_credential(api_credentials_pg, ui_credentials_add):
    """Basic end-to-end verification for creating a credential
    """
    pass  # TODO: implement


@pytest.mark.skipif(True, reason='not implemented')
def test_update_credential(api_credentials_pg, ui_credentials_edit):
    """Basic end-to-end verification for updating a credential
    """
    pass  # TODO: implement


@pytest.mark.skipif(True, reason='not implemented')
def test_filter(ssh_credential, api_credentials_pg, ui_credentials):
    """Verify table filtering
    """
    pass  # TODO: implement


@pytest.mark.skipif(True, reason='not implemented')
def test_filter_notfound(ssh_credential, ui_credentials):
    """Verify table filtering using a bogus value
    """
    pass  # TODO: implement
