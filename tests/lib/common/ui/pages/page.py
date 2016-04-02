import logging
import re
import urlparse

from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import UnexpectedAlertPresentException
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.events import AbstractEventListener
from selenium.webdriver.support.events import EventFiringWebDriver
from selenium.webdriver.support.expected_conditions import title_contains
from selenium.webdriver.support.ui import WebDriverWait


log = logging.getLogger(__name__)

_meta_registry = {}


class MetaSelector(type):

    def __new__(meta, name, bases, class_dict):
        cls = type.__new__(meta, name, bases, class_dict)

        if getattr(cls, '_path', None):
            _meta_registry[cls.__name__] = cls

        return cls


class Selector(object):

    _timeout = 20

    def __init__(self, base_url, driver, **kwargs):

        if not isinstance(driver, EventFiringWebDriver):
            driver = EventFiringWebDriver(driver, SelectorEventListener())

        self.driver = driver
        self.kwargs = kwargs

        self.wait = WebDriverWait(self.driver, self.timeout)
        self._base_url = urlparse.urlparse(base_url, allow_fragments=False)

    def _get_page(self, name):
        """Return an external page object using the meta registry.
        """
        return _meta_registry[name]

    @property
    def base_url(self):
        return self._base_url.geturl().rstrip('/')

    @property
    def timeout(self):
        return self.kwargs.get('timeout', self._timeout)

    @property
    def root(self):
        return self.driver

    def _normalize_text(self, text):
        return re.sub('[^0-9a-zA-Z_]+', '', text.replace(' ', '_')).lower()

    def _lookup_page(self, url):
        """Search the meta registry for a page with a matching url
        """
        _url = urlparse.urlparse(url, allow_fragments=False)

        if self._base_url.netloc == _url.netloc:
            for new_page in _meta_registry.values():
                p = new_page(self.base_url, self.driver)
                if p.path.rstrip('/') == _url.path.rstrip('/'):
                    return new_page
        raise ValueError('page lookup failed for url: {}'.format(url))

    def find_element(self, locator):
        if By.is_valid(locator[0]):
            return self.root.find_element(*locator)

        assert isinstance(locator, tuple) and locator, (
            'must be a valid locator or non-empty tuple of valid locators')

        assert all([By.is_valid(loc[0]) for loc in locator]), (
            'must be a valid locator or non-empty tuple of valid locators')

        element = self.root

        for loc in locator:
            element = element.find_element(*loc)

        return element

    def find_elements(self, locator):
        return self.root.find_elements(*locator)

    def is_element_clickable(self, locator):
        try:
            return self.find_element(locator).is_enabled()
        except (NoSuchElementException, WebDriverException):
            return False

    def is_element_displayed(self, locator):
        try:
            return self.find_element(locator).is_displayed()
        except (NoSuchElementException, WebDriverException):
            return False

    def is_element_present(self, locator):
        try:
            return self.find_element(locator)
        except (NoSuchElementException, WebDriverException):
            return False

    def lookup_element(self, locator, text=None, **kwargs):
        if text is not None:
            text = self._normalize_text(text)

        for e in self.find_elements(locator):
            if all([e.get_attribute(k) == v for k, v in kwargs.iteritems()]):
                if text is None or text == self._normalize_text(e.text):
                    return e
        raise NoSuchElementException

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

    __metaclass__ = MetaSelector

    _path = None

    @property
    def _current_url(self):
        return urlparse.urlparse(self.current_url, allow_fragments=False)

    @property
    def _url(self):
        return self._base_url._replace(path=self.path)

    @property
    def path(self):
        return self._path.format(**self.kwargs)

    @property
    def url(self):
        return self._url.geturl().rstrip('/')

    @property
    def current_url(self):
        return self.driver.current_url.rstrip('/')

    @property
    def source(self):
        """Return the raw html source of the current page
        """
        return self.driver.page_source

    def back(self):
        """Return to previous page
        """
        self.driver.back()

    def get(self, url):
        if self.driver.name == 'internet explorer':
            self.wait.until(lambda _: self._get_success(url))
        else:
            self.driver.get(url)

    def _get_success(self, url):
        # This is here because IE 11 WebDriver sometimes fails with a java
        # threadpool exception when using the url get method.
        try:
            self.driver.get(url)
            return True
        except WebDriverException:
            return False

    def open(self):
        if not self.is_loaded():
            self.get(self.url)
        return self

    def get_active_element(self):
        """Return the element that has the current focus
        """
        return self.driver.execute_script('return document.activeElement;')

    def is_loaded(self):
        """Return true or false indicating if this page is currently loaded
        """
        try:
            _current_url = self._current_url
        except (AttributeError, WebDriverException):
            return False

        netloc_match = self._url.netloc == _current_url.netloc
        path_match = self._url.path.rstrip('/') in _current_url.path.rstrip('/')

        return netloc_match and path_match

    def refresh(self):
        """Refresh the current page
        """
        self.driver.refresh()
        self.wait_until_loaded()
        return self

    def wait_until_loaded(self):
        self.wait.until(lambda _: self.is_loaded())
        return self


class Region(Selector):

    _root_locator = None
    _root_extension = None

    def __init__(self, page, **kwargs):
        super(Region, self).__init__(page.base_url, page.driver, **kwargs)
        self.page = page

    @property
    def root(self):
        base_root = self.kwargs.get('root') or self._locate_base_root()

        if base_root is not self.driver:
            if self.root_extension is not None:
                try:
                    return base_root.find_element(*self.root_extension)
                except (NoSuchElementException, WebDriverException):
                    return self.driver
        return base_root

    def _locate_base_root(self):
        if self.root_locator is not None:
            try:
                return self.page.find_element(self.root_locator)
            except (NoSuchElementException, WebDriverException):
                return self.driver
        return self.driver

    @property
    def root_locator(self):
        return self.kwargs.get('root_locator', self._root_locator)

    @property
    def root_extension(self):
        return self.kwargs.get('root_extension', self._root_extension)

    @property
    def size(self):
        self.wait_until_present()
        return self.root.size

    @property
    def location(self):
        self.wait_until_present()
        return self.root.location

    @property
    def text(self):
        self.wait_until_present()
        return self.root.text

    @property
    def value(self):
        self.wait_until_present()
        return self.root.get_attribute('value') or self.text

    @property
    def v1(self):
        """Top-left vertex (x, y) coordinate tuple

        Coordinate units are in pixels and are relative to the top-left
        corner of the page

        v1 *--------*
           | Region |
           *--------* v2
        """
        point = self.location

        return (point['x'], point['y'])

    @property
    def v2(self):
        """Bottom-right vertex (x, y) coordinate tuple

        Coordinate units are in pixels and are relative to the top-left
        corner of the page

        v1 *--------*
           | Region |
           *--------* v2
        """
        point = self.location
        size = self.size

        return (point['x'] + size['width'], point['y'] + size['height'])

    def overlaps_with(self, other_region):
        """Determine if this region overlaps the bounding box of another
        """
        (x1, y1) = self.v1
        (x2, y2) = self.v2

        (x1_other, y1_other) = other_region.v1
        (x2_other, y2_other) = other_region.v2

        return x1 < x2_other and x2 > x1_other and y1 < y2_other and y2 > y1_other

    def surrounds(self, other_region):
        """Determine if this region fully surrounds the bounding box of another
        """
        (x1, y1) = self.v1
        (x2, y2) = self.v2

        (x1_other, y1_other) = other_region.v1
        (x2_other, y2_other) = other_region.v2

        return x1 < x1_other and y1 < y1_other and x2 > x2_other and y2 > y2_other

    def is_clickable(self):
        try:
            return self.is_displayed() and self.root.is_enabled()
        except (AttributeError, WebDriverException):
            # We end up here if the root element becomes stale or unavailable
            # while checking if its enabled
            return False

    def is_displayed(self):
        try:
            return self.is_present() and self.root.is_displayed()
        except (AttributeError, WebDriverException):
            # We end up here if the root element becomes stale or unavailable
            # while checking if its displayed
            return False

    def is_present(self):
        return self.root is not self.driver

    def click(self):
        self.wait_until_clickable()
        self.root.click()

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


class RegionMap(Region):

    # Region subclasses are mapped to keys that are usable from within
    # a region spec
    _region_registry = {}

    # The region_spec maps a property attribute name to a dictionary
    # that is used to lookup a region object in the registry and
    # initialize it with a set of keyword arguments.
    _region_spec = {}

    def __getattr__(self, name):
        try:
            spec = self._region_spec[name]
        except KeyError:
            raise AttributeError
        else:
            return self._load_region(spec)

    def _load_region(self, spec):
        """Lookup and initialize a region from the region registry using the
        provided spec dictionary
        """
        kwargs = spec.copy()
        region_type = kwargs.pop('region_type', 'default')

        if 'root_extension' in kwargs and 'root_locator' not in kwargs:
            kwargs['root'] = self.root

        if region_type == 'default':
            return Region(self.page, **kwargs)
        else:
            return self._region_registry[region_type](self.page, **kwargs)

    def get_regions(self, **kwargs):
        """Generate (name, region) tuples for of regions defined in the
        region spec. Results can be filtered by spec dictionary values
        using keyword arguments.
        """
        for name, spec in self._region_spec.iteritems():
            if all(spec.get(k) == v for k, v in kwargs.iteritems()):
                yield (name, self._load_region(spec))


class SelectorEventListener(AbstractEventListener):

    def on_exception(self, exception, driver):
        if isinstance(exception, UnexpectedAlertPresentException):
            driver.switch_to_alert().accept()

    def after_navigate_to(self, url, driver):
        if driver.name == 'internet explorer':
            if self._title_contains(driver, 'Certificate Error'):
                driver.find_element_by_id('overridelink').click()

    def _title_contains(self, driver, text):
        try:
            return title_contains(text)(driver)
        except WebDriverException:
            return False
