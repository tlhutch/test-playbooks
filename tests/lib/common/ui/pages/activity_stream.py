from selenium.webdriver.common.by import By

from common.ui.pages.base import TowerPage
from common.ui.pages.page import Region

from common.ui.pages.regions import Clickable

from common.ui.pages.forms import SelectDropDown
from common.ui.pages.regions.panels import ActivityStreamListPanel
from common.ui.pages.regions.table import Table
from common.ui.pages.regions.cells import DescriptionCell


class ActivityStreamActionModal(Region):
    _root_locator = (By.CLASS_NAME, 'modal-content')

    _close = (By.CSS_SELECTOR, 'button[class="close Modal-exit"]')
    _changes = (By.CLASS_NAME, 'StreamDetail-changes')
    _ok = (By.ID, 'action_cancel_btn')
    _initiated_by = (By.CSS_SELECTOR, '[class="StreamDetail-inlineRow"][ng-show="user"]')
    _operation = (By.CSS_SELECTOR, '[ng-bind="operation"]')

    @property
    def close(self):
        return Region(self.page, root_locator=self._close)

    @property
    def changes(self):
        return Region(self.page, root_locator=self._changes)

    @property
    def ok(self):
        return Region(self.page, root_locator=self._ok)

    @property
    def initiated_by(self):
        return Region(self.page, root_locator=self._initiated_by)

    @property
    def operation(self):
        return Region(self.page, root_locator=self._operation)


class EventDetailCell(Clickable):
    _root_extension = (By.CSS_SELECTOR, "i[class='fa fa-search-plus']")

    def after_click(self):
        super(EventDetailCell, self).after_click()
        return ActivityStreamActionModal(self.page)


class ActivityTable(Table):

    _root_locator = (By.CSS_SELECTOR, '#activities_table')

    _row_spec = (
        ('action', DescriptionCell),
        ('event_details', EventDetailCell)
    )


class ActivityStreamSearch(Region):
    _root_extension = (By.ID, 'search_value_input')


class ActivityStream(TowerPage):

    _path = '/#/activity_stream'

    _subtitle = (By.CSS_SELECTOR, '[class="List-titleText"]')
    _related = (By.ID, 'search-widget-container3')
    _nav_dropdown = ((By.ID, 'stream-dropdown-nav'), (By.XPATH, '..'))

    @property
    def subtitle(self):
        return self.find_element(self._subtitle)

    @property
    def nav_dropdown(self):
        return SelectDropDown(self, root_locator=self._nav_dropdown)

    @property
    def panel(self):
        return ActivityStreamListPanel(self)

    @property
    def table(self):
        return ActivityTable(self)

    @property
    def target(self):
        return self.kwargs.get('target')

    @property
    def index(self):
        return self.kwargs.get('index')

    def __init__(self, base_url, driver, **kwargs):
        super(ActivityStream, self).__init__(base_url, driver, **kwargs)

        if self.target is not None:
            self._path += '?target={}'.format(self.target)
        if self.index is not None:
            self._path += '&id={}'.format(self.index)
