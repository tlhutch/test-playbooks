from selenium.common.exceptions import UnexpectedAlertPresentException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait

from common.ui.pages.page import Region


class Spinny(Region):

    _root_locator = (By.CSS_SELECTOR, "div.spinny")

    def __init__(self, page, **kwargs):
        super(Spinny, self).__init__(page, **kwargs)

        self._wait_one = WebDriverWait(self.driver, 10)
        self._wait_two = WebDriverWait(self.driver, 60)

    def is_clickable(self):
        try:
            return super(Spinny, self).is_clickable()
        except UnexpectedAlertPresentException:
            # We end up here if an unhandled alert shows up on the page while
            # checking if the root element is displayed or enabled
            self.handle_alert()
            return False

    def is_displayed(self):
        try:
            return super(Spinny, self).is_displayed()
        except UnexpectedAlertPresentException:
            # We end up here if an unhandled alert shows up on the page while
            # checking if the root element is displayed
            self.handle_alert()
            return False

    def handle_alert(self):
        self.driver.switch_to_alert().accept()

    def wait_until_displayed(self):
        self._wait_one.until(lambda _: self.is_displayed())

    def wait_until_not_displayed(self):
        self._wait_two.until_not(lambda _: self.is_displayed())
