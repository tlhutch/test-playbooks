from selenium.webdriver.common.by import By

from common.ui.page import Region
from common.ui.models.base import TowerPage

class Dashboard(TowerPage):

    url_template = '#/home'
    _toolbar = (By.CSS_SELECTOR, '.DashboardGraphs-graphToolbar')

    @property
    def toolbar(self):
        return self.find_element(*self._toolbar)

    def wait_until_loaded(self):
        self.wait.until(lambda _: self.is_element_displayed(*self._toolbar))
