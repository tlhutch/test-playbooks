from selenium.webdriver.common.by import By

from common.ui.pages.page import Region
from common.ui.pages.regions.lists import ListRegion
from common.ui.pages.regions.buttons import Button


class PaginationLinks(ListRegion):
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
        return Button(self.page, root=self.find_element(self._locators['first']))

    @property
    def prev_page(self):
        return Button(self.page, root=self.find_element(self._locators['previous']))

    @property
    def next_page(self):
        return Button(self.page, root=self.find_element(self._locators['next']))

    @property
    def last_page(self):
        return Button(self.page, root=self.find_element(self._locators['last']))

    @property
    def active_page(self):
        '''
        Returns the current page as an integer.
        '''
        value = self.find_element(*self._locators['current']).text
        assert value.isdigit(), "expecting digit, but found %s" % type(value)
        return int(value)


class PaginationLabels(Region):
    '''Represents the pagination links at the bottom of a table'''
    _root_locator = (By.CSS_SELECTOR, '#pagination-labels')
    _locators = {
        'current-page': (By.CSS_SELECTOR, '#current-page'),
        'total-pages': (By.CSS_SELECTOR, '#total-pages'),
        'total-items': (By.CSS_SELECTOR, '#total-items'),
    }

    @property
    def current_page(self):
        value = self.find_element(self._locators['current-page']).text
        assert value.isdigit(), "expecting digit, but found %s" % type(value)
        return int(value)

    @property
    def total_pages(self):
        value = self.find_element(self._locators['total-pages']).text
        assert value.isdigit(), "expecting digit, but found %s" % type(value)
        return int(value)

    @property
    def total_items(self):
        value = self.find_element(self._locators['total-items']).text
        assert value.isdigit(), "expecting digit, but found %s" % type(value)
        return int(value)


class Pagination(PaginationLinks, PaginationLabels):
    '''Represents the pagination links at the bottom of a table'''
    _root_locator = (By.CSS_SELECTOR, 'div.page-row')  # Call should provide element/locator
    _locators = {}

    def __init__(self, page, root=None, **kwargs):
        super(Pagination, self).__init__(page, root=root, **kwargs)

        self._locators.update(PaginationLinks._locators)
        self._locators.update(PaginationLabels._locators)

    @property
    def links(self):
        return PaginationLinks(self.page, root=self.find_element(PaginationLinks._root_locator))

    @property
    def labels(self):
        return PaginationLabels(self.page, root=self.find_element(PaginationLabels._root_locator))

