from selenium.webdriver.common.by import By

from common.ui.pages.base import TowerCrudPage
from common.ui.pages.page import Region

from common.ui.pages.regions import Table
from common.ui.pages.regions.tabs import PanelTab
from common.ui.pages.forms import FormPanel

from common.ui.pages.regions.cells import (NameCell, DeleteActionCell, EditActionCell, OrganizationCell, JobStatusCell,
                                           SyncStatusCell)


class InventoriesTable(Table):

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

    _region_spec = {
        'description': {
            'region_type': 'text_input',
            'root_locator': (
                (By.CSS_SELECTOR, 'label[for=inventory_description]'),
                (By.XPATH, '..'))
        },
        'name': {
            'required': True,
            'region_type': 'text_input',
            'root_locator': (
                (By.CSS_SELECTOR, 'label[for=inventory_name]'),
                (By.XPATH, '..'))
        },
        'organization': {
            'required': True,
            'region_type': 'lookup',
            'root_locator': (
                (By.CSS_SELECTOR, 'label[for=organization]'),
                (By.XPATH, '..'))
        },
        'variables_parse_type': {
            'region_type': 'radio_buttons',
            'root_locator': (
                (By.CSS_SELECTOR, 'label[for=variables]'),
                (By.XPATH, '..'))
        },
    }


class Inventories(TowerCrudPage):

    _path = '/#/inventories/{index}'

    _details_tab = (By.ID, 'inventory_tab')
    _scan_job_templates_tab = (By.ID, 'scan_job_templates_tab')

    @property
    def forms(self):
        return [self.details]

    @property
    def table(self):
        return InventoriesTable(self)

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
