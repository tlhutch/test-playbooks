from contextlib import contextmanager

from selenium.webdriver.common.by import By

from common.ui.page import Page
from common.ui.models.login import Login
from common.ui.models.regions import (
    Dialog,
    Header,
    MobileHeader,
)

class TowerPage(Page):

    _breadcrumbs = (By.CLASS_NAME, 'BreadCrumb-item')
    _refresh = (By.CSS_SELECTOR, 'button[aw-tool-tip="Refresh the page"]')

    @property
    def breadcrumbs(self):
        elements = self.find_elements(*self._breadcrumbs)
        return [e.text.lower() for e in elements]

    @property
    def dialog(self):
        return Dialog(self)

    @property
    def header(self):
        mobileHeader = MobileHeader(self) 
        if mobileHeader.is_displayed():
            return mobileHeader.expand()
        return Header(self)

    @contextmanager
    def current_user(self, username, password='fo0m4nchU'):
        """Momentarily switch to a different user opened to this page
        """
        url = self.driver.current_url
        cookies = self.driver.get_cookies()
        try:
            loginPage = Login(self.driver, self.base_url)
            loginPage.logout()
            loginPage.login(username, password)
            self.driver.get(url)
            yield
        finally:
            map(self.driver.add_cookie, cookies)
            self.driver.refresh()

    @property
    def refresh(self):
        return self.find_element(*self._refresh)

    def is_refresh_button_displayed(self):
        return self.is_element_displayed(*self._refresh)

