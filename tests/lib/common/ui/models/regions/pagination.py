from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By

from common.ui.page import Region


class Pagination(Region):

    _first = (By.CSS_SELECTOR, '#first-page-set')
    _previous = (By.CSS_SELECTOR, '#previous-page')
    _next = (By.CSS_SELECTOR, '#next-page')
    _last = (By.CSS_SELECTOR, '#last-page-set')
    _active = (By.CSS_SELECTOR, 'li.active > a')
    _numbered_links = (By.CSS_SELECTOR, 'li.ng-scope > a')
    _pager = (By.CSS_SELECTOR, '.List-paginationPager--pageof')
    _total_items = (By.CSS_SELECTOR, '#total-items')
    _total_pages = (By.CSS_SELECTOR, '#total-pages')
    _current_page = (By.CSS_SELECTOR, '#current-page')
    _pagination_links = (By.CSS_SELECTOR, '#pagination-links')

    @property
    def active(self):
        links = self.find_element(*self._pagination_links)
        return links.find_element(*self._active)

    @property
    def first(self):
        links = self.find_element(*self._pagination_links)
        return links.find_element(*self._first)

    @property
    def previous(self):
        links = self.find_element(*self._pagination_links)
        return links.find_element(*self._previous)

    @property
    def next(self):
        links = self.find_element(*self._pagination_links)
        return links.find_element(*self._next)

    @property
    def last(self):
        links = self.find_element(*self._pagination_links)
        return links.find_element(*self._last)

    @property
    def current_page(self):
        # 'PAGE X of Y' -> X
        pager = self.find_element(*self._pager)
        element = pager.find_element(*self._current_page)
        if element.text:
            return int(element.text)
        return None

    @property
    def total_pages(self):
        # 'PAGE X of Y' -> Y
        pager = self.find_element(*self._pager)
        element = pager.find_element(*self._total_pages)
        if element.text:
            return int(element.text)
        return None

    @property
    def total_items(self):
        # 'ITEMS X-Y OF Z' -> Z
        element = self.page.find_element(*self._total_items)
        return int(element.text.split()[-1])

    @property
    def item_range(self):
        # 'ITEMS X-Y OF Z' -> (X, Y)
        element = self.page.find_element(*self._total_items)
        return map(int, element.text.split()[1].split(u'\u2013'))

    def _find_numbered_link(self, text):
        search_text = text.lower()
        links = self.find_element(*self._pagination_links)
        for element in links.find_elements(*self._numbered_links):
            if element.text.lower() == search_text:
                return element
        raise NoSuchElementException

    def __call__(self, text):
        if text == '>':
            return self.next
        if text == '<':
            return self.previous
        if text == '<<':
            return self.first
        if text == '>>':
            return self.last
        return self._find_numbered_link(text)

    def scan_right(self):
        while self('>').is_displayed():
            if self.current_page >= self.total_pages:
                break
            self('>').click()
            self.wait_until_loaded()
            yield

    def scan_left(self):
        while self('<').is_displayed():
            if self.current_page <= 1:
                break
            self('<').click()
            self.wait_until_loaded()
            yield

    def reset(self):
        if self.current_page == 1:
            return
        for _ in self._scan_left():
            continue
        assert self.current_page == 1

    def wait_until_loaded(self):
        self.wait.until(lambda _: self.current_page is not None)


class ListPagination(Pagination):
    _root_locator = (By.CLASS_NAME, 'List-pagination')
