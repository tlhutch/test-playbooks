from selenium.webdriver.common.by import By

from qe.ui.page import Region
from qe.ui.models.base import TowerPage
from qe.ui.models.forms import FormPanel

from qe.ui.models.regions import (
    ListPagination,
    ListTable,
    Tab,
    TagSearch,
)

__all__ = ['Inventories', 'InventoryAdd', 'InventoryEdit']


class Inventories(TowerPage):

    url_template = '/#/inventories'

    @property
    def list_pagination(self):
        return ListPagination(self)

    @property
    def list_table(self):
        return InventoriesTable(self)

    @property
    def list_search(self):
        return TagSearch(self)

    def wait_until_loaded(self):
        self.list_table.wait_for_table_to_load()


class InventoryAdd(Inventories):

    url_template = '/#/inventories/add'

    @property
    def details(self):
        DetailsTab(self).enable()
        return InventoryDetails(self)


class InventoryEdit(Inventories):

    url_template = '/#/inventories/{id}'

    @property
    def details(self):
        DetailsTab(self).enable()
        return InventoryDetails(self)

    @property
    def scan_job_templates(self):
        ScanJobTemplatesTab(self).enable()
        return FormPanel(self)


class InventoriesTable(ListTable):

    _root_locator = (By.CSS_SELECTOR, '#inventories_table')

    class Row(Region):

        _name = (By.CLASS_NAME, 'name-column')
        _organization = (By.CLASS_NAME, 'organization-column')
        _delete = (By.ID, 'delete-action')
        _edit = (By.ID, 'edit-action')

        @property
        def name(self):
            return self.find_element(*self._name)

        @property
        def organization(self):
            return self.find_element(*self._organization)

        @property
        def delete(self):
            return self.find_element(*self._delete)

        @property
        def edit(self):
            return self.find_element(*self._edit)


class DetailsTab(Tab):
    _root_locator = (By.ID, 'inventory_tab')


class ScanJobTemplatesTab(Tab):
    _root_locator = (By.ID, 'scan_job_templates_tab')


class InventoryDetails(FormPanel):

    _region_spec = {
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
        'description': {
            'region_type': 'text_input',
            'root_locator': (
                (By.CSS_SELECTOR, 'label[for=inventory_description]'),
                (By.XPATH, '..'))
        },
        'variables_parse_type': {
            'region_type': 'radio_buttons',
            'root_locator': (
                (By.CSS_SELECTOR, 'label[for=variables]'),
                (By.XPATH, '..'))
        },
    }
