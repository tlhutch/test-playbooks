import time
import logging
import urlparse
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import NoSuchElementException, ElementNotVisibleException, TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from unittestzero import Assert


log = logging.getLogger(__name__)


class Page(object):
    '''
    Base class for all Pages
    '''
    _spinny_locator = (By.CSS_SELECTOR, "div.spinny")
    _logo_locator = (By.CSS_SELECTOR, "#ansible-brand-logo")

    def __init__(self, testsetup, **kwargs):
        self.testsetup = testsetup
        self.base_url = testsetup.base_url
        self.selenium = testsetup.selenium
        self.timeout = testsetup.timeout
        self._selenium_root = hasattr(self, '_root_element') and self._root_element or self.selenium
        if '_breadcrumb_title' in kwargs:
            self._breadcrumb_title = kwargs['_breadcrumb_title']

    def wait_for_spinny(self):
        '''Wait for the 'Working...' spinner to disappear'''
        # Wait for spinner to appear
        time.sleep(0.5)
        # WebDriverWait(self.selenium, 1).until(lambda s: s.find_element(*self._spinny_locator).is_displayed())

        # Wait for spinner to disappear
        WebDriverWait(self.selenium, self.timeout).until(lambda s: not s.find_element(*self._spinny_locator).is_displayed())

    def open(self, url_fragment=""):
        '''Open the specified url_fragment, which is relative to the base_url, in the current window.'''
        self.selenium.get(self.base_url + url_fragment)
        self.is_the_current_page

    def back(self):
        '''Simulate clicking the browser 'Back' button'''
        self.selenium.back()

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
        if hasattr(self, '_page_title') and self._page_title:  # IGNORE:E1101
            Assert.equal(self.page_title, self._page_title,  # IGNORE:E1101
                         "Actual page title: %s. Expected page title: %s" %
                         (self.page_title, self._page_title))  # IGNORE:E1101
        return True

    def get_current_page_url(self):
        '''Return the current selenium URL'''
        return self.selenium.current_url

    def get_current_page_path(self):
        '''Return the path from the current selenium URL'''
        url = self.get_current_page_url()
        path = urlparse.urlparse(url, allow_fragments=False).path
        if path.startswith('/#/'):
            path = path[2:]
        return path

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
                raise Exception(locator[1] + ' has not loaded')

    def wait_for_element_visible(self, *locator):
        """Wait for the element at the specified locator to be visible in the browser."""
        count = 0
        while not self.is_element_visible(*locator):
            time.sleep(1)
            count += 1
            if count == self.timeout:
                raise Exception(locator[1] + " is not visible")

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

    def wait_for_element_not_visible(self, *locator):
        """Wait for the element at the specified locator to be not visible in the DOM."""
        self.selenium.implicitly_wait(0)
        try:
            WebDriverWait(self.selenium, self.timeout).until(lambda s: not self.is_element_visible(*locator))
            return True
        except TimeoutException:
            Assert.fail(TimeoutException)
        finally:
            self.selenium.implicitly_wait(self.testsetup.default_implicit_wait)

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

    def find_visible_element(self, *locator):
        '''FIXME'''
        for el in self.find_elements(*locator):
            if el.is_displayed():
                return el
        raise NoSuchElementException('element not found: %s' % str(locator))

    def find_visible_elements(self, *locator):
        '''FIXME'''
        return [el for el in self.find_elements(*locator) if el.is_displayed()]

    def handle_popup(self, cancel=False):
        wait = WebDriverWait(self.selenium, self.timeout)
        # throws timeout exception if not found
        wait.until(EC.alert_is_present())
        popup = self.selenium.switch_to_alert()
        answer = 'cancel' if cancel else 'ok'
        print popup.text + " ...clicking " + answer
        popup.dismiss() if cancel else popup.accept()


class PageRegion(Page):
    """Base class for a page region (generally an element in a list of elements)."""

    def __init__(self, testsetup, **kwargs):
        '''Initialize the region using a provided _root_element, or _root_locator'''

        for k, v in kwargs.items():
            setattr(self, k, v)

        if not hasattr(self, '_root_element') or self._root_element is None:
            '''if _root_element was not provided, lookup using _root_locator'''
            locator = kwargs.get('_root_locator', getattr(self, '_root_locator', None))
            if locator is None:
                raise Exception("No _root_element or _root_locator provided")
            # NOTE: We cannot use 'Page.find_element()' as 'self._selenium_root' is not yet initialized
            # The following works fine, unless there are multiple matching elements
            # self._root_element = testsetup.selenium.find_element(*locator)
            self._root_element = [el for el in testsetup.selenium.find_elements(*locator) if el.is_displayed()][0]

        super(PageRegion, self).__init__(testsetup)

    def is_displayed(self):
        '''Return true if the _root_element is currently visible'''
        return self._root_element.is_displayed()
