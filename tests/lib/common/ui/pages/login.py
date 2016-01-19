from selenium.webdriver.common.by import By

from page import Page

from common.ui.pages.regions import (
    DashboardLink,
    Field,
    Header,
)


class LoginButton(DashboardLink):
    _root_locator = (By.ID, 'login-button')


class LoginUsername(Field):
    _root_locator = (By.ID, 'login-username')


class LoginPassword(Field):
    _root_locator = (By.ID, 'login-password')


class Login(Page):

    _path = '/#/login'

    _alert_errors = (By.CLASS_NAME, 'LoginModal-alert--error')

    @property
    def alert_errors(self):
        return self.find_elements(self._alert_errors)

    @property
    def displayed_alert_errors(self):
        return [elem for elem in self.alert_errors if elem.is_displayed()]

    @property
    def header(self):
        return Header(self)

    @property
    def login_button(self):
        return LoginButton(self)

    @property
    def username(self):
        return LoginUsername(self)

    @property
    def password(self):
        return LoginPassword(self)

    def is_logged_in(self):
        return self.header.is_displayed()

    def is_loaded(self):
        return super(Login, self).is_loaded() and not self.is_logged_in()

    def login(self, username, password):
        self.username.clear()
        self.username.send_keys(username)

        self.password.clear()
        self.password.send_keys(password)

        return self.login_button.click()


class Logout(Login):

    _path = '/#/logout'
