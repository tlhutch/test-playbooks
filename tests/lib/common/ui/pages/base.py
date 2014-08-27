import logging
from selenium.common.exceptions import NoSuchElementException
from common.ui.pages import Page, PageRegion


log = logging.getLogger(__name__)


class Base(Page):
    '''
    Base class for Tower UI pages
    '''

    _page_title = 'Ansible Tower'
    _breadcrumb_title = 'UNDEFINED'

    def go_to_login_page(self):
        self.selenium.get(self.base_url)
        from common.ui.pages.login import Login_Page
        self.wait_for_spinny()
        return Login_Page(self.testsetup)

    @property
    def account_menu(self):
        from common.ui.pages.regions.account_menu import Account_Menu
        return Account_Menu(self.testsetup)

    @property
    def is_logged_in(self):
        return self.account_menu.is_logged_in

    def logout(self):
        self.account_menu.show()
        return self.account_menu.click_logout()

    @property
    def alert_dialog(self):
        from common.ui.pages.regions.alert_dialog import Alert_Dialog
        return Alert_Dialog(self.testsetup)

    @property
    def has_alert_dialog(self):
        return self.alert_dialog.is_displayed()

    @property
    def breadcrumb(self):
        from common.ui.pages.regions.breadcrumb import BreadCrumb
        return BreadCrumb(self.testsetup)

    @property
    def has_breadcrumb(self):
        return self.breadcrumb.is_displayed()

    @property
    def is_the_active_breadcrumb(self):
        assert self.has_breadcrumb, "No breadcrumb visible"
        assert self._breadcrumb_title == self.breadcrumb.active_crumb, \
            "Expected breadcrumb title: %s. Actual breadcrumb title: %s" % \
            (self._breadcrumb_title, self.breadcrumb.active_crumb)  # IGNORE:E1101

        return True

    @property
    def csrf_token(self):
        csrf_meta = self.selenium.find_element_by_css_selector("meta[name=csrf-token]")
        return csrf_meta.get_attribute('content')

    @csrf_token.setter
    def csrf_token(self, value):
        # Changing the CSRF Token on the fly via the DOM by iterating
        # over the meta tags
        script = '''
            var elements = document.getElementsByTagName("meta");
            for (var i=0, element; element = elements[i]; i++) {
                var ename = element.getAttribute("name");
                if (ename != null && ename.toLowerCase() == "csrf-token") {
                    element.setAttribute("content", "%s");
                    break;
                }
            }
        ''' % value
        self.selenium.execute_script(script)

    @property
    def is_on_dashboard_page(self):
        '''Return whether the currently loaded page is the dashboard page'''
        return self.get_current_page_path().startswith('/home')

    @property
    def main_menu(self):
        from common.ui.pages.regions.main_menu import Main_Menu
        return Main_Menu(self.testsetup)

    @property
    def is_the_active_tab(self):
        '''Return whether the current page is the active/highlighted tab'''
        if not hasattr(self, '_tab_title'):
            log.warning("_tab_title is not set for class '%s'" % self.__class__.__name__)
            return True

        # determine selected tab
        try:
            active_tab = self.main_menu.active_item
        except NoSuchElementException:
            log.warning("unable to determine the active tab")
            active_tab = None

        # if no selected tab, is dashboard page active
        if active_tab is None and self.is_on_dashboard_page:
            active_tab = "Home"

        assert self._tab_title == active_tab, \
            "Expected tab title: %s. Actual tab title: %s" % \
            (self._tab_title, active_tab)

        return True


class BaseRegion(PageRegion, Base):
    '''sub-class'''
