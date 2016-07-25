from selenium.webdriver.common.by import By

from common.ui.page import Region
from common.ui.models.base import TowerPage


__all__ = ['SetupMenu']


class SetupMenu(TowerPage):

    url_template = '/#/setup'
    _cards = (By.CLASS_NAME, 'SetupItem')

    @property
    def cards(self):
        elements = self.find_elements(*self._cards)
        return [SetupCard(self, root=e) for e in elements]

    @property
    def card_titles(self):
        return [c.title.text for c in self.cards if c.title.text]

    def wait_until_loaded(self):
        self.wait.until(lambda _: self.card_titles)


class SetupCard(Region):

    _description = (By.CLASS_NAME, 'SetupItem-description')
    _title = (By.CLASS_NAME, 'SetupItem-title')
    
    @property
    def title(self):
        return self.find_element(*self._title)

    @property
    def description(self):
        return self.find_element(*self._description)

    @property
    def href(self):
        return self.root.get_attribute('href')
