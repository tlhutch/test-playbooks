from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

from common.ui.page import Page

class Login(Page):

    url_template = '#/login'

    _alert_errors = (By.CLASS_NAME, 'LoginModal-alert--error')
    _field_errors = (By.CLASS_NAME, 'error')
    _login_username = (By.ID, 'login-username')
    _login_password = (By.ID, 'login-password')
    _login_button = (By.ID, 'login-button')
    _main_menu_logo = (By.CSS_SELECTOR, '#main_menu_logo > img')

    @property
    def username(self):
        return self.find_element(*self._login_username)

    @property
    def password(self):
        return self.find_element(*self._login_password)

    @property
    def login_button(self):
        return self.find_element(*self._login_button)

    @property
    def errors(self):
        alert_errors = self.find_elements(*self._alert_errors)
        field_errors = self.find_elements(*self._field_errors)
        return [e for e in alert_errors + field_errors if e.is_displayed()]

    def is_login_button_displayed(self):
        return self.is_element_displayed(*self._login_button)

    def is_logged_in(self):
        return self.is_element_displayed(*self._main_menu_logo)

    def login(self, username, password):
        self.username.send_keys(username)
        self.password.send_keys(password)
        self.login_button.click()
        self.wait.until(lambda _: self.is_logged_in() or self.errors)
        return self

    def login_with_enter_key(self, username, password):
        self.username.send_keys(username)
        self.password.send_keys(password)
        self.login_button.send_keys(Keys.RETURN)
        self.wait.until(lambda _: self.is_logged_in() or self.errors)
        return self

    def logout(self):
        self.driver.get(self.open_url.replace('login', 'logout'))
        self.wait.until_not(lambda _: self.is_logged_in())
        return self

    def wait_until_loaded(self):
        self.wait.until(lambda _: self.is_login_button_displayed())
        return self
