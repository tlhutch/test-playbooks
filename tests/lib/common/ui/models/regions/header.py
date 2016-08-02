from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By

from common.ui.page import Region


__all__ = ['Header', 'MobileHeader']


class BaseHeader(Region):

    _logo = (By.ID, 'main_menu_logo')
    _socket_status = (By.ID, 'main_menu_socket_status_notification')

    @property
    def logo(self):
        return self.find_element(*self._logo)

    @property
    def socket_status(self):
        return self.find_element(*self._socket_status)

    def is_displayed(self):
        return self.logo.is_displayed()

    def wait_until_loaded(self):
        return self


class Header(BaseHeader):

    _docs = (By.ID, 'main_menu_docs_link')
    _inventories = (By.ID, 'main_menu_inventories_link')
    _jobs = (By.ID, 'main_menu_jobs_link')
    _job_templates = (By.ID, 'main_menu_job_templates_link')
    _logout = (By.ID, 'main_menu_logout_link')
    _portal = (By.ID, 'main_menu_portal_link')
    _projects = (By.ID, 'main_menu_projects_link')
    _setup = (By.ID, 'main_menu_setup_link')
    _user = (By.ID, 'main_menu_current_user_link')
    _username = (By.CLASS_NAME, 'MainMenu-item--user')

    @property
    def docs(self):
        return self.find_element(*self._docs)

    @property
    def inventories(self):
        return self.find_element(*self._inventories)

    @property
    def jobs(self):
        return self.find_element(*self._jobs)

    @property
    def job_templates(self):
        return self.find_element(*self._job_templates)

    @property
    def logout(self):
        return self.find_element(*self._logout)

    @property
    def portal(self):
        return self.find_element(*self._portal)

    @property
    def projects(self):
        return self.find_element(*self._projects)

    @property
    def setup(self):
        return self.find_element(*self._setup)

    @property
    def toggle(self):
        return self.find_element(*self._toggle)

    @property
    def user(self):
        return self.find_element(*self._user)

    @property
    def username(self):
        element = self.find_element(*self._username)
        return element.text


class MobileHeader(BaseHeader):

    _docs = (By.ID, 'main_menu_docs_mobile_link')
    _inventories = (By.ID, 'main_menu_inventories_mobile_link')
    _jobs = (By.ID, 'main_menu_jobs_mobile_link')
    _job_templates = (By.ID, 'main_menu_job_templates_mobile_link')
    _logout = (By.ID, 'main_menu_logout_mobile_link')
    _projects = (By.ID, 'main_menu_projects_mobile_link')
    _setup = (By.ID, 'main_menu_setup_mobile_link')
    _toggle = (By.ID, 'main_menu_mobile_toggle_button')
    _user = (By.ID, 'main_menu_current_user_mobile_link')

    @property
    def docs(self):
        return self.find_element(*self._docs)

    @property
    def inventories(self):
        return self.find_element(*self._inventories)

    @property
    def jobs(self):
        return self.find_element(*self._jobs)

    @property
    def job_templates(self):
        return self.find_element(*self._job_templates)

    @property
    def portal(self):
        for element in self.find_elements(*self._setup):
            if 'portal' in element.text.lower():
                return element
        raise NoSuchElementException

    @property
    def logout(self):
        return self.find_element(*self._logout)

    @property
    def projects(self):
        return self.find_element(*self._projects)

    @property
    def setup(self):
        for element in self.find_elements(*self._setup):
            if 'settings' in element.text.lower():
                return element
        raise NoSuchElementException

    @property
    def toggle(self):
        return self.find_element(*self._toggle)

    @property
    def user(self):
        return self.find_element(*self._user)

    @property
    def username(self):
        return self.user.text.split().pop()

    def expand(self):
        if not self.logout.is_displayed():
            self.toggle.click()
        return self

    def collapse(self):
        if self.logout.is_displayed():
            self.toggle.click()
        return self

    def is_displayed(self):
        return self.toggle.is_displayed()
