from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.support.ui import WebDriverWait


class Selector(object):

    def __init__(self, driver, timeout):
        self.driver = driver
        self.timeout = timeout
        self.wait = WebDriverWait(driver, timeout)

    def find_element(self, *locator):
        """Find an element on the page
        """
        if isinstance(locator[0], tuple):
            return self._find_element_chain(*locator)
        return self.driver.find_element(*locator)

    def _find_element_chain(self, *locator_chain):
        """Find an element sequentially with a list of locators
        """
        element = self.find_element(*locator_chain[0])
        if len(locator_chain) == 1:
            return element
        for locator in locator_chain[1:]:
            element = element.find_element(*locator)
        return element

    def find_elements(self, *locator):
        """Find elements on the page
        """
        return self.driver.find_elements(*locator)

    def is_element_displayed(self, *locator):
        """Check if an element is displayed.
        """
        try:
            element = self.find_element(*locator)
            return element.is_displayed()
        except NoSuchElementException:
            return False

    def is_element_present(self, *locator):
        """Checks if an element is present.
        """
        try:
            element = self.find_element(*locator)
            return element
        except NoSuchElementException:
            return False
