from contextlib import contextmanager

from selenium.webdriver.common.by import By

from qe.ui.page import get_page
from qe.ui.page import Page
from qe.ui.models.login import Login

from qe.ui.models.regions import (
    Dialog,
    Header,
    MobileHeader,
)


class TowerPage(Page):

    _activity_stream_link = (By.CSS_SELECTOR, 'i[class="BreadCrumb-menuLinkImage icon-activity-stream"]')
    _breadcrumbs = (By.CLASS_NAME, 'BreadCrumb-item')
    _refresh_button = (By.CSS_SELECTOR, 'button[aw-tool-tip="Refresh the page"]')

    @property
    def activity_stream_link(self):
        return self.find_element(*self._activity_stream_link)

    @property
    def breadcrumbs(self):
        elements = self.find_elements(*self._breadcrumbs)
        return [e.text.lower() for e in elements]

    @property
    def current_breadcrumb(self):
        breadcrumbs = self.breadcrumbs
        import pdb; pdb.set_trace()
        return breadcrumbs[-1] if breadcrumbs else None

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
        Login(self.driver, self.base_url).logout().login(username, password)
        self.driver.get(url)
        yield
        map(self.driver.add_cookie, cookies)
        self.driver.refresh()

    @property
    def refresh_button(self):
        return self.find_element(*self._refresh_button)

    def is_refresh_button_displayed(self):
        return self.is_element_displayed(*self._refresh_button)

    def open_activity_stream(self):
        self.activity_stream_link.click()
        return get_page('ActivityStream')(self.driver).wait_until_loaded()
