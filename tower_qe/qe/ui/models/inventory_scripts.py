from selenium.webdriver.common.by import By

from qe.ui.models.base import TowerPage
from qe.ui.models.forms import FormPanel

__all__ = ['InventoryScripts']


class InventoryScripts(TowerPage):

    _path = '/#/inventory_scripts/{id}'

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
