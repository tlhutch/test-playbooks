from contextlib import contextmanager

from login import Login
from page import Page

from common.ui.pages.regions.header import Header
from common.ui.pages.regions.spinny import Spinny


class TowerPage(Page):

    @property
    def header(self):
        return Header(self)

    @property
    def spinny(self):
        return Spinny(self)

    def open(self, username=None, password=None):
        """Open the driver directly to this page
        """
        un = username or self.kwargs.get('username')
        pw = password or self.kwargs.get('password')

        loginPage = Login(self.base_url, self.driver, **self.kwargs)
        loginPage.open()
        loginPage.login(un, pw).wait_for_page_load()

        return self

    def logout(self):
        """Ensure the test client is logged out of Ansible Tower
        """
        if self.header.is_displayed():
            self.header.logout_link.click()

    def refresh(self):
        """Refresh the page
        """
        super(TowerPage, self).refresh()

        self.spinny.wait_until_displayed()
        self.spinny.wait_until_not_displayed()

        return self

    @contextmanager
    def current_user(self, username, password):
        """Momentarily switch to a different user and re-open page
        """
        cookies = self.driver.get_cookies()
        try:
            self.logout()
            self.open(username, password)
            yield

        finally:
            map(self.driver.add_cookie, cookies)
            self.refresh()
