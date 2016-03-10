from selenium.webdriver.common.by import By

from common.ui.pages.base import TowerPage
from common.ui.pages.page import Region

from common.ui.pages.regions.forms import SelectDropDown
from common.ui.pages.regions.panels import ListPanel


class ActivityStreamSearch(Region):
    _root_extension = (By.ID, 'search_value_input')


class ActivityStream(TowerPage):

    _path = '/#/activity_stream'

    _subtitle = (By.CSS_SELECTOR, '[class="List-titleText"]')
    _username = (By.ID, 'search-widget-container')
    _resources = (By.ID, 'search-widget-container2')
    _related = (By.ID, 'search-widget-container3')
    _nav_dropdown = (By.ID, 'stream-dropdown-nav')

    @property
    def subtitle(self):
        return self.find_element(self._subtitle)

    @property
    def username(self):
        return ActivityStreamSearch(self, root_locator=self._username)

    @property
    def resources(self):
        return ActivityStreamSearch(self, root_locator=self._resources)

    @property
    def related_resources(self):
        return ActivityStreamSearch(self, root_locator=self._related)

    @property
    def nav_dropdown(self):
        return SelectDropDown(self, root_locator=self._nav_dropdown)

    @property
    def panel(self):
        return ListPanel(self)

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
