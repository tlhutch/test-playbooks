from urlparse import urljoin
import re

from selector import Selector


__all__ = ['get_page', 'lookup_page', 'Page']


_meta_registry = {}


def get_page(name):
    try:
        return _meta_registry[name]
    except KeyError:
        raise ValueError('No page found with name {0}'.format(name))


def lookup_page(url):
    for page_cls in _meta_registry.itervalues():
        if not page_cls.base_url:
            continue
        if not page_cls.url_match_pattern:
            continue
        if page_cls.base_url not in url:
            continue
        if re.search(page_cls.url_match_pattern, url):
            return page_cls
    raise ValueError('No page found matching url: {0}'.format(url))


def register_page(name, page_cls):
    if name in _meta_registry:
        raise ValueError(
            'A page is already registered with name {0}'.format(name))
    _meta_registry[name] = page_cls


class MetaPage(type):

    def __new__(meta, name, bases, class_dict):
        cls = type.__new__(meta, name, bases, class_dict)

        register_page(cls.__name__, cls)

        return cls


class Page(Selector):

    __metaclass__ = MetaPage

    url_template = None
    url_match_pattern = None

    def __init__(self, driver, base_url=None, timeout=30, **kwargs):
        super(Page, self).__init__(driver, timeout)
        self.base_url = base_url
        self.kwargs = kwargs

    @property
    def open_url(self):
        """Get a URL that can be used to open the page
        """
        if self.url_template is not None:
            formatted_url = self.url_template.format(**self.kwargs)
            return urljoin(self.base_url, formatted_url)
        return self.base_url

    def open(self):
        """Open the page to open_url
        """
        if self.open_url:
            self.driver.get(self.open_url)
            self.wait_until_loaded()
            return self
        raise RuntimeError('A base_url or url_template is required')

    def wait_until_loaded(self):
        """Wait for the page to load - override or extend as needed
        """
        return self
