import base
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class Api_Browser_Page(base.Base):
    # TODO: This obviously should change. File bug
    _logo_locator = (By.CSS_SELECTOR, 'img.logo')
    _get_button_locator = (By.CSS_SELECTOR, 'form#get-form a.btn')
    _options_button_locator = (By.CSS_SELECTOR, 'form.button-form > button.btn')

    def __init__(self, *args, **kwargs):
        super(Api_Browser_Page, self).__init__(*args, **kwargs)
        self.base_url = self.base_url + '/api'

    @property
    def is_the_current_page(self):
        '''Override the base implementation to make sure that we are actually on a API Browser page
        '''
        return super(Api_Browser_Page, self).is_the_current_page \
            and self.is_element_visible(*self._logo_locator) \
            and self.is_element_visible(*self._get_button_locator) \
            and self.is_element_visible(*self._options_button_locator)

    @property
    def get_button(self):
        return self.selenium.find_element(*self._get_button_locator)

    @property
    def options_button(self):
        return self.selenium.find_element(*self._options_button_locator)

class Api_Browser_Home(Api_Browser_Page):
    _page_title = u"REST API \xb7 Ansible Tower REST API"
    _href_locator = (By.CSS_SELECTOR, "a[href = '{href}']")
    _v1_link_locator = (By.CSS_SELECTOR, "a[href = '/api/v1/']")

    def click_v1_link(self):
        self.selenium.find_element(*self._v1_link_locator).click()
        return Api_Browser_v1(self.testsetup)

    def click_by_href(self, href):
        self.selenium.find_element(*(x.format(href=href) for x in self._href_locator)).click()
        return Api_Browser_Home(self.testsetup)

    def login(self):
        '''this doesn't yet work ... can't figure out how to deal with http
        auth browser alert
        '''
        wait = WebDriverWait(self.selenium, self.timeout)
        # throws timeout exception if not found
        wait.until(EC.alert_is_present())
        popup = self.selenium.switch_to_alert()
        print popup.text
        popup.dismiss()
        #popup.accept()

class Api_Browser_v1(Api_Browser_Page):
    _page_title = u"Version 1 \xb7 Ansible Tower REST API"

