from selenium.webdriver.common.by import By

from common.ui.pages.base import TowerCrudPage
from common.ui.pages.regions import Table
from common.ui.pages.forms import FormPanel
from common.ui.pages.regions.tabs import PanelTab

from common.ui.pages.regions.cells import (NameCell, DescriptionCell, OrganizationCell, EditActionCell,
                                           DeleteActionCell)


class TeamsTable(Table):

    _root_locator = (By.CSS_SELECTOR, '#teams_table')

    _row_spec = (
        ('name', NameCell),
        ('description', DescriptionCell),
        ('organization', OrganizationCell),
        ('edit', EditActionCell),
        ('delete', DeleteActionCell)
    )


class TeamsDetails(FormPanel):

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


class Teams(TowerCrudPage):

    _path = '/#/teams/{index}'

    _details_tab = (By.CSS_SELECTOR, '#team_tab')
    _credentials_tab = (By.CSS_SELECTOR, '#credentials_tab')
    _permissions_tab = (By.CSS_SELECTOR, '#permissions_tab')
    _projects_tab = (By.CSS_SELECTOR, '#team_tab')
    _users_tab = (By.CSS_SELECTOR, '#users_tab')

    @property
    def forms(self):
        return [self.details]

    @property
    def details(self):
        self.details_tab.enable()
        return TeamsDetails(self)

    @property
    def credentials(self):
        self.credentials_tab.enable()
        return FormPanel(self)

    @property
    def permissions(self):
        self.permissions_tab.enable()
        return FormPanel(self)

    @property
    def projects(self):
        self.projects_tab.enable()
        return FormPanel(self)

    @property
    def users(self):
        self.users_tab.enable()
        return FormPanel(self)

    @property
    def details_tab(self):
        return PanelTab(self, root_locator=self._details_tab)

    @property
    def credentials_tab(self):
        return PanelTab(self, root_locator=self._credentials_tab)

    @property
    def permissions_tab(self):
        return PanelTab(self, root_locator=self._permissions_tab)

    @property
    def projects_tab(self):
        return PanelTab(self, root_locator=self._projects_tab)

    @property
    def users_tab(self):
        return PanelTab(self, root_locator=self._users_tab)

    @property
    def table(self):
        return TeamsTable(self)
