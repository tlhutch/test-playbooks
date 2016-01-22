from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait

from common.ui.pages.page import Region


class Spinny(Region):

    _root_locator = (By.CSS_SELECTOR, "div.spinny")

    # TODO: Pull these values from a config file once we're using pytest-vars
    # and pytest-selenium
    _timeout_displayed = 10
    _timeout_not_displayed = 60

    def __init__(self, page, root=None, **kwargs):
        super(Spinny, self).__init__(page, root=root, **kwargs)

        self._wait_displayed = WebDriverWait(
            self.driver, self._timeout_displayed)

        self._wait_not_displayed = WebDriverWait(
            self.driver, self._timeout_not_displayed)

    def wait_until_displayed(self):
        self._wait_displayed.until(lambda _: self.is_displayed())

    def wait_until_not_displayed(self):
        self._wait_not_displayed.until_not(lambda _: self.is_displayed())
