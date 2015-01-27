class Page(object):
    """Base class for all API Pages"""

    def __init__(self, testsetup):
        """Constructor"""
        self.testsetup = testsetup

    def open(self):
        """Open the specified url_fragment, which is relative to the base_url, in the current window."""
        return self.get()
        # self.is_the_current_page

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


class PageRegion(Page):
    """Base class for a page region (generally an element in a list of elements)."""

    def __init__(self, testsetup, element):
        self._root_element = element
        Page.__init__(self, testsetup)
