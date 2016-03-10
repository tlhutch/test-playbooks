from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By

from base import TowerCrudPage
from page import Region

from common.ui.pages.regions import Clickable

from common.ui.pages.regions.cells import (
    DeleteActionCell,
    EditActionCell,
)


class OrganizationCard(Region):
    _description = (By.CLASS_NAME, 'OrgCards-description')
    _badges = (By.CLASS_NAME, 'OrgCards-linkBadge')
    _label = (By.CLASS_NAME, 'OrgCards-label')
    _links = (By.CLASS_NAME, 'OrgCards-linkName')

    @property
    def delete(self):
        return DeleteActionCell(self.page, root=self.root)

    @property
    def edit(self):
        return EditActionCell(self.page, root=self.root)

    @property
    def badges(self):
        return self.find_elements(self._badges)

    @property
    def label(self):
        return self.find_element(self._label)

    @property
    def links(self):
        return [Clickable(self, root=e) for e in self.find_elements(self._links)]

    @property
    def displayed_link_names(self):
        return [link.text for link in self.links]

    @property
    def displayed_link_badges(self):
        return [badge.text for badge in self.badges]

    @property
    def description(self):
        return self.find_element(self._description)

    def get_badge(self, name):
        text = self._normalize_text(name)
        for n, link in enumerate(self.links):
            if self._normalize_text(link.text) == text:
                return self.badges[n]
        raise NoSuchElementException

    def get_badge_number(self, name):
        return int(self.get_badge(name).text)

    def get_link(self, name):
        text = self._normalize_text(name)
        for link in self.links:
            if self._normalize_text(link.text) == text:
                return link
        raise NoSuchElementException


class Organizations(TowerCrudPage):

    _path = '/#/organizations/{index}'

    _add_button = (By.CSS_SELECTOR, '.List-buttonSubmit')

    _cards = (By.CLASS_NAME, 'OrgCards-card')
    _badge = (By.CLASS_NAME, 'List-titleBadge')

    @property
    def cards(self):
        elements = self.find_elements(self._cards)
        return [OrganizationCard(self, root=e) for e in elements]

    @property
    def displayed_card_labels(self):
        return [c.label.text for c in self.cards if c.is_displayed()]

    @property
    def add_button(self):
        return Clickable(self, root_locator=self._add_button)

    @property
    def badge_number(self):
        return int(self.find_element(self._badge).text)

    def get_card(self, label):
        text = self._normalize_text(label)
        for card in self.cards:
            if self._normalize_text(card.label.text) == text:
                return card
        raise NoSuchElementException

    def refresh(self):
        self.driver.refresh()
        self.wait_until_loaded()
        return self
