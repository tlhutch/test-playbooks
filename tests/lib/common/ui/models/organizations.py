from selenium.webdriver.common.by import By

from common.ui.page import Region
from common.ui.models.base import TowerPage
from common.ui.models.forms import FormPanel

from common.ui.models.regions import (
    ListPagination,
    Tab,
    TagSearch,
)

__all__ = ['Organizations', 'OrganizationAdd', 'OrganizationEdit']


class Organizations(TowerPage):

    url_template = '/#/organizations'

    _add = (By.CSS_SELECTOR, '.List-buttonSubmit')
    _badge = (By.CLASS_NAME, 'List-titleBadge')
    _cards = (By.CLASS_NAME, 'OrgCards-card')
    _noitems = (By.CLASS_NAME, 'List-noItems')
    _selected_card = (By.CLASS_NAME, 'OrgCards-card--selected')

    @property
    def add(self):
        return self.find_element(*self._add)

    @property
    def cards(self):
        elements = self.find_elements(*self._cards)
        return [OrganizationCard(self, root=e) for e in elements]

    @property
    def list_badge(self):
        return self.find_element(*self._badge)

    @property
    def list_pagination(self):
        return ListPagination(self)

    @property
    def list_search(self):
        return TagSearch(self)

    @property
    def selected_card(self):
        elements = self.find_elements(*self._selected_card)
        assert len(elements) <= 1, 'multiple results found'
        if not elements:
            return None
        return OrganizationCard(self, root=elements.pop())

    def is_loaded(self):
        if not self.is_element_displayed(*self._badge):
            return False
        locators = [self._cards, self._noitems]
        return any(self.is_element_displayed(*loc) for loc in locators)

    def query_cards(self, query_filter):
        return [c for c in self.cards if query_filter(c)]

    def wait_until_loaded(self):
        self.wait.until(lambda _: self.is_loaded())


class OrganizationAdd(Organizations):

    url_template = '/#/organizations/add'

    @property
    def details(self):
        DetailsTab(self).enable()
        return OrganizationDetails(self)


class OrganizationEdit(Organizations):

    url_template = '/#/organizations/{id}'

    @property
    def details(self):
        DetailsTab(self).enable()
        return OrganizationDetails(self)

    @property
    def notifications(self):
        NotificationsTab(self).enable()
        return FormPanel(self)

    @property
    def permissions(self):
        PermissionsTab(self).enable()
        return FormPanel(self)


class OrganizationCard(Region):

    _badges = (By.CLASS_NAME, 'OrgCards-linkBadge')
    _delete = (By.CLASS_NAME, 'List-actionButton--delete')
    _description = (By.CLASS_NAME, 'OrgCards-description')
    _edit = (By.CSS_SELECTOR, 'i[class*=fa-pencil]')
    _label = (By.CLASS_NAME, 'OrgCards-label')
    _links = (By.CLASS_NAME, 'OrgCards-linkName')
    _selected_card = (By.CLASS_NAME, 'OrgCards-card--selected')

    @property
    def delete(self):
        return self.find_element(*self._delete)

    @property
    def description(self):
        return self.find_element(*self._description)

    @property
    def edit(self):
        return self.find_element(*self._edit)

    @property
    def name(self):
        return self.find_element(*self._label)

    @property
    def badges(self):
        badge_map = {}
        for element in self.find_elements(*self._badges):
            parent = element.find_element(By.XPATH, '..')
            link = parent.find_element(*self._links)
            link_text = link.text
            if link_text:
                badge_map[link_text] = element
        return badge_map

    @property
    def links(self):
        link_map = {}
        for element in self.find_elements(*self._links):
            link_text = element.text
            if link_text:
                link_map[link_text] = element
        return link_map

    def is_selected(self):
        # find the currently selected card
        elements = self.page.find_elements(*self._selected_card)
        # if no cards are selected, stop here
        if not elements:
            return False
        selected_card = OrganizationCard(root=elements.pop())
        # compare label of selected card to that of this card
        return self.label.text == selected_card.label.text


class DetailsTab(Tab):
    _root_locator = (By.ID, 'organization_tab')


class NotificationsTab(Tab):
    _root_locator = (By.ID, 'notifications_tab')


class PermissionsTab(Tab):
    _root_locator = (By.ID, 'permissions_tab')


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
