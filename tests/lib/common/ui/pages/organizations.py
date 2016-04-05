from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By

from base import TowerCrudPage
from page import Region

from common.ui.pages.regions import Clickable
from common.ui.pages.forms import FormPanel
from common.ui.pages.regions.tabs import PanelTab

from common.ui.pages.regions.cells import (
    DeleteActionCell,
    EditActionCell,
)


class OrganizationDetails(FormPanel):

    _region_spec = {
        'description': {
            'region_type': 'text_input',
            'root_locator': (
                (By.CSS_SELECTOR, 'label[for=description]'),
                (By.XPATH, '..'))
        },
        'name': {
            'required': True,
            'region_type': 'text_input',
            'root_locator': (
                (By.CSS_SELECTOR, 'label[for=name]'),
                (By.XPATH, '..'))
        }
    }


class Organizations(TowerCrudPage):

    _path = '/#/organizations/{index}'

    _add_button = (By.CSS_SELECTOR, '.List-buttonSubmit')
    _badge = (By.CLASS_NAME, 'List-titleBadge')
    _cards = (By.CLASS_NAME, 'OrgCards-card')
    _details_tab = (By.ID, 'organization_tab')

    @property
    def forms(self):
        return [self.details]

    @property
    def details_tab(self):
        return PanelTab(self, root_locator=self._details_tab)

    @property
    def details(self):
        self.details_tab.enable()
        return OrganizationDetails(self)

    @property
    def add_button(self):
        return Clickable(self, root_locator=self._add_button)

    @property
    def badge_number(self):
        return int(self.find_element(self._badge).text)

    @property
    def cards(self):
        elements = self.find_elements(self._cards)
        return [OrganizationCard(self, root=element) for element in elements]

    @property
    def displayed_card_labels(self):
        return [card.label.text for card in self.cards if card.is_displayed()]

    def get_card(self, label_text):
        label_text = self._normalize_text(label_text)
        for card in self.cards:
            if card.label.normalized_text == label_text:
                return card
        raise NoSuchElementException

    def refresh(self):
        self.driver.refresh()
        self.wait_until_loaded()
        return self


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
    def description(self):
        return Region(self.page, root=self.find_element(self._description))

    @property
    def label(self):
        return Region(self.page, root=self.find_element(self._label))

    @property
    def badges(self):
        elements = self.find_elements(self._badges)
        return [Region(self.page, root=e) for e in elements]

    @property
    def links(self):
        elements = self.find_elements(self._links)
        return [Clickable(self.page, root=e) for e in elements]

    @property
    def displayed_link_names(self):
        return [k.text for k in self.links if k.is_displayed()]

    @property
    def displayed_link_badges(self):
        return [badge.text for badge in self.badges]

    def get_badge(self, name):
        name = self._normalize_text(name)
        for n, link in enumerate(self.links):
            if link.normalized_text == name:
                return self.badges[n]
        raise NoSuchElementException

    def get_badge_number(self, name):
        return int(self.get_badge(name).text)

    def get_link(self, name):
        name = self._normalize_text(name)
        for link in self.links:
            if link.normalized_text == name:
                return link
        raise NoSuchElementException
