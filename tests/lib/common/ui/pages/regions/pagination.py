from selenium.webdriver.common.by import By

from common.ui.pages.page import Region
from common.ui.pages.regions.clickable import Clickable


class PaginationLink(Clickable):
    _spinny = True
    _root_locator = (By.CSS_SELECTOR, '#pagination-links')


class PaginationFirstLink(PaginationLink):
    _root_extension = (By.CSS_SELECTOR, '#first-page-set')


class PaginationPreviousLink(PaginationLink):
    _root_extension = (By.CSS_SELECTOR, '#previous-page')


class PaginationNextLink(PaginationLink):
    _root_extension = (By.CSS_SELECTOR, '#next-page')


class PaginationLastLink(PaginationLink):
    _root_extension = (By.CSS_SELECTOR, '#last-page-set')


class PaginationActiveLink(PaginationLink):
    _root_extension = (By.CSS_SELECTOR, 'li.active > a')


class PaginationNumberedLinks(PaginationLink):
    _item_locator = (By.CSS_SELECTOR, 'li.ng-scope > a')

    def __len__(self):
        return len(self.items())

    def options(self):
        return [element.text for element in self.items()]

    def get(self, option):
        element = self.lookup_element(self._item_locator, text=option)
        return Clickable(self.page, root=element, spinny=True)

    def click(self, option):
        self.get(option).click()

    def items(self):
        return self.find_elements(self._item_locator)


class PaginationLabel(Region):
    _root_locator = (By.CSS_SELECTOR, '.List-paginationPager--pageof')

    @property
    def value(self):
        return self._normalize_text(self.root.text)


class PaginationCurrentPageLabel(PaginationLabel):
    _root_extension = (By.CSS_SELECTOR, '#current-page')


class PaginationTotalPagesLabel(PaginationLabel):
    _root_extension = (By.CSS_SELECTOR, '#total-pages')


class Pagination(Region):
    _root_locator = None
    _total_items = (By.CSS_SELECTOR, '#total-items')

    @property
    def active(self):
        return PaginationActiveLink(self.page)

    @property
    def first(self):
        return PaginationFirstLink(self.page)

    @property
    def previous(self):
        return PaginationPreviousLink(self.page)

    @property
    def next(self):
        return PaginationNextLink(self.page)

    @property
    def last(self):
        return PaginationLastLink(self.page)

    @property
    def numbered_links(self):
        return PaginationNumberedLinks(self.page)

    @property
    def current_page_label(self):
        return PaginationCurrentPageLabel(self.page)

    @property
    def total_pages_label(self):
        return PaginationTotalPagesLabel(self.page)

    @property
    def total_items_label(self):
        return self.find_element(self._total_items)

    @property
    def total_items(self):
        # 'ITEMS X-Y OF Z' -> Z
        return int(self.total_items_label.text.split()[-1])

    @property
    def item_range(self):
        # 'ITEMS X-Y OF Z' -> (X, Y)
        text = self.total_items_label.text
        return map(int, text.split()[1].split(u'\u2013'))

    @property
    def current_page(self):
        return int(self.current_page_label.value)

    @property
    def total_pages(self):
        return int(self.total_pages_label.value)

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
