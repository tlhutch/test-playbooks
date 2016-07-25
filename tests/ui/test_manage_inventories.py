'''
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


def test_group_search_visibility(ui_manage_inventory):
    """Verify group panel search region is not displayed when no groups are
    associated with the inventory
    """
    assert ui_manage_inventory.groups_panel.search.is_displayed(), (
        'groups panel search region unexpectedly not displayed')

    for _ in xrange(len(ui_manage_inventory.groups_table.rows)):
        row = ui_manage_inventory.groups_table.rows[0]
        modal = row['delete'].click()
        modal.delete_hosts.click()
        modal.delete()
        ui_manage_inventory.wait_for_spinny()

    assert not ui_manage_inventory.groups_panel.search.is_displayed(), (
        'groups panel search region unexpectedly displayed')


def test_host_search_visibility(ui_manage_inventory):
    """Verify host panel search region is not displayed when no groups are
    associated with the inventory
    """
    assert ui_manage_inventory.hosts_panel.search.is_displayed(), (
        'hosts panel search region unexpectedly not displayed')

    for row in ui_manage_inventory.hosts_table.rows:
        row['delete'].click().delete.click()

    assert not ui_manage_inventory.hosts_panel.search.is_displayed(), (
        'hosts panel search region unexpectedly displayed')
'''
