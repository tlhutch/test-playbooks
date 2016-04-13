from selenium.webdriver.common.by import By

from common.ui.pages.page import Region
from common.ui.pages.regions.clickable import Clickable


class NumberedLinks(Clickable):

    _root_locator = (By.CSS_SELECTOR, '#pagination-links')
    _item_locator = (By.CSS_SELECTOR, 'li.ng-scope > a')

    def __len__(self):
        return len(self.items())

    @property
    def options(self):
        return [element.text for element in self.items()]

    def get(self, option):
        element = self.lookup_element(self._item_locator, text=option)
        return Clickable(self.page, root=element, spinny=True)

    def items(self):
        return self.find_elements(self._item_locator)


class Pagination(Region):

    _root_locator = None

    _total_items = (By.CSS_SELECTOR, '#total-items')

    _first = (
        (By.CSS_SELECTOR, '#pagination-links'),
        (By.CSS_SELECTOR, '#first-page-set'))

    _previous = (
        (By.CSS_SELECTOR, '#pagination-links'),
        (By.CSS_SELECTOR, '#previous-page'))

    _next = (
        (By.CSS_SELECTOR, '#pagination-links'),
        (By.CSS_SELECTOR, '#next-page'))

    _last = (
        (By.CSS_SELECTOR, '#pagination-links'),
        (By.CSS_SELECTOR, '#last-page-set'))

    _active = (
        (By.CSS_SELECTOR, '#pagination-links'),
        (By.CSS_SELECTOR, 'li.active > a'))

    _total_pages = (
        (By.CSS_SELECTOR, '.List-paginationPager--pageof'),
        (By.CSS_SELECTOR, '#total-pages'))

    _current_page = (
        (By.CSS_SELECTOR, '.List-paginationPager--pageof'),
        (By.CSS_SELECTOR, '#current-page'))

    @property
    def active(self):
        return Clickable(
            self.page,
            root=self.find_element(self._active),
            spinny=True)

    @property
    def first(self):
        return Clickable(
            self.page,
            root=self.find_element(self._first),
            spinny=True)

    @property
    def previous(self):
        return Clickable(
            self.page,
            root=self.find_element(self._previous),
            spinny=True)

    @property
    def next(self):
        return Clickable(
            self.page,
            root=self.find_element(self._next),
            spinny=True)

    @property
    def last(self):
        return Clickable(
            self.page,
            root=self.find_element(self._last),
            spinny=True)

    @property
    def numbered_links(self):
        return NumberedLinks(self.page)

    @property
    def total_items(self):
        label = Region(self.page, root=self.find_element(self._total_items))
        # 'ITEMS X-Y OF Z' -> Z
        return int(label.text.split()[-1])

    @property
    def item_range(self):
        label = Region(self.page, root=self.find_element(self._total_items))
        # 'ITEMS X-Y OF Z' -> (X, Y)
        return map(int, label.text.split()[1].split(u'\u2013'))

    @property
    def current_page(self):
        label = Region(self.page, root=self.find_element(self._current_page))
        return int(label.value)

    @property
    def total_pages(self):
        label = Region(self.page, root=self.find_element(self._total_pages))
        return int(label.value)

    def rewind(self):
        while self.previous.is_displayed():
            if self.current_page <= 1:
                break
            self.previous.click()

    def fast_forward(self):
        while self.next.is_displayed():
            if self.current_page >= self.total_pages:
                break
            self.next.click()
