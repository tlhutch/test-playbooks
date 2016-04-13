from clickable import Clickable


class Link(Clickable):

    _spinny = True
    _load_page = None

    @property
    def href(self):
        return self.root.get_attribute('href')

    @property
    def load_page(self):
        return self.kwargs.get('load_page', self._load_page)

    def click(self):
        if self.load_page:
            new_page = self._get_page(self.load_page)
        else:
            new_page = self._lookup_page(self.href)

        super(Link, self).click()

        return new_page(self.base_url, self.driver).wait_until_loaded()
