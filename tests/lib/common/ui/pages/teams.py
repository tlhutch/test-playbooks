from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from common.ui.pages import Base, BaseRegion, Organizations_Page, Organization_Create_Page
from common.ui.pages.forms import input_getter, input_setter, input_getter_by_name, input_setter_by_name
from common.ui.pages.regions.stream_container import Activity_Stream_Region
from common.ui.pages.regions.accordion import Accordion_Region
from common.ui.pages.regions.buttons import Activity_Stream_Button, Base_Button, Add_Button, Help_Button
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


