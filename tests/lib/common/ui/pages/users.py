from selenium.webdriver.common.by import By

from common.ui.pages.base import TowerCrudPage
from common.ui.pages.page import Region
from common.ui.pages.regions import Table

from common.ui.pages.regions.tabs import PanelTab

from common.ui.pages.forms import (
    FormPanel,
    TextInput,
    Lookup,
    Password,
)

from common.ui.pages.regions.cells import (
    UserNameCell,
    FirstNameCell,
    LastNameCell,
    EditActionCell,
    DeleteActionCell
)


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

    _first_name = ((By.CSS_SELECTOR, '[for=first_name]'), (By.XPATH, '..'))
    _last_name = ((By.CSS_SELECTOR, '[for=last_name]'), (By.XPATH, '..'))
    _email = ((By.CSS_SELECTOR, '[for=email]'), (By.XPATH, '..'))
    _username = ((By.CSS_SELECTOR, '[for=username]'), (By.XPATH, '..'))
    _password = ((By.CSS_SELECTOR, '[for=password]'), (By.XPATH, '..'))
    _confirm_password = ((By.CSS_SELECTOR, '[for=password_confirm]'), (By.XPATH, '..'))
    _organization = ((By.CSS_SELECTOR, '[for=organization]'), (By.XPATH, '..'))
    _organization_api_error = (By.CSS_SELECTOR, '#user-organization-api-error')

    @property
    def first_name(self):
        return TextInput(
            self.page,
            root_locator=self._first_name)

    @property
    def last_name(self):
        return TextInput(
            self.page,
            root_locator=self._last_name)

    @property
    def email(self):
        return TextInput(
            self.page,
            root_locator=self._email)

    @property
    def username(self):
        return TextInput(
            self.page,
            root_locator=self._username)

    @property
    def password(self):
        return Password(
            self.page,
            root_locator=self._password)

    @property
    def confirm_password(self):
        return Password(
            self.page,
            root_locator=self._confirm_password)

    @property
    def organization(self):
        return Lookup(
            self.page,
            root_locator=self._organization)

    @property
    def organization_api_error(self):
        return Region(
            self.page,
            root_locator=self._organization_api_error)


class Users(TowerCrudPage):

    _path = '/#/users/{index}'

    _details_tab = (By.ID, 'user_tab')

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
