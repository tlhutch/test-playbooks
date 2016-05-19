from selenium.webdriver.common.by import By

from common.ui.pages.page import Region
from pagination import Pagination
from search import Search
from clickable import Clickable


class ListPanel(Region):

    _root_locator = ((By.CLASS_NAME, 'List-header'), (By.XPATH, '..'))

    _add = (By.CSS_SELECTOR, '.List-buttonSubmit')
    _badge = (By.CSS_SELECTOR, '.badge')
    _title = (By.CSS_SELECTOR, '.List-titleText')
    _pagination = (By.CLASS_NAME, 'List-pagination')

    @property
    def add(self):
        return Clickable(
            self.page,
            root=self.root,
            root_extension=self._add)

    @property
    def badge(self):
        return Region(
            self.page,
            root=self.root,
            root_extension=self._add)

    @property
    def pagination(self):
        return Pagination(
            self.page,
            root_locator=self._pagination)

    @property
    def title(self):
        return Region(
            self.page,
            root=self.root,
            root_extension=self._title)

    @property
    def search(self):
        return Search(self.page, root=self.root)

    @property
    def badge_number(self):
        self.wait.until(lambda _: self.badge.text != '')
        return int(self.badge.text)


class ActivityStreamListPanel(ListPanel):
    _root_locator = (
        (By.CLASS_NAME, 'List-header'),
        (By.XPATH, '..'),
        (By.XPATH, '..'))
