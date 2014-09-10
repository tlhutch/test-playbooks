from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from common.ui.pages import Base, BaseRegion
from common.ui.pages.forms import input_getter, input_setter
from common.ui.pages.regions.stream_container import Activity_Stream_Region
from common.ui.pages.regions.accordion import Accordion_Region
from common.ui.pages.regions.buttons import Activity_Stream_Button, Base_Button, Add_Button, Help_Button
from common.ui.pages.regions.lists import SortTable_Region
from common.ui.pages.regions.dialogs import Prompt_Dialog
from common.ui.pages.regions.search import Search_Region
from common.ui.pages.regions.pagination import Pagination_Region


class Users_Page(Base):
    '''Describes the Users page'''
    _tab_title = "Users"

    # Search form
    _search_widget_locator = (By.CSS_SELECTOR, '#search-widget-container')
    _search_select_locator = (By.CSS_SELECTOR, '#search-field-ddown')
    _search_value_locator = (By.CSS_SELECTOR, '#search-value-input')

    # Results table
    _table_locator = (By.CSS_SELECTOR, '#users_table')

    @property
    def add_btn(self):
        return Add_Button(self.testsetup, _item_class=User_Create_Page)

    @property
    def activity_stream_btn(self):
        return Activity_Stream_Button(self.testsetup, _item_class=Users_Activity_Page)

    def open(self, id):
        super(Users_Page, self).open('/#/users/%d' % id)
        return User_Edit_Page(self.testsetup)

    @property
    def table(self):
        # FIXME - doesn't work yet
        _region_map = {
            '.name-column': User_Edit_Page,
            '#edit-action': User_Edit_Page,
            '#delete-action': Prompt_Dialog,
        }
        return SortTable_Region(self.testsetup, _root_locator=self._table_locator, _region_map=_region_map)

    @property
    def pagination(self):
        return Pagination_Region(self.testsetup, _item_class=Users_Page)

    @property
    def search(self):
        return Search_Region(self.testsetup, _item_class=Users_Page)


class Users_Activity_Page(Activity_Stream_Region):
    '''Activity stream page for all users'''
    _tab_title = "Users"
    _item_class = Users_Page


class User_Create_Page(Base):
    '''Describes the user create page'''

    _tab_title = "Users"
    _breadcrumb_title = 'Create User'
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
    }
    _org_lookup_btn_locator = (By.CSS_SELECTOR, '#organization-lookup-btn')
    _save_btn_locator = (By.CSS_SELECTOR, '#user_save_btn')
    _reset_btn_locator = (By.CSS_SELECTOR, '#user_reset_btn')

    first_name = property(input_getter(_locators['first_name']), input_setter(_locators['first_name']))
    last_name = property(input_getter(_locators['last_name']), input_setter(_locators['last_name']))
    username = property(input_getter(_locators['username']), input_setter(_locators['username']))
    email = property(input_getter(_locators['email']), input_setter(_locators['email']))
    password = property(input_getter(_locators['password']), input_setter(_locators['password']))
    password_confirm = property(input_getter(_locators['password_confirm']), input_setter(_locators['password_confirm']))
    is_superuser = property(input_getter(_locators['is_superuser']), input_setter(_locators['is_superuser']))

    @property
    def org_lookup_btn(self):
        return Base_Button(self.testsetup, _root_locator=self._org_lookup_btn_locator, _item_class=NotImplementedError)

    @property
    def save_btn(self):
        return Base_Button(self.testsetup, _root_locator=self._save_btn_locator, _item_class=Users_Page)

    @property
    def reset_btn(self):
        return Base_Button(self.testsetup, _root_locator=self._reset_btn_locator, _item_class=User_Create_Page)


class User_Edit_Properties_Region(BaseRegion, User_Create_Page):
    '''Describes the user edit accordion region'''

    @property
    def activity_stream_btn(self):
        return Activity_Stream_Button(self.testsetup, _item_class=User_Activity_Page)


class User_Users_Page(Base):
    '''Describes the user users page'''
    _tab_title = "Users"
    _breadcrumb_title = "Add Users"
    _table_locator = (By.CSS_SELECTOR, '#users_table')

    @property
    def add_btn(self):
        return Add_Button(self.testsetup, _item_class=NotImplementedError)

    @property
    def help_btn(self):
        return Help_Button(self.testsetup, _item_class=NotImplementedError)

    @property
    def users(self):
        return SortTable_Region(self.testsetup, _root_locator=self._table_locator)


class User_Admins_Page(Base):
    '''Describes the user admin page'''
    _tab_title = "Users"
    _breadcrumb_title = "Add Administrators"
    _table_locator = (By.CSS_SELECTOR, '#admins_table')

    @property
    def help_btn(self):
        return Help_Button(self.testsetup, _item_class=NotImplementedError)


class User_Edit_Users_Region(BaseRegion):
    '''Describes the user users region'''
    _tab_title = "Users"
    _search_widget_locator = (By.CSS_SELECTOR, '#search-widget-container')
    _table_locator = (By.CSS_SELECTOR, '#users_table')
    _add_btn_locator = (By.CSS_SELECTOR, '#add_btn')

    @property
    def _breadcrumb_title(self):
        '''The breadcrumb title should always match user name'''
        return self.name

    @property
    def add_btn(self):
        return Add_Button(self.testsetup, _item_class=User_Users_Page, _root_element=self.find_element(*self._add_btn_locator))

    @property
    def users(self):
        return SortTable_Region(self.testsetup, _root_locator=_self.table_locator)


class User_Edit_Admins_Region(User_Edit_Users_Region):
    '''Describes the user administrators region'''
    _tab_title = "Users"
    _search_widget_locator = (By.CSS_SELECTOR, '#search-widget-container')
    _table_locator = (By.CSS_SELECTOR, '#admins_table')

    @property
    def _breadcrumb_title(self):
        '''The breadcrumb title should always match user name'''
        return self.name

    @property
    def add_btn(self):
        return Add_Button(self.testsetup, _item_class=User_Admins_Page, _root_element=self.find_element(*self._add_btn_locator))


# class User_Edit_Page(Base):
class User_Edit_Page(User_Create_Page):
    _tab_title = "Users"
    _region_map = {"Properties": User_Edit_Properties_Region,
                   "Credentials": NotImplementedError,
                   "Permissions": NotImplementedError,
                   "Admin of Organizations": NotImplementedError,
                   "Organizations": NotImplementedError,
                   "Teams": NotImplementedError}

    @property
    def _breadcrumb_title(self):
        '''The breadcrumb title should always match user name'''
        return self.name

    @property
    def accordion(self):
        '''Returns an Accordion_Region object describing the user accordion'''
        return Accordion_Region(self.testsetup, _region_map=self._region_map)


class User_Activity_Page(Activity_Stream_Region):
    '''Activity stream page for a single users'''
    _tab_title = "Users"
    _item_class = User_Edit_Page
