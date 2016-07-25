from selenium.webdriver.common.by import By

from common.ui.pages.base import TowerCrudPage
from common.ui.pages.forms import FormPanel


class InventoryScripts(TowerCrudPage):

    _path = '/#/inventory_scripts/{index}'

    @property
    def forms(self):
        return [self.details]

    @property
    def details(self):
        return InventoryScriptsDetails(self)


class InventoryScriptsDetails(FormPanel):

    _region_spec = {
        'description': {
            'region_type': 'text_input',
            'root_locator': (
                (By.CSS_SELECTOR, 'label[for=description]'),
                (By.XPATH, '..'))
        },
        'name': {
            'required': True,
            'region_type': 'text_input',
            'root_locator': (
                (By.CSS_SELECTOR, 'label[for=name]'),
                (By.XPATH, '..'))
        },
        'organization': {
            'required': True,
            'region_type': 'lookup',
            'root_locator': (
                (By.CSS_SELECTOR, 'label[for=organization]'),
                (By.XPATH, '..'))
        },
        'script': {
            'region_type': 'code_mirror',
            'required': True,
            'root_locator': (
                (By.CSS_SELECTOR, 'label[for=script]'),
                (By.XPATH, '..'))
        },
    }
