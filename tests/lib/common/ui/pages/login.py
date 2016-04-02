from selenium.webdriver.common.by import By

from common.ui.pages.page import Page
from common.ui.pages.page import Region

from common.ui.pages.regions import Link
from common.ui.pages.regions import Header
from common.ui.pages.regions import Spinny


class Login(Page):

    _path = '/#/login'

    _login_username = (By.ID, 'login-username')
    _login_password = (By.ID, 'login-password')
    _login_button = (By.ID, 'login-button')
    _alert_errors = (By.CLASS_NAME, 'LoginModal-alert--error')
    _field_errors = (By.CLASS_NAME, 'error')
    _backdrop = (By.CLASS_NAME, 'LoginModal-backDrop')

    @property
    def alert_errors(self):
        return self.find_elements(self._alert_errors)

    @property
    def field_errors(self):
        return self.find_elements(self._field_errors)

    @property
    def displayed_alert_errors(self):
        return [elem for elem in self.alert_errors if elem.is_displayed()]

    @property
    def displayed_field_errors(self):
        return [elem for elem in self.field_errors if elem.is_displayed()]

    @property
    def header(self):
        return Header(self)

    @property
    def username(self):
        return Region(self, root_locator=self._login_username)

    @property
    def password(self):
        return Region(self, root_locator=self._login_password)

    @property
    def login_button(self):
        return Link(self, root_locator=self._login_button, load_page='Dashboard', spinny=True)

    def is_logged_in(self):
        return not self.is_element_present(self._backdrop)

    def wait_until_loaded(self):
        super(Login, self).wait_until_loaded()
        if not self.is_element_displayed(self._backdrop):
            self.driver.refresh()
            self.wait.until(lambda _: self.is_element_displayed(self._backdrop))

    def login(self, username, password):
        self.username.send_keys(username)
        self.password.send_keys(password)

        return self.login_button.click()

    def open(self):
        super(Login, self).open()
        Spinny(self).wait_cycle()
        return self
