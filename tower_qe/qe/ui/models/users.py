from selenium.webdriver.common.by import By

from qe.ui.page import Region
from qe.ui.models.base import TowerPage
from qe.ui.models.forms import FormPanel
from qe.ui.models.forms import Lookup

from qe.ui.models.regions import (
    ListPagination,
    ListTable,
    Tab,
    TagSearch,
)


__all__ = ['Users', 'UserAdd', 'UserEdit']


class Users(TowerPage):

    url_template = '/#/users'

    @property
    def list_pagination(self):
        return ListPagination(self)

    @property
    def list_table(self):
        return UsersTable(self)

    @property
    def list_search(self):
        return TagSearch(self)

    def wait_until_loaded(self):
        self.list_table.wait_for_table_to_load()


class UserAdd(Users):

    url_template = '/#/users/add'

    @property
    def details(self):
        DetailsTab(self).enable()
        return UserDetails(self)


class UserEdit(Users):

    url_template = '/#/users/{id}'

    @property
    def details(self):
        DetailsTab(self).enable()
        return UserDetails(self)

    @property
    def organizations(self):
        OrganizationsTab(self).enable()
        return FormPanel(self)

    @property
    def granted_permissions(self):
        GrantedPermissionsTab(self).enable()
        return FormPanel(self)

    @property
    def teams(self):
        Tab(self).enable()
        return FormPanel(self)


class UsersTable(ListTable):

    _root_locator = (By.CSS_SELECTOR, '#users_table')

    class Row(Region):

        _username = (By.CLASS_NAME, 'username-column')
        _first_name = (By.CLASS_NAME, 'first_name-column')
        _last_name = (By.CLASS_NAME, 'last_name-column')
        _edit = (By.ID, 'edit-action')
        _delete = (By.ID, 'delete-action')

        @property
        def username(self):
            return self.find_element(*self._username)

        @property
        def first_name(self):
            return self.find_element(*self._first_name)

        @property
        def last_name(self):
            return self.find_element(*self._last_name)

        @property
        def edit(self):
            return self.find_element(*self._edit)

        @property
        def delete(self):
            return self.find_element(*self._delete)


class DetailsTab(Tab):
    _root_locator = (By.ID, 'user_tab')


class OrganizationsTab(Tab):
    _root_locator = (By.ID, 'organizations_tab')


class GrantedPermissionsTab(Tab):
    _root_locator = (By.ID, 'roles_tab')


class TeamsTab(Tab):
    _root_locator = (By.ID, 'teams_tab')


class UserDetails(FormPanel):

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
        'playbook': {
            'region_type': 'select',
            'root_locator': (
                (By.CSS_SELECTOR, 'label[for=user_type]'),
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

    _organization = (
        (By.CSS_SELECTOR, '[for=organization]'),
        (By.XPATH, '..'))

    @property
    def organization(self):
        return Lookup(self.page, root_locator=self._organization)
