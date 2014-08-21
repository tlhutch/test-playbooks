from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from common.ui.pages import *
from common.ui.pages.forms import input_getter, input_setter

class Login_Page(Base):
    # TODO: This obviously should change. File bug
    _page_title = "Ansible Tower"

    # The following should move to using alert_dialog
    _login_license_warning_button_locator = (By.ID, 'alert2_ok_btn')

    _locators = {
        'username': (By.CSS_SELECTOR, '#login-username'),
        'password': (By.CSS_SELECTOR, '#login-password'),
        'login_btn': (By.CSS_SELECTOR, '#login-button'),
    }

    _save_btn_locator = (By.CSS_SELECTOR, '#organization_save_btn')
    _reset_btn_locator = (By.CSS_SELECTOR, '#organization_reset_btn')

    username = property(input_getter(_locators['username']), input_setter(_locators['username']))
    password = property(input_getter(_locators['password']), input_setter(_locators['password']))

    def click_save(self):
        self.get_visible_element(*self._save_btn_locator).click()
        return Organizations_Page(self.testsetup)

    def click_reset(self):
        self.get_visible_element(*self._reset_btn_locator).click()
        return Organizations_Page(self.testsetup)

    @property
    def is_the_current_page(self):
        '''Override the base implementation to make sure that we are actually on the login screen
        and not the actual dashboard
        '''
        return Base.is_the_current_page and self.is_element_visible(*self._locators['login_btn'])

    @property
    def login_btn(self):
        return self.selenium.find_element(*self._locators['login_btn'])

    @property
    def license_warning_button(self):
        return self.selenium.find_element(*self._login_license_warning_button_locator)

    def click_on_login_button(self):
        self.login_btn.click()

    def press_enter_on_login_button(self):
        self.login_btn.send_keys(Keys.RETURN)

    def click_on_login_and_send_window_size(self):
        self.login_btn.click()
        driver = self.login_btn.parent
        driver.execute_script("""miqResetSizeTimer();""")

    def login(self, user='default'):
        return self.login_with_mouse_click(user)
        # return self.login_with_enter_key(user)

    def login_with_enter_key(self, user='default'):
        return self.__do_login(self.press_enter_on_login_button, user)

    def login_with_mouse_click(self, user='default'):
        return self.__do_login(self.click_on_login_button, user)

    def login_and_send_window_size(self, user='default'):
        return self.__do_login(self.click_on_login_and_send_window_size, user)

    def __do_login(self, login_method, user='default'):
        '''
        login to the application using the specified 'login_method'
        '''
        # Wait for "busy" throbber to go away
        self._wait_for_results_refresh()

        self.__set_login_fields(user)
        # Submit field (click submit, press <enter> etc...)
        login_method()

        # Wait for "busy" throbber to go away
        self._wait_for_results_refresh()

        # FIXME - Acknowledge license warning dialog
        # try:
        #     self.license_warning_button.click()
        # except:
        #     pass

        # Wait for "busy" throbber to go away
        # self._wait_for_results_refresh()

        # FIXME - This should return the correct redirected page
        from dashboard import Dashboard
        return Dashboard(self.testsetup)

    def __set_login_fields(self, user='default'):
        credentials = self.testsetup.credentials[user]
        self.username = credentials['username']
        self.password = credentials['password']
