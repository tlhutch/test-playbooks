from selenium.webdriver.common.by import By
from common.ui.pages import Base, BaseRegion, MainTab_Page
from common.ui.pages.forms import Form_Page, input_getter_by_name, input_setter_by_name
from common.ui.pages.regions.stream_container import Activity_Stream_Region
from common.ui.pages.regions.accordion import Accordion_Region, Accordion_Content
from common.ui.pages.regions.buttons import Activity_Stream_Button, Base_Button, Help_Button, Select_Button
from common.ui.pages.regions.lists import SortTable_Region
from common.ui.pages.regions.dialogs import Prompt_Dialog  # NOQA
from common.ui.pages.regions.search import Search_Region
from common.ui.pages.regions.pagination import Pagination_Region


class Users_Page(MainTab_Page):
    '''Describes users page'''
    _tab_title = "Users"
    _related = {
        'add': 'User_Create_Page',
        'edit': 'User_Edit_Page',
        'delete': 'Prompt_Dialog',
        'activity_stream': 'Users_Activity_Page',
    }
    _locators = {
        'table': (By.CSS_SELECTOR, '#users_table'),
        'pagination': (By.CSS_SELECTOR, '#user-pagination'),
    }


class Users_Activity_Page(Activity_Stream_Region):
    '''Activity stream page for all users'''
    _tab_title = "Users"
    _related = {
        'close': 'Users_Page',
    }


class User_Create_Page(Form_Page):
    '''Describes the users create page'''
    _tab_title = "Users"
    _breadcrumb_title = 'Create User'
    _related = {
        'save': 'Users_Page',
    }
    _locators = {
        'first_name': (By.CSS_SELECTOR, '#user_first_name'),
        'last_name': (By.CSS_SELECTOR, '#user_last_name'),
        'email': (By.CSS_SELECTOR, '#user_email'),
        'organization_lookup_btn': (By.CSS_SELECTOR, '#organization-lookup-btn'),
        'username': (By.CSS_SELECTOR, '#user_username'),
        'password': (By.CSS_SELECTOR, '#user_password'),
        'password_confirm': (By.CSS_SELECTOR, '#user_password_confirm'),
        'progbar': (By.CSS_SELECTOR, '#progbar'),
        'is_superuser': (By.CSS_SELECTOR, '#user_is_superuser_chbox'),
        'organization_btn': (By.CSS_SELECTOR, '#organization-lookup-btn'),
        'organization_name': (By.CSS_SELECTOR, "input[name='organization_name']"),
        'save_btn': (By.CSS_SELECTOR, '#user_save_btn'),
        'reset_btn': (By.CSS_SELECTOR, '#user_reset_btn'),
    }

    first_name = property(input_getter_by_name('first_name'), input_setter_by_name('first_name'))
    last_name = property(input_getter_by_name('last_name'), input_setter_by_name('last_name'))
    username = property(input_getter_by_name('username'), input_setter_by_name('username'))
    email = property(input_getter_by_name('email'), input_setter_by_name('email'))
    password = property(input_getter_by_name('password'), input_setter_by_name('password'))
    password_confirm = property(input_getter_by_name('password_confirm'), input_setter_by_name('password_confirm'))
    is_superuser = property(input_getter_by_name('is_superuser'), input_setter_by_name('is_superuser'))
    organization_name = property(input_getter_by_name('organization_name'), input_setter_by_name('organization_name'))

    @property
    def organization_btn(self):
        return Base_Button(self.testsetup, _root_locator=self._locators['organization_btn'], _item_class=NotImplementedError)


class User_Edit_Page(User_Create_Page):
    _tab_title = "Users"
    _related = {
        'Properties': Users_Page.__module__ + '.User_Properties_Region',
        'Credentials': Users_Page.__module__ + '.User_Credentials_Region',
        'Permissions': Users_Page.__module__ + '.User_Permissions_Region',
        'Projects': Users_Page.__module__ + '.User_Projects_Region',
        'Admin of Organizations': Users_Page.__module__ + '.User_AdminOfOrgs_Region',
        'Organizations': Users_Page.__module__ + '.User_Organizations_Region',
        'Teams': Users_Page.__module__ + '.User_Teams_Region',
    }

    @property
    def _breadcrumb_title(self):
        '''The breadcrumb title should always match object name'''
        return self.name

    @property
    def accordion(self):
        '''Returns an Accordion_Region object describing the accordion'''
        return Accordion_Region(self.testsetup, _related=self._related)


class User_Properties_Region(BaseRegion, User_Create_Page):
    '''Describes the properties accordion region'''
    _related = User_Create_Page._related
    _related.update({
        'activity_stream': 'User_Activity_Page',
    })

    @property
    def activity_stream_btn(self):
        return Activity_Stream_Button(self.testsetup, _item_class=self.get_related('activity_stream'))


class User_Activity_Page(Activity_Stream_Region):
    '''Activity stream page for a single organizations'''
    _tab_title = "Users"
    _related = {
        'close': 'User_Edit_Page',
    }


class User_Credentials_Region(Accordion_Content):
    '''Describes the credentials accordion region'''
    _tab_title = "Users"
    _related = {
        'add': 'User_Add_Credentials_Page',
    }


class User_Add_Credentials_Page(Base):
    '''Describes the page for adding users to a user'''
    _tab_title = "Users"
    _breadcrumb_title = 'Add Credentials'
    _related = {
        'select': 'User_Edit_Page',
    }
    _locators = {
        'table': (By.CSS_SELECTOR, '#credentials_table'),
        'pagination': (By.CSS_SELECTOR, '#credential-pagination'),
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


class User_Permissions_Region(Accordion_Content):
    '''Describes the permissions accordion region'''
    _tab_title = "Users"
    _related = {
        'add': 'User_Add_Permissions_Page',
    }


class User_Add_Permissions_Page(User_Add_Credentials_Page):
    '''Describes the page for adding permissions to a user'''
    _breadcrumb_title = 'Add Permissions'
    _locators = {
        'table': (By.CSS_SELECTOR, '#permissions_table'),
        'pagination': (By.CSS_SELECTOR, '#permission-pagination'),
    }


class User_AdminOfOrgs_Region(Accordion_Content):
    '''Describes the admin of organizations accordion region'''
    _tab_title = "Users"


class User_Organizations_Region(Accordion_Content):
    '''Describes the organizations accordion region'''
    _tab_title = "Users"


class User_Teams_Region(Accordion_Content):
    '''Describes the teams accordion region'''
    _tab_title = "Users"
