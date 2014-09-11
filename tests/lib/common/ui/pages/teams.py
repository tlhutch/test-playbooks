from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from common.ui.pages import Base, BaseRegion, Organizations_Page, Organization_Create_Page
from common.ui.pages.forms import input_getter, input_setter, input_getter_by_name, input_setter_by_name
from common.ui.pages.regions.stream_container import Activity_Stream_Region
from common.ui.pages.regions.accordion import Accordion_Region, Accordion_Content
from common.ui.pages.regions.buttons import Activity_Stream_Button, Base_Button, Add_Button, Help_Button, Select_Button
from common.ui.pages.regions.lists import SortTable_Region
from common.ui.pages.regions.dialogs import Prompt_Dialog
from common.ui.pages.regions.search import Search_Region
from common.ui.pages.regions.pagination import Pagination_Region


class Teams_Page(Organizations_Page):
    '''Describes teams page'''
    _base_url = "/#/teams/"
    _tab_title = "Teams"
    _related = {
        'add': 'Team_Create_Page',
        'edit': 'Team_Edit_Page',
        'delete': 'Prompt_Dialog',
        'activity_stream': 'Teams_Activity_Page',
    }
    _locators = {
        'table': (By.CSS_SELECTOR, '#teams_table'),
        'pagination': (By.CSS_SELECTOR, '#team-pagination'),
    }


class Teams_Activity_Page(Activity_Stream_Region):
    '''Activity stream page for all teams'''
    _tab_title = "Teams"
    _related = {
        'close': 'Teams_Page',
    }


class Team_Create_Page(Organization_Create_Page):
    '''Describes the teams create page'''
    _tab_title = "Teams"
    _breadcrumb_title = 'Create Team'
    _related = {
        'save': 'Teams_Page',
    }
    _locators = {
        'name': (By.CSS_SELECTOR, '#team_name'),
        'description': (By.CSS_SELECTOR, '#team_description'),
        'organization_btn': (By.CSS_SELECTOR, '#organization-lookup-btn'),
        'organization_name': (By.CSS_SELECTOR, "input[name='organization_name']"),
        'save_btn': (By.CSS_SELECTOR, '#team_save_btn'),
        'reset_btn': (By.CSS_SELECTOR, '#team_reset_btn'),
    }

    organization_name = property(input_getter_by_name('organization_name'), input_setter_by_name('organization_name'))


class Team_Edit_Page(Team_Create_Page):
    _tab_title = "Teams"
    _related = {
        'Properties': Teams_Page.__module__ + '.Team_Properties_Region',
        'Credentials': Teams_Page.__module__ + '.Team_Credentials_Region',
        'Permissions': Teams_Page.__module__ + '.Team_Permissions_Region',
        'Projects': Teams_Page.__module__ + '.Team_Projects_Region',
        'Users': Teams_Page.__module__ + '.Team_Users_Region',
    }

    @property
    def _breadcrumb_title(self):
        '''The breadcrumb title should always match object name'''
        return self.name

    @property
    def accordion(self):
        '''Returns an Accordion_Region object describing the accordion'''
        return Accordion_Region(self.testsetup, _related=self._related)


class Team_Properties_Region(BaseRegion, Team_Create_Page):
    '''Describes the properties accordion region'''
    _related = Team_Create_Page._related
    _related.update({
        'activity_stream': 'Team_Activity_Page',
    })

    @property
    def activity_stream_btn(self):
        return Activity_Stream_Button(self.testsetup, _item_class=self.get_related('activity_stream'))


class Team_Activity_Page(Activity_Stream_Region):
    '''Activity stream page for a single organizations'''
    _tab_title = "Teams"
    _related = {
        'close': 'Team_Edit_Page',
    }


class Team_Users_Region(Accordion_Content):
    '''Describes the properties accordion region'''
    _tab_title = "Teams"
    _related = {
        'add': 'Team_Add_Users_Page',
    }


class Team_Add_Users_Page(Base):
    '''Describes the page for adding users to a team'''
    _tab_title = "Teams"
    _breadcrumb_title = 'Add Users'
    _related = {
        'select': 'Team_Edit_Page',
    }
    _locators = {
        'table': (By.CSS_SELECTOR, '#users_table'),
        'pagination': (By.CSS_SELECTOR, '#user-pagination'),
    }

    @property
    def help_btn(self):
        return Help_Button(self.testsetup)

    @property
    def select_btn(self):
        return Select_Button(self.testsetup, _item_class=self.get_related('select'))

    @property
    def table(self):
        return SortTable_Region(self.testsetup, _root_locator=self._locators['table'])

    @property
    def pagination(self):
        return Pagination_Region(self.testsetup, _root_locator=self._locators['pagination'], _item_class=self.__class__)

    @property
    def search(self):
        return Search_Region(self.testsetup, _item_class=self.__class__)


class Team_Permissions_Region(Accordion_Content):
    '''Describes the permissions accordion region'''
    _tab_title = "Teams"
    _related = {
        'add': 'Team_Add_Permissions_Page',
    }


class Team_Add_Permissions_Page(Team_Add_Users_Page):
    '''Describes the page for adding permissions to a team'''
    _breadcrumb_title = 'Add Permissions'
    _locators = {
        'table': (By.CSS_SELECTOR, '#permissions_table'),
        'pagination': (By.CSS_SELECTOR, '#permission-pagination'),
    }


class Team_Projects_Region(Accordion_Content):
    '''Describes the projects accordion region'''
    _tab_title = "Teams"
    _related = {
        'add': 'Team_Add_Projects_Page',
    }


class Team_Add_Projects_Page(Team_Add_Users_Page):
    '''Describes the page for adding projects to a team'''
    _breadcrumb_title = 'Add Project'
    _locators = {
        'table': (By.CSS_SELECTOR, '#projects_table'),
        'pagination': (By.CSS_SELECTOR, '#project-pagination'),
    }


class Team_Credentials_Region(Accordion_Content):
    '''Describes the credentials accordion region'''
    _tab_title = "Teams"
    _related = {
        'add': 'Team_Add_Credentials_Page',
    }


class Team_Add_Credentials_Page(Team_Add_Users_Page):
    '''Describes the page for adding credentials to a team'''
    _breadcrumb_title = 'Add Credentials'
    _locators = {
        'table': (By.CSS_SELECTOR, '#credentials_table'),
        'pagination': (By.CSS_SELECTOR, '#credential-pagination'),
    }
