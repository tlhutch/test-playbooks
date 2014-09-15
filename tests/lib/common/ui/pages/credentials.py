from selenium.webdriver.common.by import By
from common.ui.pages import MainTab_Page
from common.ui.pages.forms import Form_Page, input_getter_by_name, input_setter_by_name
from common.ui.pages.regions.stream_container import Activity_Stream_Region
from common.ui.pages.regions.buttons import Activity_Stream_Button, Base_Button, Add_Button, Help_Button, Select_Button  # NOQA
from common.ui.pages.regions.dialogs import Prompt_Dialog  # NOQA


class Credentials_Page(MainTab_Page):
    '''Describes credentials page'''
    _tab_title = "Credentials"
    _related = {
        'add': 'Credential_Create_Page',
        'edit': 'Credential_Edit_Page',
        'delete': 'Prompt_Dialog',
        'activity_stream': 'Credentials_Activity_Page',
    }
    _locators = {
        'table': (By.CSS_SELECTOR, '#credentials_table'),
        'pagination': (By.CSS_SELECTOR, '#credential-pagination'),
    }


class Credentials_Activity_Page(Activity_Stream_Region):
    '''Activity stream page for all credentials'''
    _tab_title = "Credentials"
    _related = {
        'close': 'Credentials_Page',
    }


class Credential_Create_Page(Form_Page):
    '''Describes the credentials create page'''
    _tab_title = "Credentials"
    _breadcrumb_title = 'Create Credential'
    _related = {
        'save': 'Credentials_Page',
    }
    _locators = {
        'name': (By.CSS_SELECTOR, '#credential_name'),
        'description': (By.CSS_SELECTOR, '#credential_description'),
        'owner': (By.CSS_SELECTOR, "#input[name='owner']"),
        'owner_help': (By.CSS_SELECTOR, '#awp-owner'),
        'user_btn': (By.CSS_SELECTOR, '#user-lookup-btn'),
        'user_username': (By.CSS_SELECTOR, "input[name='user_username']"),
        'team_btn': (By.CSS_SELECTOR, '#team-lookup-btn'),
        'team_name': (By.CSS_SELECTOR, "input[name='team_name']"),
        'credential_kind': (By.CSS_SELECTOR, '#credential_kind'),
        'kind_help': (By.CSS_SELECTOR, '#awp-kind'),
        'save_btn': (By.CSS_SELECTOR, '#credential_save_btn'),
        'reset_btn': (By.CSS_SELECTOR, '#credential_reset_btn'),
    }

    name = property(input_getter_by_name('name'), input_setter_by_name('name'))
    description = property(input_getter_by_name('description'), input_setter_by_name('description'))
    owner = property(input_getter_by_name('owner'), input_setter_by_name('owner'))
    user_username = property(input_getter_by_name('user_username'), input_setter_by_name('user_username'))
    team_name = property(input_getter_by_name('team_name'), input_setter_by_name('team_name'))
    credential_kind = property(input_getter_by_name('credential_kind'), input_setter_by_name('credential_kind'))


class Credential_Edit_Page(Credential_Create_Page):
    _tab_title = "Credentials"

    @property
    def _breadcrumb_title(self):
        '''The breadcrumb title should always match object name'''
        return self.name


class Credential_Activity_Page(Activity_Stream_Region):
    '''Activity stream page for a single organizations'''
    _tab_title = "Credentials"
    _related = {
        'close': 'Credential_Edit_Page',
    }
