from selenium.webdriver.support.event_firing_webdriver import EventFiringWebElement

from selector import Selector


class Region(Selector):

    _root_locator = None

    def __init__(self, page, root=None, **kwargs):
        super(Region, self).__init__(page.driver, page.timeout)
        self._root = root
        self.kwargs = kwargs
        self.page = page
        self.wait_until_loaded()

    @property
    def root_locator(self):
        return self.kwargs.get('root_locator', self._root_locator)

    @property
    def root(self):
        """Root element for the page region.
        """
        if self._root is None and self.root_locator is not None:
            return self.page.find_element(*self.root_locator)
        return self._root

    @property
    def v1(self):
        """Top-left vertex (x, y) coordinate tuple

        Coordinate units are in pixels and are relative to the top-left
        corner of the page

        v1 *--------*
           | Region |
           *--------* v2
        """
        point = self.root.location
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
        point = self.root.location
        size = self.root.size

        return (point['x'] + size['width'], point['y'] + size['height'])

    def find_element(self, *locator):
        """Find an element on the page
        """
        root = self.root
        if root is not None:
            return root.find_element(*locator)
        return self.page.find_element(*locator)

    def find_elements(self, *locator):
        """Find elements on the page
        """
        root = self.root
        if root is not None:
            return root.find_elements(*locator)
        return self.page.find_elements(*locator)

    def overlaps_with(self, other):
        """Determine if this region overlaps the bounding box of another
        Region or WebElement
        """
        if isinstance(other, EventFiringWebElement):
            other = Region(self.page, root=other)

        (x1, y1) = self.v1
        (x2, y2) = self.v2

        (x1_other, y1_other) = other.v1
        (x2_other, y2_other) = other.v2

        return x1 < x2_other and x2 > x1_other and y1 < y2_other and y2 > y1_other

    def surrounds(self, other):
        """Determine if this region fully surrounds the bounding box of
        another Region or WebElement
        """
        if isinstance(other, EventFiringWebElement):
            other = Region(self.page, root=other)

        (x1, y1) = self.v1
        (x2, y2) = self.v2

        (x1_other, y1_other) = other.v1
        (x2_other, y2_other) = other.v2

        return x1 < x1_other and y1 < y1_other and x2 > x2_other and y2 > y2_other

    def wait_until_loaded(self):
        """Wait for the region to load - override or extend as needed
        """
        return self


class RegionMap(Region):

    # Region subclasses are mapped to keys that are usable from within
    # a region spec
    _region_registry = {'default': Region}

    # The region_spec maps a property attribute name to a dictionary
    # key that is used to lookup a region object in the registry and
    # initialize it with a set of keyword arguments.
    _region_spec = {}

    def __getattr__(self, name):
        try:
            spec = self._region_spec[name]
        except KeyError:
            raise AttributeError
        else:
            return self._load_region(name, spec)

    def __init__(self, page, **kwargs):
        super(RegionMap, self).__init__(page, **kwargs)
        self._region_cache = {}

    def _load_region(self, name, spec):
        """Lookup and initialize a region from the region registry using the
        provided spec dictionary
        """
        try:
            return self._region_cache[name]
        except KeyError:
            region_cls = self._region_registry[spec.get('region_type', 'default')]
            element = self.page.find_element(*spec['root_locator'])
            self._region_cache[name] = region_cls(self.page, root=element, **spec)
            return self._region_cache[name]

    def get_regions(self, **kwargs):
        """Generate (name, region) tuples for regions defined in the
        region spec. Results can be filtered by spec dictionary values
        using keyword arguments.
        """
        for name, spec in self._region_spec.iteritems():
            if all(spec.get(k) == v for k, v in kwargs.iteritems()):
                yield (name, self._load_region(name, spec))
