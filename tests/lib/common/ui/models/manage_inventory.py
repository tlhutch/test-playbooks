'''
from selenium.webdriver.common.by import By

from common.ui.pages.base import TowerPage

from common.ui.pages.regions import Clickable
from common.ui.pages.regions import ListPanel
from common.ui.pages.regions import Table

from common.ui.pages.regions import LegacyDeleteDialog

from common.ui.pages.regions.cells import (
    NameCell,
    SyncStatusCell,
    JobStatusCell,
    GroupUpdateActionCell,
    CopyActionCell,
    EditActionCell,
    DeleteActionCell,
)


class GroupDeleteActionCell(DeleteActionCell):

    _spinny = False

    def after_click(self):
        return LegacyDeleteDialog(self.page)


class ManageInventoryGroupsTable(Table):
    _root_locator = (By.CSS_SELECTOR, '#groups_table')

    _row_spec = (
        ('name', NameCell),
        ('sync_status', SyncStatusCell),
        ('job_status', JobStatusCell),
        ('group_update', GroupUpdateActionCell),
        ('copy', CopyActionCell),
        ('edit', EditActionCell),
        ('delete', GroupDeleteActionCell)
    )


class ManageInventoryHostsTable(Table):
    _root_locator = (By.CSS_SELECTOR, '#hosts_table')

    _row_spec = (
        ('name', NameCell),
        ('delete', DeleteActionCell),
        ('job_status', JobStatusCell),
        ('copy', CopyActionCell),
        ('edit', EditActionCell)
    )


class ManageInventoryGroupsPanel(ListPanel):
    _root_locator = (By.CSS_SELECTOR, '#groups-list')
    _run = (By.CSS_SELECTOR, '[aw-tool-tip*="Run a command"]')

    @property
    def run_commands(self):
        return Clickable(self.page, root_locator=self._run, spinny=True)


class ManageInventoryHostsPanel(ListPanel):
    _root_locator = (By.CSS_SELECTOR, '#host-list-container')


class ManageInventory(TowerPage):

    _path = '/#/inventories/{index}/manage'

    @property
    def groups_table(self):
        return ManageInventoryGroupsTable(self)

    @property
    def groups_panel(self):
        return ManageInventoryGroupsPanel(self)

    @property
    def hosts_table(self):
        return ManageInventoryHostsTable(self)

    @property
    def hosts_panel(self):
        return ManageInventoryHostsPanel(self)

    def __init__(self, base_url, driver, index='', **kwargs):

        super(ManageInventory, self).__init__(
            base_url, driver, index=index, **kwargs)
'''
