'''
import pytest

pytestmark = [
    pytest.mark.ui,
    pytest.mark.nondestructive,
    pytest.mark.usefixtures('maximized_window_size')
]


@pytest.mark.skipif(True, reason='not implemented')
@pytest.mark.usefixtures('authtoken')
def test_create_inventory_script(api_inventory_scripts_pg, ui_inventory_scripts_add):
    """Basic end-to-end verification for creating an inventory script
    """
    pass  # TODO: implement


@pytest.mark.skipif(True, reason='not implemented')
@pytest.mark.usefixtures('authtoken')
def test_update_inventory_script(api_inventory_scripts_pg,
                                 inventory_script, ui_inventory_scripts_edit):
    """Basic end-to-end verification for updating an inventory script
    """
    pass  # TODO: implement


@pytest.mark.skipif(True, reason='not implemented')
@pytest.mark.usefixtures('authtoken')
def test_delete_inventory_script(inventory_script, ui_inventory_scripts):
    """Basic end-to-end verification for deleting an inventory script
    """
    pass  # TODO: implement
'''
