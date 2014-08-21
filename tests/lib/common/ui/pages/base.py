from common.ui.pages import Page
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By


class Base(Page):
    '''
    Base class for global project specific functions
    '''

    _breadcrumb_title = 'Not defined'

    @property
    def page_title(self):
        WebDriverWait(self.selenium, self.timeout).until(lambda s: self.selenium.title)
        return self.selenium.title

    def go_to_login_page(self):
        self.selenium.get(self.base_url)
        from common.ui.pages.login import Login_Page
        return Login_Page(self.testsetup)

    def logout(self):
        '''convenience method to logout of tower by accessing the header'''
        return self.header.logout()

    @property
    def header(self):
        from common.ui.pages.regions.header import HeaderRegion
        return HeaderRegion(self.testsetup)

    @property
    def is_logged_in(self):
        return self.header.is_logged_in

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
        return self.has_breadcrumb and self._breadcrumb_title == self.breadcrumb.active_crumb

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
