import pytest

pytestmark = [
    pytest.mark.ui,
    pytest.mark.nondestructive,
    pytest.mark.usefixtures('maximized_window_size')
]


@pytest.mark.skipif(True, reason='not implemented')
@pytest.mark.usefixtures('authtoken')
def test_delete_inventory(inventory, ui_inventories):
    """Basic end-to-end verification for deleting an inventory
    """
    pass  # TODO: implement


@pytest.mark.skipif(True, reason='not implemented')
@pytest.mark.usefixtures('authtoken')
def test_create_inventory(api_inventories_pg, ui_inventories_add):
    """Basic end-to-end verification for creating an inventory
    """
    pass  # TODO: implement


@pytest.mark.skipif(True, reason='not implemented')
@pytest.mark.usefixtures('authtoken')
def test_update_inventory(api_inventories_pg, ui_inventories_edit):
    """Basic end-to-end verification for updating an inventory
    """
    pass  # TODO: implement
