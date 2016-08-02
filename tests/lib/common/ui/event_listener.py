from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import UnexpectedAlertPresentException
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.support.events import AbstractEventListener
from selenium.webdriver.support.expected_conditions import title_contains
from selenium.webdriver.support.ui import WebDriverWait


class TowerEventListener(AbstractEventListener):

    def _title_contains(self, driver, text):
        try:
            return title_contains(text)(driver)
        except WebDriverException:
            return False

    def _is_spinny_displayed(self, driver):
        try:
            return driver.find_element_by_css_selector('div.spinny').is_displayed()
        except NoSuchElementException:
            return False

    def _check_for_spinny(self, driver):
        if self._is_spinny_displayed(driver):
            WebDriverWait(driver, 30).until_not(self._is_spinny_displayed)

    def before_navigate_to(self, url, driver):
        self._check_for_spinny(driver)

    def after_navigate_to(self, url, driver):
        if driver.name == 'internet explorer':
            if self._title_contains(driver, 'Certificate Error'):
                driver.find_element_by_id('overridelink').click()
        self._check_for_spinny(driver)

    def before_navigate_back(self, driver):
        self._check_for_spinny(driver)

    def after_navigate_back(self, driver):
        self._check_for_spinny(driver)

    def before_navigate_forward(self, driver):
        self._check_for_spinny(driver)

    def after_navigate_forward(self, driver):
        self._check_for_spinny(driver)

    def before_find(self, by, value, driver):
        self._check_for_spinny(driver)

    def after_find(self, by, value, driver):
        self._check_for_spinny(driver)

    def before_click(self, element, driver):
        self._check_for_spinny(driver)

    def after_click(self, element, driver):
        self._check_for_spinny(driver)

    def before_change_value_of(self, element, driver):
        self._check_for_spinny(driver)

    def after_change_value_of(self, element, driver):
        self._check_for_spinny(driver)

    def before_execute_script(self, script, driver):
        self._check_for_spinny(driver)

    def after_execute_script(self, script, driver):
        self._check_for_spinny(driver)

    def on_exception(self, exception, driver):
        if isinstance(exception, UnexpectedAlertPresentException):
            driver.switch_to_alert().accept()
