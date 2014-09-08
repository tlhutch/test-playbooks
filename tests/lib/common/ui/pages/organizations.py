from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from common.ui.pages import Base, BaseRegion
from common.ui.pages.forms import input_getter, input_setter
from common.ui.pages.regions.stream_container import Activity_Stream_Region
from common.ui.pages.regions.accordion import Accordion_Region
from common.ui.pages.regions.buttons import Activity_Stream_Button, Base_Button, Add_Button, Help_Button
from common.ui.pages.regions.lists import SortTable_Region, Pagination_Region
from common.ui.pages.regions.dialogs import Prompt_Dialog
from common.ui.pages.regions.search import Search_Region


class Organizations_Page(Base):
    '''Describes organizations page'''
    _tab_title = "Organizations"
    _related = {
        'add': 'Organization_Create_Page',
        'edit': 'Organization_Edit_Page',
        'delete': 'Prompt_Dialog',
        'activity_stream': 'Organizations_Activity_Page',
    }
    _locators = {
        'table': (By.CSS_SELECTOR, '#organizations_table'),
    }

    @property
    def add_btn(self):
        return Add_Button(self.testsetup, _item_class=self.get_related('add'))

    @property
    def activity_stream_btn(self):
        return Activity_Stream_Button(self.testsetup, _item_class=self.get_related('activity_stream'))

    def open(self, id):
        super(Organizations_Page, self).open('/#/organizations/%d' % id)
        return self.get_related('edit')(self.testsetup)

    @property
    def table(self):
        # FIXME - doesn't work yet
        _region_map = {
            'edit-action': Organization_Edit_Page,
            'delete-action': Prompt_Dialog,
        }
        return SortTable_Region(self.testsetup, _root_locator=self._locators['table'], _region_map=_region_map)

    @property
    def pagination(self):
        return Pagination_Region(self.testsetup, _item_class=self.__class__)

    @property
    def search(self):
        return Search_Region(self.testsetup, _item_class=self.__class__)


class Organizations_Activity_Page(Activity_Stream_Region):
    '''Activity stream page for all organizations'''
    _tab_title = "Organizations"
    _related = {
        'close': 'Organizations_Page',
    }


class Organization_Create_Page(Base):
    '''Describes the organization edit page'''

    _tab_title = "Organizations"
    _breadcrumb_title = 'Create Organization'
    _related = {
        'save': 'Organizations_Page',
    }
    _locators = {
        'name': (By.CSS_SELECTOR, '#organization_name'),
        'description': (By.CSS_SELECTOR, '#organization_description'),
        'save_btn': (By.CSS_SELECTOR, '#organization_save_btn'),
        'reset_btn': (By.CSS_SELECTOR, '#organization_reset_btn'),
    }

    name = property(input_getter(_locators['name']), input_setter(_locators['name']))
    description = property(input_getter(_locators['description']), input_setter(_locators['description']))

    @property
    def save_btn(self):
        return Base_Button(self.testsetup, _root_locator=self._locators['save_btn'], _item_class=self.get_related('save'))

    @property
    def reset_btn(self):
        return Base_Button(self.testsetup, _root_locator=self._locators['reset_btn'], _item_class=self.__class__)


class Organization_Edit_Properties_Region(BaseRegion, Organization_Create_Page):
    '''Describes the organization edit accordion region'''
    _related = {
        'activity_stream': 'Organization_Activity_Page',
    }

    @property
    def activity_stream_btn(self):
        return Activity_Stream_Button(self.testsetup, _item_class=self.get_related('activity_stream'))


class Organization_Users_Page(Base):
    '''Describes the organization users page'''
    _tab_title = "Organizations"
    _breadcrumb_title = "Add Users"
    _related = {
        'add': 'FIXME',
        'help': 'FIXME',
    }
    _locators = {
        'table': (By.CSS_SELECTOR, '#users_table'),
    }

    @property
    def add_btn(self):
        return Add_Button(self.testsetup, _item_class=self.get_related('add'))

    @property
    def help_btn(self):
        return Help_Button(self.testsetup, _item_class=self.get_related('help'))

    @property
    def users(self):
        return SortTable_Region(self.testsetup, _root_locator=self._locators['table'])


class Organization_Admins_Page(Organization_Users_Page):
    '''Describes the organization admin page'''
    _tab_title = "Organizations"
    _breadcrumb_title = "Add Administrators"
    _locators = {
        'table': (By.CSS_SELECTOR, '#admins_table')
    }

    @property
    def help_btn(self):
        return Help_Button(self.testsetup, _item_class=self.get_related('help'))

class Organization_Edit_Users_Region(BaseRegion):
    '''Describes the organization users region'''
    _tab_title = "Organizations"
    _related = {
        'add': 'Organization_Users_Page',
    }
    _locators = {
        'table': (By.CSS_SELECTOR, '#users_table'),
        'add': (By.CSS_SELECTOR, '#add_btn'),
    }

    @property
    def _breadcrumb_title(self):
        '''The breadcrumb title should always match organization name'''
        return self.name

    @property
    def add_btn(self):
        return Add_Button(self.testsetup, _item_class=self.get_related('add'), _root_element=self.find_element(*self._locators['add']))

    @property
    def users(self):
        return SortTable_Region(self.testsetup, _root_locator=self._locators['table'])


class Organization_Edit_Admins_Region(Organization_Edit_Users_Region):
    '''Describes the organization administrators region'''
    _tab_title = "Organizations"
    _locators = {
        'table': (By.CSS_SELECTOR, '#admins_table'),
        'add': (By.CSS_SELECTOR, '#add_btn'),
    }

    @property
    def _breadcrumb_title(self):
        '''The breadcrumb title should always match organization name'''
        return self.name

    @property
    def add_btn(self):
        return Add_Button(self.testsetup, _item_class=Organization_Admins_Page, _root_element=self.find_element(*self._locators['add']))


# class Organization_Edit_Page(Base):
class Organization_Edit_Page(Organization_Create_Page):
    _tab_title = "Organizations"
    _region_map = {
        'Properities': Organization_Edit_Properties_Region,
        'Users': Organization_Edit_Users_Region,
        'Administrators': Organization_Edit_Admins_Region,
    }

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
    _related = {
        'close': 'Organization_Edit_Page',
    }
