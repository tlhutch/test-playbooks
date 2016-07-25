from selenium.webdriver.common.by import By

from common.ui.page import Region
from common.ui.models.base import TowerPage
from common.ui.models.forms import FormPanel 
from common.ui.models.forms import Lookup

from common.ui.models.regions import (
    ListPagination,
    ListTable,
    Tab,
    TagSearch,
    StatusIcon,
)


__all__ = ['Teams', 'TeamAdd', 'TeamEdit']


class Teams(TowerPage):

    url_template = '/#/teams'

    forms = []

    @property
    def list_pagination(self):
        return ListPagination(self)

    @property
    def list_table(self):
        return TeamsTable(self)

    @property
    def list_search(self):
        return TagSearch(self)

    def wait_until_loaded(self):
        self.list_table.wait_for_table_to_load()


class TeamAdd(Teams):

    url_template = '/#/teams/add'

    @property
    def forms(self):
        return [self.details]

    @property
    def details(self):
        DetailsTab(self).enable()
        return TeamDetails(self)


class TeamEdit(Teams):

    url_template = '/#/teams/{id}'

    @property
    def forms(self):
        return [self.details]

    @property
    def details(self):
        DetailsTab(self).enable()
        return TeamDetails(self)

    @property
    def granted_permissions(self):
        GrantedPermissionsTab(self).enable()
        return FormPanel(self)

    @property
    def users(self):
        UsersTab(self).enable()
        return FormPanel(self)


class DetailsTab(Tab):
    _root_locator = (By.ID, 'team_tab')

class GrantedPermissionsTab(Tab):
    _root_locator = (By.ID, 'roles_tab')

class UsersTab(Tab):
    _root_locator = (By.ID, 'teams_tab')


class TeamDetails(FormPanel):

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
    }


class TeamsTable(ListTable):

    _root_locator = (By.CSS_SELECTOR, '#teams_table')

    class Row(Region):

        _name = (By.CLASS_NAME, 'name-column')
        _description = (By.CLASS_NAME, 'description-column')
        _organization = (By.CLASS_NAME, 'organization-column')
        _edit = (By.ID, 'edit-action')
        _delete = (By.ID, 'delete-action')
        
        @property
        def name(self):
            return self.find_element(*self._name)

        @property
        def description(self):
            return self.find_element(*self.description)

        @property
        def organization(self):
            return self.find_element(*self._organization)

        @property
        def delete(self):
            return self.find_element(*self._delete)

        @property
        def edit(self):
            return self.find_element(*self._edit)
