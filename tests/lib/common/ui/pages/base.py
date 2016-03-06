from contextlib import contextmanager
from dateutil.parser import parse
from dateutil.relativedelta import relativedelta
import urllib

from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By

from login import Login
from page import Page
from page import Region

from common.ui.pages.regions import ActivityStreamLink
from common.ui.pages.regions import DashboardLink
from common.ui.pages.regions import Header
from common.ui.pages.regions import ListPanel
from common.ui.pages.regions import Spinny


class TowerPage(Page):

    _crumbs = (By.CLASS_NAME, 'BreadCrumb-item')
    _tab_pane = (By.CLASS_NAME, 'tab-pane')
    _dash_button = (By.CSS_SELECTOR, 'i[class="BreadCrumb-menuLinkImage fa fa-tachometer"]')

    @property
    def dashboard_button(self):
        return DashboardLink(self, root_locator=self._dash_button)

    @property
    def activity_stream_link(self):
        return ActivityStreamLink(self)

    @property
    def crumbs(self):
        return [e.text.lower() for e in self.find_elements(self._crumbs)]

    @property
    def current_crumb(self):
        return self.crumbs[-1]

    @property
    def header(self):
        return Header(self)

    @property
    def spinny(self):
        return Spinny(self)

    @property
    def tab_pane_id(self):
        return self.find_element(self._tab_pane).get_attribute('id')

    def open(self, username=None, password=None, wait=True):
        """Open the driver directly to the page. Subclasses are expected
        to extend this method to reach the modeled page.
        """
        un = username or self.kwargs.get('username')
        pw = password or self.kwargs.get('password')

        loginPage = Login(self.base_url, self.driver)

        loginPage.open()
        loginPage.login(un, pw).wait_until_loaded()

        self.driver.get(self.url)

        if wait:
            self.wait_for_spinny()
            self.wait_until_loaded()

        return self

    def logout(self):
        """Ensure the client is logged out of Ansible Tower
        """
        if self.header.is_displayed():
            self.header.logout_link.click()

    def refresh(self):
        """Refresh the page
        """
        super(TowerPage, self).refresh()
        self.wait_for_spinny()
        return self

    @contextmanager
    def current_user(self, username, password):
        """Momentarily switch to a different user opened to this page
        """
        cookies = self.driver.get_cookies()
        try:
            self.logout()
            self.open(username, password)
            yield

        finally:
            map(self.driver.add_cookie, cookies)
            self.refresh()

    @contextmanager
    def expired_cookie(self):
        cookies = self.driver.get_cookies()

        try:
            self.driver.delete_cookie('token')

            # set token_expires cookie
            token_expires = self.driver.get_cookie('token_expires')
            token_expires['value'] = urllib.unquote(token_expires['value'])

            # delete token_expires cookie
            self.driver.delete_cookie('token_expires')

            # add modified token_expires
            token_expires['value'] = parse(
                token_expires['value'], fuzzy=True) - relativedelta(hours=6)

            token_expires['value'] = token_expires['value'].strftime(
                '"%Y-%m-%dT%H:%M:%S.%fZ"')
            self.driver.add_cookie(token_expires)
            yield

        finally:
            map(self.driver.add_cookie, cookies)
            self.refresh()

    def wait_for_spinny(self):
        try:
            self.spinny.wait_until_displayed()
        except TimeoutException:
            pass

        self.spinny.wait_until_not_displayed()


class TowerCrudPage(TowerPage):

    _refresh_button = (By.CSS_SELECTOR, 'button[aw-tool-tip="Refresh the page"]')

    @property
    def add_button(self):
        return self.list_panel.add_button

    @property
    def list_panel(self):
        return ListPanel(self)

    @property
    def pagination(self):
        return self.list_panel.pagination

    @property
    def search(self):
        return self.list_panel.search

    @property
    def refresh_button(self):
        return Region(self, root_locator=self._refresh_button)

    def open(self, username=None, password=None):
        super(TowerCrudPage, self).open(username, password, wait=False)
        self.wait_for_spinny()
        if self.driver.name == 'internet explorer':
            alert_ok = Region(self, root_locator=(By.ID, 'alert_ok_btn'))
            if alert_ok.is_displayed():
                alert_ok.click()
        self.wait_until_loaded()
        return self

    def __init__(self, base_url, driver, index='', **kwargs):
        super(TowerCrudPage, self).__init__(
            base_url, driver, index=index, **kwargs)
