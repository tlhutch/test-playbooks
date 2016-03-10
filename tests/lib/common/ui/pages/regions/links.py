from selenium.webdriver.common.by import By

from clickable import Clickable


class PageReference(Clickable):

    _spinny = True

    @property
    def href(self):
        return self.root.get_attribute('href')

    def before_click(self):
        super(PageReference, self).before_click()
        self._new_page = self._lookup_page(self.href)

    def after_click(self):
        return self._new_page(self.base_url, self.driver).wait_until_loaded()


class ProjectsLink(Clickable):

    _spinny = True

    def after_click(self):
        new_page = self._get_page('Projects')
        return new_page(self.base_url, self.driver).wait_until_loaded()


class InventoriesLink(Clickable):

    _spinny = True

    def after_click(self):
        new_page = self._get_page('Inventories')
        return new_page(self.base_url, self.driver).wait_until_loaded()


class JobTemplatesLink(Clickable):

    _spinny = True

    def after_click(self):
        new_page = self._get_page('JobTemplates')
        return new_page(self.base_url, self.driver).wait_until_loaded()


class JobsLink(Clickable):

    _spinny = True

    def after_click(self):
        new_page = self._get_page('Jobs')
        return new_page(self.base_url, self.driver).wait_until_loaded()


class SetupLink(Clickable):

    _spinny = False

    def after_click(self):
        new_page = self._get_page('SetupMenu')
        return new_page(self.base_url, self.driver).wait_until_loaded()


class LogoutLink(Clickable):

    _spinny = False

    def after_click(self):
        new_page = self._get_page('Login')
        return new_page(self.base_url, self.driver).wait_until_loaded()


class UserLink(Clickable):

    _spinny = True

    def after_click(self):
        new_page = self._get_page('Users')
        return new_page(self.base_url, self.driver).wait_until_loaded()


class DashboardLink(Clickable):

    _spinny = True

    def after_click(self):
        new_page = self._get_page('Dashboard')
        return new_page(self.base_url, self.driver).wait_until_loaded()


class OrganizationsLink(Clickable):

    _spinny = True

    def after_click(self):
        new_page = self._get_page('Organizations')
        return new_page(self.base_url, self.driver).wait_until_loaded()


class ManageInventoryLink(Clickable):

    _spinny = True

    def after_click(self):
        new_page = self._get_page('ManageInventory')
        return new_page(self.base_url, self.driver).wait_until_loaded()


class ActivityStreamLink(Clickable):

    _spinny = True

    _root_locator = (By.CSS_SELECTOR, 'i[class="BreadCrumb-menuLinkImage icon-activity-stream"]')

    def after_click(self):
        new_page = self._get_page('ActivityStream')
        return new_page(self.base_url, self.driver).wait_until_loaded()
