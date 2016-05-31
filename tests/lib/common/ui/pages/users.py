from selenium.webdriver.common.by import By

from common.ui.pages.base import TowerCrudPage
from common.ui.pages.page import Region
from common.ui.pages.regions import Table

from common.ui.pages.regions.tabs import PanelTab
from common.ui.pages.forms import FormPanel
from common.ui.pages.forms import Lookup

from common.ui.pages.regions.cells import (UserNameCell, FirstNameCell, LastNameCell, EditActionCell, DeleteActionCell)


class UsersTable(Table):

    _root_locator = (By.CSS_SELECTOR, '#users_table')

    _row_spec = (
        ('username', UserNameCell),
        ('first_name', FirstNameCell),
        ('last_name', LastNameCell),
        ('edit', EditActionCell),
        ('delete', DeleteActionCell)
    )


class UserDetailForm(FormPanel):

    _region_spec = {
        'first_name': {
            'required': True,
            'region_type': 'text_input',
            'root_locator': (
                (By.CSS_SELECTOR, 'label[for=first_name]'),
                (By.XPATH, '..'))
        },
        'last_name': {
            'required': True,
            'region_type': 'text_input',
            'root_locator': (
                (By.CSS_SELECTOR, 'label[for=last_name]'),
                (By.XPATH, '..'))
        },
        'email': {
            'required': True,
            'region_type': 'email',
            'root_locator': (
                (By.CSS_SELECTOR, 'label[for=email]'),
                (By.XPATH, '..'))
        },
        'username': {
            'required': True,
            'region_type': 'text_input',
            'root_locator': (
                (By.CSS_SELECTOR, 'label[for=username]'),
                (By.XPATH, '..'))
        },
        'superuser': {
            'region_type': 'checkbox',
            'root_locator': (
                (By.ID, 'user_is_superuser_chbox'),
                (By.XPATH, '..'),
                (By.XPATH, '..'))
        },
        'password': {
            'region_type': 'password',
            'root_locator': (
                (By.CSS_SELECTOR, 'label[for=password]'),
                (By.XPATH, '..'))
        },
        'password_confirm': {
            'region_type': 'password',
            'root_locator': (
                (By.CSS_SELECTOR, 'label[for=password_confirm]'),
                (By.XPATH, '..'))
        },
    }

    _organization = ((By.CSS_SELECTOR, '[for=organization]'), (By.XPATH, '..'))
    _organization_api_error = (By.CSS_SELECTOR, '#user-organization-api-error')

    @property
    def organization_api_error(self):
        return Region(self.page, root_locator=self._organization_api_error)

    @property
    def organization(self):
        return Lookup(self.page, root_locator=self._organization)


class Users(TowerCrudPage):

    _path = '/#/users/{index}'

    _details_tab = (By.ID, 'user_tab')

    @property
    def forms(self):
        return [self.details]

    @property
    def table(self):
        return UsersTable(self)

    @property
    def details_tab(self):
        return PanelTab(self, root_locator=self._details_tab)

    @property
    def details(self):
        self.details_tab.enable()
        return UserDetailForm(self)
