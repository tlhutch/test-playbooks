from selenium.webdriver.common.by import By

from common.ui.pages.base import TowerCrudPage
from common.ui.pages.page import Region

from common.ui.pages.regions import Table
from common.ui.pages.regions.tabs import PanelTab

from common.ui.pages.regions.cells import (
    DeleteActionCell,
    EditActionCell,
    JobStatusCell,
    NameCell,
    OrganizationCell,
    SyncStatusCell
)

from common.ui.pages.forms import (
    CodeMirror,
    Lookup,
    RadioButtons,
    TextInput,
    FormPanel,
)


class InventoryTable(Table):

    _root_locator = (By.CSS_SELECTOR, '#inventories_table')

    _row_spec = (
        ('name', NameCell),
        ('delete', DeleteActionCell),
        ('edit', EditActionCell),
        ('organization', OrganizationCell),
        ('job_status', JobStatusCell),
        ('sync_status', SyncStatusCell)
    )


class InventoriesEditDetails(FormPanel):

    _desc = ((By.CSS_SELECTOR, '[for=inventory_description]'), (By.XPATH, '..'))
    _name = ((By.CSS_SELECTOR, '[for=inventory_name]'), (By.XPATH, '..'))
    _orgz = ((By.CSS_SELECTOR, '[for=inventory_organization]'), (By.XPATH, '..'))
    _parse = (By.CSS_SELECTOR, '#inventory_variables_parse_type')
    _variables = (By.XPATH, "//div[@id='cm-variables-container']/div/div/textarea")

    @property
    def description(self):
        return TextInput(self.page, root_locator=self._desc)

    @property
    def name(self):
        return TextInput(self.page, root_locator=self._name)

    @property
    def organization(self):
        return Lookup(self.page, root_locator=self._orgz)

    @property
    def parse_type(self):
        return RadioButtons(self.page, root_extension=self._parse)

    @property
    def variables(self):
        return CodeMirror(self.page, root_locator=self._variables)


class Inventories(TowerCrudPage):

    _path = '/#/inventories/{index}'

    _details_tab = (By.ID, 'inventory_tab')
    _scan_job_templates_tab = (By.ID, 'scan_job_templates_tab')

    @property
    def table(self):
        return InventoryTable(self)

    @property
    def details(self):
        self.details_tab.enable()
        return InventoriesEditDetails(self)

    @property
    def scan_job_templates(self):
        self.scan_job_templates_tab.enable()
        return Region(self)

    @property
    def details_tab(self):
        return PanelTab(self, root_locator=self._details_tab)

    @property
    def scan_job_templates_tab(self):
        return PanelTab(self, root_locator=self._scan_job_templates_tab)
