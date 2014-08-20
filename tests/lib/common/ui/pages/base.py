import page
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By


def input_getter(locator):
    '''
    Generic property fget method
    '''
    def get_field(self):
        return self.get_visible_element(*locator).get_attribute('value')
    return get_field


def input_setter(locator):
    '''
    Generic property fset method
    '''
    def set_field(self, value):
        el = self.get_visible_element(*locator)
        el.clear()
        el.send_keys(value)
    return set_field


class Base(page.Page):
    '''
    Base class for global project specific functions
    '''
    @property
    def page_title(self):
        WebDriverWait(self.selenium, self.timeout).until(lambda s: self.selenium.title)
        return self.selenium.title

    @property
    def header(self):
        from regions.header import HeaderRegion
        return HeaderRegion(self.testsetup)

    @property
    def is_logged_in(self):
        return self.header.is_logged_in

    @property
    def current_subpage(self):
        submenu_name = self.selenium.find_element_by_tag_name("body").get_attribute("id")
        return self.submenus[submenu_name](self.testsetup)  # IGNORE:E1101

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

    def go_to_login_page(self):
        self.selenium.get(self.base_url)
