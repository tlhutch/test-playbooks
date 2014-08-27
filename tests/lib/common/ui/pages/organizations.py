from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from common.ui.pages import *
from common.ui.pages.forms import input_getter, input_setter, Form_Page
from common.ui.pages.regions.stream_container import Activity_Stream_Region, Activity_Stream_Button
from common.ui.pages.regions.accordion import Accordion_Region


class Organizations_Page(Base):
    '''Describes organizations page'''
    _tab_title = "Organizations"
    _add_btn_locator = (By.CSS_SELECTOR, '#add_btn')

    # Search form
    _search_widget_locator = (By.CSS_SELECTOR, '#search-widget-container')
    _search_select_locator = (By.CSS_SELECTOR, '#search-field-ddown')
    _search_value_locator = (By.CSS_SELECTOR, '#search-value-input')

    # Results table
    _table_locator = (By.CSS_SELECTOR, '#organizations_table')

    @property
    def add_button(self):
        return self.find_visible_element(*self._add_btn_locator)

    @property
    def has_add_button(self):
        try:
            return self.add_button.is_displayed()
        except NoSuchElementException:
            return False

    def click_add(self):
        self.add_button.click()
        return Organization_Create_Page(self.testsetup)

    def open(self, id):
        super(Organizations_Page, self).open('/#/organizations/%d' % id)
        return Organization_Edit_Page(self.testsetup)

    @property
    def activity_stream_btn(self):
        return Activity_Stream_Button(self.testsetup, _item_class=Organizations_Activity_Page)


class Organizations_Activity_Page(Activity_Stream_Region):
    '''Activity stream page for all organizations'''
    _tab_title = "Organizations"
    _parent_object = Organizations_Page


class Organization_Activity_Page(Activity_Stream_Region):
    '''Activity stream page for a single organizations'''
    _tab_title = "Organizations"


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

    def click_save(self):
        self.find_visible_element(*self._save_btn_locator).click()
        return Organizations_Page(self.testsetup)

    def click_reset(self):
        self.find_visible_element(*self._reset_btn_locator).click()
        return Organizations_Page(self.testsetup)


class Organization_Edit_Properties_Region(BaseRegion, Organization_Create_Page):
    '''Describes the organization edit region'''

    @property
    def activity_stream_btn(self):
        return Activity_Stream_Button(self.testsetup, _item_class=Organization_Activity_Page)


class Organization_Edit_Users_Region(BaseRegion):
    '''Describes the organization users region'''


# class Organization_Edit_Page(Base):
class Organization_Edit_Page(Organization_Create_Page):
    _tab_title = "Organizations"
    _region_map = {"Properties": Organization_Edit_Properties_Region,
                   "Users": Organization_Edit_Users_Region,
                   "Administrators": Organization_Edit_Users_Region,}

    @property
    def _breadcrumb_title(self):
        '''The breadcrumb title should always match organization name'''
        return self.name

    @property
    def accordion(self):
        '''Returns an Accordion_Region object describing the organization accordion'''
        return Accordion_Region(self.testsetup, _region_map=self._region_map)
