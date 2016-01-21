import logging
import re
import urlparse

from requests.structures import CaseInsensitiveDict
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.support.ui import WebDriverWait

log = logging.getLogger(__name__)

_meta_registry = CaseInsensitiveDict()


class MetaSelector(type):

    def __new__(meta, name, bases, class_dict):
        cls = type.__new__(meta, name, bases, class_dict)

        _meta_registry[cls.__name__] = cls

        if hasattr(cls, '_path') and getattr(cls, '_path') is not None:
            _meta_registry[getattr(cls, '_path')] = cls

        return cls


class Selector(object):

    __metaclass__ = MetaSelector

    _timeout = 25

    def __init__(self, base_url, driver, **kwargs):
        self.driver = driver
        self.kwargs = kwargs

        self.wait = WebDriverWait(self.driver, self.timeout)

        if isinstance(base_url, str):
            base_url = urlparse.urlparse(base_url, allow_fragments=False)
        self._base_url = base_url

    @property
    def base_url(self):
        return self._base_url.geturl()

    @property
    def timeout(self):
        return self.kwargs.get('timeout', self._timeout)

    @property
    def root(self):
        return self.driver

    def find_element(self, locator, root_locator=None):
        if root_locator is not None:
            root = self.find_element(root_locator)
        else:
            root = self.root

        return root.find_element(*locator)

    def find_elements(self, locator, root_locator=None):
        if root_locator is not None:
            root = self.find_element(root_locator)
        else:
            root = self.root

        return root.find_elements(*locator)

    def filter_elements(self, locator, root_locator=None, **kwargs):

        elements = self.find_elements(locator, root_locator=root_locator)

        for element in elements:
            if self._element_matches_by_filter(element, **kwargs):
                return element

        raise NoSuchElementException

    def find_element_by_text(self, locator, text, root_locator=None):

        text = self._normalize_text(text)

        if root_locator is not None:
            root = self.find_element(root_locator)
        else:
            root = self.root

        for element in root.find_elements(*locator):
            if text == self._normalize_text(element.text):
                return element

        raise NoSuchElementException

    def _element_matches_by_filter(self, element, **kwargs):
        for key, value in kwargs.iteritems():
            if not element.get_attribute(key) == value:
                return False
        return True

    def _normalize_text(self, text):
        return re.sub('[^0-9a-zA-Z_]+', '', text.replace(' ', '_')).lower()

    def is_element_clickable(self, locator):
        try:
            return self.find_element(locator).is_enabled()
        except NoSuchElementException:
            return False

    def is_element_displayed(self, locator):
        try:
            return self.find_element(locator).is_displayed()
        except NoSuchElementException:
            return False

    def is_element_present(self, locator):
        try:
            return self.find_element(locator)
        except NoSuchElementException:
            return False

    def wait_until_element_displayed(self, locator):
        self.wait.until(lambda _: self.is_element_displayed(locator))

    def wait_until_element_clickable(self, locator):
        self.wait.until(lambda _: self.is_element_clickable(locator))

    def wait_until_element_present(self, locator):
        self.wait.until(lambda _: self.is_element_present(locator))

    def wait_until_element_not_displayed(self, locator):
        self.wait.until_not(lambda _: self.is_element_displayed(locator))

    def wait_until_element_not_clickable(self, locator):
        self.wait.until_not(lambda _: self.is_element_clickable(locator))

    def wait_until_element_not_present(self, locator):
        self.wait.until_not(lambda _: self.is_element_present(locator))


class Page(Selector):

    @property
    def _url(self):
        return self._base_url._replace(path=self._path or '')

    @property
    def _current_url(self):
        return urlparse.urlparse(self.current_url, allow_fragments=False)

    @property
    def url(self):
        return self._url.geturl()

    @property
    def current_url(self):
        return self.driver.current_url

    @property
    def source(self):
        """Return the raw html source of the current page
        """
        return self.driver.page_source

    def back(self):
        """Return to previous page
        """
        self.driver.back()

    def get_active_element(self):
        """Return the element that has the current focus
        """
        return self.driver.execute_script('return document.activeElement;')

    def is_loaded(self):
        """Return true or false indicating if page is loaded
        """
        base_present = self.base_url in self.current_url
        path_present = self._url.path in self._current_url.path

        return base_present and path_present

    def _load_page(self, page_key):
        """Initialize an external page object instance using the meta
        registry."""

        loaded_page = _meta_registry[page_key](
            self._base_url, self.driver, **self.kwargs)

        loaded_page.wait_for_page_load()

        return loaded_page

    def open(self):
        if not self.is_loaded():
            self.driver.get(self._url.geturl())

        return self

    def refresh(self):
        """Refresh the current page
        """
        self.driver.refresh()
        self.wait_for_page_load()

        return self

    def wait_for_page_load(self):
        self.wait.until(lambda _: self.is_loaded())

        return self


class Region(Selector):

    _root_locator = None

    def __init__(self, page, root=None, **kwargs):
        super(Region, self).__init__(page.base_url, page.driver, **kwargs)
        self._root_element = root
        self.page = page

    @property
    def root(self):
        if self._root_element is None:
            if self.root_locator is not None:
                return self.page.find_element(self.root_locator)
            return self.driver
        return self._root_element

    @property
    def root_locator(self):
        return self.kwargs.get('root_locator', self._root_locator)

    def is_clickable(self):
        return self.is_displayed() and self.root.is_enabled()

    def is_displayed(self):
        return self.is_present() and self.root.is_displayed()

    def is_present(self):
        return self.root is not self.driver

    def wait_until_displayed(self):
        self.wait.until(lambda _: self.is_displayed())

    def wait_until_clickable(self):
        self.wait.until(lambda _: self.is_clickable())

    def wait_until_present(self):
        self.wait.until(lambda _: self.is_present())

    def wait_until_not_displayed(self):
        self.wait.until_not(lambda _: self.is_displayed())

    def wait_until_not_clickable(self):
        self.wait.until_not(lambda _: self.is_clickable())

    def wait_until_not_present(self):
        self.wait.until_not(lambda _: self.is_present())
