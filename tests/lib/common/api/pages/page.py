import time
from unittestzero import Assert

class Page(object):
    """Base class for all API Pages"""

    def __init__(self, testsetup):
        """Constructor"""
        self.testsetup = testsetup

    def open(self):
        """Open the specified url_fragment, which is relative to the base_url, in the current window."""
        return self.get()
        #self.is_the_current_page

    @property
    def base_url(self):
        return self.testsetup.base_url

    @property
    def api(self):
        return self.testsetup.api

    @property
    def get(self):
        return self.api.get

    @property
    def put(self):
        return self.api.put

    @property
    def patch(self):
        return self.api.patch

    @property
    def post(self):
        return self.api.post

    @property
    def head(self):
        return self.api.head

    @property
    def options(self):
        return self.api.options

    @property
    def delete(self):
        return self.api.delete

    @property
    def page_title(self):
        """
            Return the page title from Selenium.
            This is different from _page_title,
            which is defined for a specific page object and is the expected title of the page.
        """
        WebDriverWait(self.selenium, self.timeout).until(lambda s: self.selenium.title)
        return self.selenium.title

    @property
    def is_the_current_page(self):
        """Return true if the actual page title matches the expected title stored in _page_title."""
        if self._page_title:
            Assert.equal(self.page_title, self._page_title,
                         "Expected page title: %s. Actual page title: %s" % (self._page_title, self.page_title))
        return True

    def is_element_present(self, *locator):
        """
        Return true if the element at the specified locator is present in the DOM.
        Note: It returns false immediately if the element is not found.
        """
        self.selenium.implicitly_wait(0)
        try:
            self._selenium_root.find_element(*locator)
            return True
        except NoSuchElementException:
            return False
        finally:
            # set the implicit wait back
            self.selenium.implicitly_wait(self.testsetup.default_implicit_wait)

    def is_element_visible(self, *locator):
        """
        Return true if the element at the specified locator is visible in the browser.
        Note: It uses an implicit wait if it cannot find the element immediately.
        """
        try:
            return self._selenium_root.find_element(*locator).is_displayed()
        except (NoSuchElementException, ElementNotVisibleException):
            return False

    def is_element_not_visible(self, *locator):
        """
        Return true if the element at the specified locator is not visible in the browser.
        Note: It returns true immediately if the element is not found.
        """
        self.selenium.implicitly_wait(0)
        try:
            return not self._selenium_root.find_element(*locator).is_displayed()
        except (NoSuchElementException, ElementNotVisibleException):
            return True
        finally:
            # set the implicit wait back
            self.selenium.implicitly_wait(self.testsetup.default_implicit_wait)

    def wait_for_element_present(self, *locator):
        """Wait for the element at the specified locator to be present in the DOM."""
        count = 0
        while not self.is_element_present(*locator):
            time.sleep(1)
            count += 1
            if count == self.timeout:
                raise Exception(*locator + ' has not loaded')

    def wait_for_element_visible(self, *locator):
        """Wait for the element at the specified locator to be visible in the browser."""
        count = 0
        while not self.is_element_visible(*locator):
            time.sleep(1)
            count += 1
            if count == self.timeout:
                raise Exception(*locator + " is not visible")

    def wait_for_element_not_present(self, *locator):
        """Wait for the element at the specified locator to be not present in the DOM."""
        self.selenium.implicitly_wait(0)
        try:
            WebDriverWait(self.selenium, self.timeout).until(lambda s: len(self.find_elements(*locator)) < 1)
            return True
        except TimeoutException:
            Assert.fail(TimeoutException)
        finally:
            self.selenium.implicitly_wait(self.testsetup.default_implicit_wait)

    def get_url_current_page(self):
        """Return the url for the current page."""
        return(self.selenium.current_url)

    def find_element(self, *locator):
        """Return the element at the specified locator."""
        return self._selenium_root.find_element(*locator)

    def find_elements(self, *locator):
        """Return a list of elements at the specified locator."""
        return self._selenium_root.find_elements(*locator)

    def link_destination(self, locator):
        """Return the href attribute of the element at the specified locator."""
        link = self.find_element(*locator)
        return link.get_attribute('href')

    def image_source(self, locator):
        """Return the src attribute of the element at the specified locator."""
        link = self.find_element(*locator)
        return link.get_attribute('src')


class PageRegion(Page):
    """Base class for a page region (generally an element in a list of elements)."""

    def __init__(self, testsetup, element):
        self._root_element = element
        Page.__init__(self, testsetup)
