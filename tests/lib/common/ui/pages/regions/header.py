from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By

from common.ui.pages.page import Region

from clickable import Clickable

from links import (
    LogoutLink,
    DashboardLink,
    ProjectsLink,
    InventoriesLink,
    JobTemplatesLink,
    JobsLink,
    SetupLink,
    UserLink,
)


class HeaderProjectsLink(ProjectsLink):
    _root_locator = (By.ID, 'main_menu_projects_link')


class HeaderInventoriesLink(InventoriesLink):
    _root_locator = (By.ID, 'main_menu_inventories_link')


class HeaderJobTemplatesLink(JobTemplatesLink):
    _root_locator = (By.ID, 'main_menu_job_templates_link')


class HeaderJobsLink(JobsLink):
    _root_locator = (By.ID, 'main_menu_jobs_link')


class HeaderSetupLink(SetupLink):
    _root_locator = (By.ID, 'main_menu_setup_link')


class HeaderDocsLink(Clickable):
    _root_locator = (By.ID, 'main_menu_docs_link')


class HeaderLogoutLink(LogoutLink):
    _spinny = False
    _root_locator = (By.ID, 'main_menu_logout_link')


class HeaderUserLink(UserLink):
    _root_locator = (By.ID, 'main_menu_current_user_link')


class HeaderStandard(Region):

    _user = (By.CLASS_NAME, 'MainMenu-item--user')

    @property
    def projects_link(self):
        return HeaderProjectsLink(self.page)

    @property
    def inventories_link(self):
        return HeaderInventoriesLink(self.page)

    @property
    def job_templates_link(self):
        return HeaderJobTemplatesLink(self.page)

    @property
    def jobs_link(self):
        return HeaderJobsLink(self.page)

    @property
    def user_link(self):
        return HeaderUserLink(self.page)

    @property
    def docs_link(self):
        return HeaderDocsLink(self.page)

    @property
    def logout_link(self):
        return HeaderLogoutLink(self.page)

    @property
    def setup_link(self):
        return HeaderSetupLink(self.page)

    @property
    def user(self):
        return self.find_element(self._user).text.lower()

    def is_displayed(self):
        return self.is_element_displayed(self.user_link._root_locator)


class HeaderProjectsMobileLink(ProjectsLink):
    _root_locator = (By.ID, 'main_menu_projects_mobile_link')


class HeaderInventoriesMobileLink(InventoriesLink):
    _root_locator = (By.ID, 'main_menu_inventories_mobile_link')


class HeaderJobTemplatesMobileLink(JobTemplatesLink):
    _root_locator = (By.ID, 'main_menu_job_templates_mobile_link')


class HeaderJobsMobileLink(JobsLink):
    _root_locator = (By.ID, 'main_menu_jobs_mobile_link')


class HeaderSetupMobileLink(SetupLink):
    _root_locator = (By.ID, 'main_menu_setup_mobile_link')


class HeaderLogoutMobileLink(LogoutLink):
    _spinny = False
    _root_locator = (By.ID, 'main_menu_logout_mobile_link')


class HeaderToggleMobileButton(Clickable):
    _root_locator = (By.ID, 'main_menu_mobile_toggle_button')


class HeaderUserMobileLink(UserLink):
    _root_locator = (By.ID, 'main_menu_current_user_mobile_link')


class HeaderDocsMobileLink(Region):
    _root_locator = (By.ID, 'main_menu_docs_mobile_link')


class HeaderMobile(Region):

    @property
    def projects_link(self):
        return HeaderProjectsMobileLink(self.page)

    @property
    def inventories_link(self):
        return HeaderInventoriesMobileLink(self.page)

    @property
    def job_templates_link(self):
        return HeaderJobTemplatesMobileLink(self.page)

    @property
    def jobs_link(self):
        return HeaderJobsMobileLink(self.page)

    @property
    def user_link(self):
        return HeaderUserMobileLink(self.page)

    @property
    def docs_link(self):
        return HeaderDocsMobileLink(self.page)

    @property
    def logout_link(self):
        return HeaderLogoutMobileLink(self.page)

    @property
    def setup_link(self):
        return HeaderSetupMobileLink(self.page)

    @property
    def toggle_mobile_button(self):
        return HeaderToggleMobileButton(self.page)

    @property
    def user(self):
        user_text = self.user_link.root.text.lower()

        if user_text == '':
            return user_text

        return user_text.split()[-1]

    def is_displayed(self):
        return self.is_element_displayed(
            self.toggle_mobile_button._root_locator)


class Logo(DashboardLink):
    _root_locator = (By.ID, 'main_menu_logo')


class SocketStatusNotification(Region):
    _root_locator = (By.ID, 'main_menu_socket_status_notification')


class Header(Region):

    _item_locator = (By.CLASS_NAME, 'MainMenu-item')
    _is_current_route = (By.CLASS_NAME, 'is-currentRoute')

    @property
    def projects_link(self):
        return self.current_menu.projects_link

    @property
    def inventories_link(self):
        return self.current_menu.inventories_link

    @property
    def job_templates_link(self):
        return self.current_menu.job_templates_link

    @property
    def jobs_link(self):
        return self.current_menu.jobs_link

    @property
    def user_link(self):
        return self.current_menu.user_link

    @property
    def setup_link(self):
        return self.current_menu.setup_link

    @property
    def docs_link(self):
        return self.current_menu.docs_link

    @property
    def logout_link(self):
        return self.current_menu.logout_link

    @property
    def logo(self):
        return Logo(self.page)

    @property
    def socket_status_notification(self):
        return SocketStatusNotification(self.page)

    @property
    def user(self):
        return self.current_menu.user

    @property
    def current_route_id(self):
        return self.find_element(self._is_current_route).get_attribute('id')

    @property
    def displayed_link_labels(self):
        labels = []
        for element in self.find_elements(self._item_locator):
            if element.is_displayed():
                labels.append(self._normalize_text(element.text))
        return labels

    @property
    def current_menu(self):
        if self.standard_menu.is_displayed():
            if self.mobile_menu.is_displayed():
                raise NoSuchElementException(
                    "Both header menus are visible - this shouldn't happen")
            return self.standard_menu

        elif self.mobile_menu.is_displayed():
            # Ensure the mobile menu is expanded if we're accessing it through
            # the header.current_menu property
            if len(self.displayed_link_labels) == 0:
                self.mobile_menu.toggle_mobile_button.click()
            return self.mobile_menu
        else:
            raise NoSuchElementException

    def __init__(self, page, **kwargs):
        super(Header, self).__init__(page, **kwargs)

        self.standard_menu = HeaderStandard(self.page)
        self.mobile_menu = HeaderMobile(self.page)

    def is_displayed(self):
        try:
            return self.current_menu.is_displayed()
        except NoSuchElementException:
            return False
