from selenium.webdriver.common.by import By

from qe.ui.page import Region
from qe.ui.models.base import TowerPage
from qe.ui.models.forms import SelectDropdown

from qe.ui.models.regions import (
    ListPagination,
    ListTable,
    TagSearch,
)


__all__ = ['ActivityStream']


class ActivityStream(TowerPage):

    url_template = '/#/activity_stream'

    _list_panel = (By.CSS_SELECTOR, '#stream-container')
    _list_subtitle = (By.CLASS_NAME, 'List-titleText')

    @property
    def list_pagination(self):
        return ListPagination(self)

    @property
    def list_search(self):
        return TagSearch(self)

    @property
    def list_table(self):
        return ActivityTable(self)

    @property
    def list_subtitle(self):
        return self.find_element(*self._list_subtitle)

    @property
    def list_panel(self):
        element = self.find_element(*self._list_panel)
        return Region(self, root=element)

    @property
    def navigation_dropdown(self):
        return ActivityDropdown(self)

    @property
    def id(self):
        return self.kwargs.get('id')

    @property
    def target(self):
        return self.kwargs.get('target')

    def wait_until_loaded(self):
        self.wait.until(lambda _: self.navigation_dropdown.is_displayed())
        return self


class ActivityTable(ListTable):

    _root_locator = (By.CSS_SELECTOR, '#activities_table')

    class Row(Region):

        _action = (By.CLASS_NAME, 'description-column')
        _details = (By.CSS_SELECTOR, "i[class='fa fa-search-plus']")

        @property
        def action(self):
            return self.find_element(*self._action)

        @property
        def details(self):
            return self.find_element(*self._details)

        def open_details(self):
            self.details.click()
            return ActivityEventModal(self.page)


class ActivityDropdown(SelectDropdown):

    _root_locator = [(By.ID, 'stream-dropdown-nav'), (By.XPATH, '..')]

    def is_displayed(self):
        return self.page.is_element_displayed(*self._root_locator)


class ActivityEventModal(Region):

    _root_locator = (By.CLASS_NAME, 'modal-content')
    _close = (By.CSS_SELECTOR, 'button[class="close Modal-exit"]')
    _changes = (By.CLASS_NAME, 'StreamDetail-changes')
    _initiated_by = (By.CSS_SELECTOR, '[class="StreamDetail-inlineRow"][ng-show="user"]')
    _ok = (By.ID, 'action_cancel_btn')
    _operation = (By.CSS_SELECTOR, '[ng-bind-html="operation"]')

    @property
    def close(self):
        return self.find_element(*self._close)

    @property
    def changes(self):
        return self.find_element(*self._changes)

    @property
    def ok(self):
        return self.find_element(*self._ok)

    @property
    def initiated_by(self):
        return self.find_element(*self._initiated_by)

    @property
    def operation(self):
        return self.find_element(*self._operation)
