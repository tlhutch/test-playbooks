from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from common.ui.pages import Base, BaseRegion
from common.ui.pages.forms import input_getter, input_setter, Form_Page
from common.ui.pages.regions.stream_container import Activity_Stream_Region
from common.ui.pages.regions.accordion import Accordion_Region
from common.ui.pages.regions.buttons import Activity_Stream_Button, Base_Button, Add_Button, Help_Button
from common.ui.pages.regions.lists import Table_Region


class Organizations_Page(Base):
    '''Describes organizations page'''
    _tab_title = "Organizations"

    # Search form
    _search_widget_locator = (By.CSS_SELECTOR, '#search-widget-container')
    _search_select_locator = (By.CSS_SELECTOR, '#search-field-ddown')
    _search_value_locator = (By.CSS_SELECTOR, '#search-value-input')

    # Results table
    _table_locator = (By.CSS_SELECTOR, '#organizations_table')

    @property
    def add_btn(self):
        return Add_Button(self.testsetup, _item_class=Organization_Create_Page)

    @property
    def activity_stream_btn(self):
        return Activity_Stream_Button(self.testsetup, _item_class=Organizations_Activity_Page)

    def open(self, id):
        super(Organizations_Page, self).open('/#/organizations/%d' % id)
        return Organization_Edit_Page(self.testsetup)


class Organizations_Activity_Page(Activity_Stream_Region):
    '''Activity stream page for all organizations'''
    _tab_title = "Organizations"
    _item_class = Organizations_Page


class Organization_Create_Page(Base):
    '''Describes the organization edit page'''

    _tab_title = "Organizations"
    _breadcrumb_title = 'Create Organization'
    _locators = {
        'name': (By.CSS_SELECTOR, '#organization_name'),
        'description': (By.CSS_SELECTOR, '#organization_description')
    }
    _save_btn_locator = (By.CSS_SELECTOR, '#organization_save_btn')
    _reset_btn_locator = (By.CSS_SELECTOR, '#organization_reset_btn')

    name = property(input_getter(_locators['name']), input_setter(_locators['name']))
    description = property(input_getter(_locators['description']), input_setter(_locators['description']))

    @property
    def save_btn(self):
        return Base_Button(self.testsetup, _root_locator=self._save_btn_locator, _item_class=Organizations_Page)

    @property
    def reset_btn(self):
        return Base_Button(self.testsetup, _root_locator=self._reset_btn_locator, _item_class=Organization_Create_Page)


class Organization_Edit_Properties_Region(BaseRegion, Organization_Create_Page):
    '''Describes the organization edit accordion region'''

    @property
    def activity_stream_btn(self):
        return Activity_Stream_Button(self.testsetup, _item_class=Organization_Activity_Page)


class Organization_Users_Page(Base):
    '''Describes the organization users page'''
    _tab_title = "Organizations"
    _breadcrumb_title = 'Add Users'

    @property
    def add_btn(self):
        return Add_Button(self.testsetup, _item_class=NotImplementedError)

    @property
    def help_btn(self):
        return Help_Button(self.testsetup, _item_class=NotImplementedError)


class Organization_Admins_Page(Base):
    '''Describes the organization admin page'''
    _tab_title = "Organizations"
    _breadcrumb_title = 'Add Administrators'

    @property
    def help_btn(self):
        return Help_Button(self.testsetup, _item_class=NotImplementedError)


class Organization_Edit_Users_Region(BaseRegion):
    '''Describes the organization users region'''
    _tab_title = "Organizations"
    _search_widget_locator = (By.CSS_SELECTOR, '#search-widget-container')

    @property
    def _breadcrumb_title(self):
        '''The breadcrumb title should always match organization name'''
        return self.name

    @property
    def add_btn(self):
        return Add_Button(self.testsetup, _item_class=Organization_Users_Page)

    @property
    def users(self):
        return Table_Region(self.testsetup)


class Organization_Edit_Admins_Region(Organization_Edit_Users_Region):
    '''Describes the organization administrators region'''
    _tab_title = "Organizations"
    _breadcrumb_title = 'Add Administrators'


# class Organization_Edit_Page(Base):
class Organization_Edit_Page(Organization_Create_Page):
    _tab_title = "Organizations"
    _region_map = {"Properties": Organization_Edit_Properties_Region,
                   "Users": Organization_Edit_Users_Region,
                   "Administrators": Organization_Edit_Admins_Region}

    @property
    def _breadcrumb_title(self):
        '''The breadcrumb title should always match organization name'''
        return self.name

    @property
    def accordion(self):
        '''Returns an Accordion_Region object describing the organization accordion'''
        return Accordion_Region(self.testsetup, _region_map=self._region_map)


class Organization_Activity_Page(Activity_Stream_Region):
    '''Activity stream page for a single organizations'''
    _tab_title = "Organizations"
    _item_class = Organization_Edit_Page
