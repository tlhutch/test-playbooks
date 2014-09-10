from selenium.webdriver.common.by import By
from common.ui.pages import PageRegion
from common.ui.pages.regions.lists import List_Region
from common.ui.pages.regions.buttons import Base_Button


class PaginationLinks_Region(List_Region):
    '''Represents the pagination links at the bottom of a table'''
    _root_locator = (By.CSS_SELECTOR, '#pagination-links')
    _item_locator = (By.CSS_SELECTOR, 'li.ng-scope > a')
    _item_class = None
    _locators = {
        'current': (By.CSS_SELECTOR, 'li.active > a'),
        'first': (By.CSS_SELECTOR, '#first-page-set'),
        'previous': (By.CSS_SELECTOR, '#previous-page'),
        'next': (By.CSS_SELECTOR, '#next-page'),
        'last': (By.CSS_SELECTOR, '#last-page-set'),
    }
    page_size = 20

    @property
    def first_page(self):
        return Base_Button(self.testsetup, _root_element=self.find_element(*self._locators['first']),
                           _on_click=self.wait_for_spinny, _item_class=self._item_class)

    @property
    def prev_page(self):
        return Base_Button(self.testsetup, _root_element=self.find_element(*self._locators['previous']),
                           _on_click=self.wait_for_spinny, _item_class=self._item_class)

    @property
    def next_page(self):
        return Base_Button(self.testsetup, _root_element=self.find_element(*self._locators['next']),
                           _on_click=self.wait_for_spinny, _item_class=self._item_class)

    @property
    def last_page(self):
        return Base_Button(self.testsetup, _root_element=self.find_element(*self._locators['last']),
                           _on_click=self.wait_for_spinny, _item_class=self._item_class)

    @property
    def active_page(self):
        '''
        Returns the current page as an integer.
        '''
        value = self.find_element(*self._locators['current']).text
        assert value.isdigit(), "expecting digit, but found %s" % type(value)
        return int(value)


class PaginationLabels_Region(PageRegion):
    '''Represents the pagination links at the bottom of a table'''
    _root_locator = (By.CSS_SELECTOR, '#pagination-labels')
    _locators = {
        'current-page': (By.CSS_SELECTOR, '#current-page'),
        'total-pages': (By.CSS_SELECTOR, '#total-pages'),
        'total-items': (By.CSS_SELECTOR, '#total-items'),
    }

    @property
    def current_page(self):
        value = self.find_element(*self._locators['current-page']).text
        assert value.isdigit(), "expecting digit, but found %s" % type(value)
        return int(value)

    @property
    def total_pages(self):
        value = self.find_element(*self._locators['total-pages']).text
        assert value.isdigit(), "expecting digit, but found %s" % type(value)
        return int(value)

    @property
    def total_items(self):
        value = self.find_element(*self._locators['total-items']).text
        assert value.isdigit(), "expecting digit, but found %s" % type(value)
        return int(value)


class Pagination_Region(PaginationLinks_Region, PaginationLabels_Region):
    '''Represents the pagination links at the bottom of a table'''
    _root_locator = (By.CSS_SELECTOR, 'div.page-row')  # Call should provide element/locator
    _locators = {}

    def __init__(self, testsetup, **kwargs):
        super(Pagination_Region, self).__init__(testsetup, **kwargs)
        self._locators.update(PaginationLinks_Region._locators)
        self._locators.update(PaginationLabels_Region._locators)

    @property
    def links(self):
        return PaginationLinks_Region(self.testsetup, _root_element=self.find_element(*PaginationLinks_Region._root_locator))

    @property
    def labels(self):
        return PaginationLabels_Region(self.testsetup, _root_element=self.find_element(*PaginationLabels_Region._root_locator))
