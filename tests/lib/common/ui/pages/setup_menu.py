from selenium.webdriver.common.by import By

from common.ui.pages.base import TowerPage
from common.ui.pages.regions import PageReference


class SetupCard(PageReference):
    _root_locator = (By.CLASS_NAME, 'SetupMenu')
    _description = (By.CLASS_NAME, 'SetupItem-description')
    _title = (By.CLASS_NAME, 'SetupItem-title')

    @property
    def title(self):
        return self.find_element(self._title).text

    @property
    def description(self):
        return self.find_element(self._description).text


class SetupCredentialsCard(SetupCard):
    _root_extension = (By.CSS_SELECTOR, '[class=SetupItem][ui-sref=credentials]')


class SetupUsersCard(SetupCard):
    _root_extension = (By.CSS_SELECTOR, '[class=SetupItem][ui-sref=users]')


class SetupTeamsCard(SetupCard):
    _root_extension = (By.CSS_SELECTOR, '[class=SetupItem][ui-sref=teams]')


class SetupInventoryScriptsCard(SetupCard):
    _root_extension = (By.CSS_SELECTOR, '[class=SetupItem][ui-sref=inventoryScripts]')


class SetupManagementJobsCard(SetupCard):
    _root_locator = (By.CSS_SELECTOR, "[href='#/management_jobs']")


class SetupOrganizationsCard(SetupCard):
    _root_extension = (By.CSS_SELECTOR, '[class=SetupItem][ui-sref=organizations]')
    _spinny = False


class SetupLicenseCard(SetupCard):
    _root_extension = (By.CSS_SELECTOR, '[class=SetupItem][ui-sref=license]')
    _spinny = False


class SetupAboutTowerCard(SetupCard):
    _root_extension = (By.CSS_SELECTOR, "[class=SetupItem][ng-click='showAboutModal()']")
    _spinny = False

    def after_click(self):
        return self.page


class SetupMenu(TowerPage):

    _path = '/#/setup'
    _cards = (By.CLASS_NAME, 'SetupItem')

    @property
    def credentials_card(self):
        return SetupCredentialsCard(self)

    @property
    def users_card(self):
        return SetupUsersCard(self)

    @property
    def teams_card(self):
        return SetupTeamsCard(self)

    @property
    def inventory_scripts_card(self):
        return SetupInventoryScriptsCard(self)

    @property
    def management_jobs_card(self):
        return SetupManagementJobsCard(self)

    @property
    def organizations_card(self):
        return SetupOrganizationsCard(self)

    @property
    def license_card(self):
        return SetupLicenseCard(self)

    @property
    def about_tower_card(self):
        return SetupAboutTowerCard(self)

    @property
    def displayed_card_titles(self):
        cards = [SetupCard(self, root=e) for e in self.find_elements(self._cards)]
        return [c.title for c in cards if c.is_displayed()]

    def open(self, *args, **kwargs):
        super(SetupMenu, self).open(*args, **kwargs)
        self.driver.get(self.url)
        return self

    def refresh(self):
        self.driver.refresh()
        self.wait_until_loaded()
        return self
