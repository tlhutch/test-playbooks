from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By

from common.ui.pages.page import Region

from links import Link


class BaseHeader(Region):

    @property
    def projects(self):
        return Link(
            self.page,
            root_locator=self._projects,
            load_page='Projects',
            spinny=True)

    @property
    def inventories(self):
        return Link(
            self.page,
            root_locator=self._inventories,
            load_page='Inventories',
            spinny=True)

    @property
    def job_templates(self):
        return Link(
            self.page,
            root_locator=self._job_templates,
            load_page='JobTemplates',
            spinny=True)

    @property
    def jobs(self):
        return Link(
            self.page,
            root_locator=self._jobs,
            load_page='Jobs',
            spinny=True)

    @property
    def user(self):
        return Link(
            self.page,
            root_locator=self._user,
            load_page='Users',
            spinny=True)

    @property
    def docs(self):
        return Link(
            self.page,
            root_locator=self._docs,
            spinny=False)

    @property
    def logout(self):
        return Link(
            self.page,
            root_locator=self._logout,
            load_page='Login',
            spinny=False)

    @property
    def setup(self):
        return Link(
            self.page,
            root_locator=self._setup,
            load_page='SetupMenu',
            spinny=True)


class HeaderStandard(BaseHeader):

    _projects = (By.ID, 'main_menu_projects_link')
    _inventories = (By.ID, 'main_menu_inventories_link')
    _job_templates = (By.ID, 'main_menu_job_templates_link')
    _jobs = (By.ID, 'main_menu_jobs_link')
    _setup = (By.ID, 'main_menu_setup_link')
    _docs = (By.ID, 'main_menu_docs_link')
    _logout = (By.ID, 'main_menu_logout_link')
    _user = (By.ID, 'main_menu_current_user_link')
    _username = (By.CLASS_NAME, 'MainMenu-item--user')

    def is_displayed(self):
        return self.user.is_displayed()

    @property
    def username(self):
        un = Region(self.page, root_locator=self._username)
        un.wait_until_displayed()
        return un.text


class HeaderMobile(BaseHeader):

    _projects = (By.ID, 'main_menu_projects_mobile_link')
    _inventories = (By.ID, 'main_menu_inventories_mobile_link')
    _job_templates = (By.ID, 'main_menu_job_templates_mobile_link')
    _jobs = (By.ID, 'main_menu_jobs_mobile_link')
    _setup = (By.ID, 'main_menu_setup_mobile_link')
    _logout = (By.ID, 'main_menu_logout_mobile_link')
    _user = (By.ID, 'main_menu_current_user_mobile_link')
    _docs = (By.ID, 'main_menu_docs_mobile_link')

    _toggle_mobile_button = (By.ID, 'main_menu_mobile_toggle_button')

    @property
    def toggle_mobile_button(self):
        return Region(self.page, root_locator=self._toggle_mobile_button)

    def is_displayed(self):
        return self.toggle_mobile_button.is_displayed()

    @property
    def username(self):
        user_text = self.user.text

        if user_text == '':
            return user_text

        return user_text.split()[-1]


class Header(Region):

    _link_labels = (By.CLASS_NAME, 'MainMenu-item')
    _is_current_route = (By.CLASS_NAME, 'is-currentRoute')
    _socket_status = (By.ID, 'main_menu_socket_status_notification')
    _logo = (By.ID, 'main_menu_logo')

    @property
    def logo(self):
        return Link(self.page, root_locator=self._logo, load_page='Dashboard', spinny=True)

    @property
    def socket_status(self):
        return Region(self.page, root_locator=self._socket_status)

    @property
    def current_route_id(self):
        icr = Region(self.page, root_locator=self._is_current_route)
        icr.wait_until_displayed()
        return icr.root.get_attribute('id')

    @property
    def link_labels(self):
        return [Region(self.page, root=e) for e in self.find_elements(self._link_labels)]

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
            if not filter(lambda r: r.is_displayed(), self.link_labels):
                self.mobile_menu.toggle_mobile_button.click()
            return self.mobile_menu
        else:
            raise NoSuchElementException

    def __init__(self, page, **kwargs):
        super(Header, self).__init__(page, **kwargs)

        self.standard_menu = HeaderStandard(self.page)
        self.mobile_menu = HeaderMobile(self.page)

    def __getattr__(self, name):
        return getattr(self.current_menu, name)

    def is_displayed(self):
        try:
            return self.current_menu.is_displayed()
        except NoSuchElementException:
            return False
