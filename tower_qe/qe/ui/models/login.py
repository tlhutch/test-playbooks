from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

from qe.ui.page import Page


class Login(Page):

    url_template = '#/login'

    _alert_errors = (By.CLASS_NAME, 'LoginModal-alert--error')
    _field_errors = (By.CLASS_NAME, 'error')
    _login_username = (By.ID, 'login-username')
    _login_password = (By.ID, 'login-password')
    _login_button = (By.ID, 'login-button')
    _main_menu_logo = (By.CSS_SELECTOR, '#main_menu_logo > img')
    _login_modal_image = (By.CLASS_NAME, 'LoginModal-logoImage')
    _login_modal_notice = (By.CLASS_NAME, 'LoginModalNotice-title')

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

    @property
    def modal_image(self):
        return self.find_element(*self._login_modal_image)

    @property
    def modal_notice(self):
        return self.find_element(*self._login_modal_notice)

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
        self.wait_until_loaded()
        return self

    def wait_until_loaded(self):
        self.wait.until(lambda _: self.is_login_button_displayed())
        return self

    def is_modal_notice_displayed(self):
        return self.is_element_displayed(*self._login_modal_notice)


class GithubLogin(Page):

    open_url = 'https://github.com/login/'

    _login_field = (By.CSS_SELECTOR, '#login_field')
    _password_field = (By.CSS_SELECTOR, '#password')
    _login_button = (By.CSS_SELECTOR, '.btn')

    @property
    def username(self):
        return self.find_element(self._login_field)

    @property
    def password(self):
        return self.find_element(self._password_field)

    @property
    def login_button(self):
        return self.find_element(self._login_button)

    def login(self, username, password):
        self.username.clear()
        self.username.send_keys(username)

        self.password.clear()
        self.password.send_keys(password)

        self.wait.until(lambda _: self.login_button.is_enabled())
        self.login_button.click()
