from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from common.ui.pages import BaseRegion


class Accordion_Region(BaseRegion):
    _root_locator = (By.CLASS_NAME, 'ui-accordion')
    _header_locator = (By.CLASS_NAME, 'ui-accordion-header')
    _content_locator = (By.CLASS_NAME, 'ui-accordion-content')
    _related = dict()  # Provided by caller

    def get(self, name):
        '''Return a (header, content) tuple for the accordion matching the provided name'''
        i = self._find_header_by_name(name)
        return (self.headers[i], self.contents[i])

    def click(self, name):
        '''Expand an according and return the related content object'''
        (hdr, content) = self.get(name)
        hdr.expand()
        # Wait until expanded
        # WebDriverWait(self.selenium, self.timeout).until(lambda s: content._root_element.is_displayed())
        return content

    def _find_header_by_name(self, name):
        for i, hdr in enumerate(self.headers):
            if hdr.title == name:
                return i
        raise Exception("No accordion found with name:%s" % name)

    def items(self):
        '''Returns a list of tuples for each accordion (header, content)'''
        return zip(self.headers, self.contents)

    @property
    def headers(self):
        '''Returns all accordion headers'''
        return [Accordion_Header(self.testsetup, _root_element=hdr) for hdr in self.find_elements(*self._header_locator)]

    @property
    def contents(self):
        '''Returns all accordion contents'''
        # return [Accordion_Content(self.testsetup, _root_element=el) for el in self.find_elements(*self._content_locator)]
        result = list()
        for i, el in enumerate(self.find_elements(*self._content_locator)):
            # Choose an appropriate region class (default: Accordion_Content)
            related_cls = self.get_related(self.headers[i].title, Accordion_Content)
            result.append(related_cls(self.testsetup, _root_element=el))
        return result


class Accordion_Content(BaseRegion):
    _root_locator = None  # Set by caller


class Accordion_Header(BaseRegion):
    _root_locator = None  # Set by caller
    _icon_locator = (By.CLASS_NAME, 'ui-accordion-header-icon')

    def expand(self):
        '''Show the accordion'''
        if self.is_collapsed():
            self._root_element.click()

    def collapse(self):
        '''Hide the accordion'''
        if self.is_element_visible(*self._submenu_locator):
            self.find_element(*self._menu_link_locator).click()

    def is_collapsed(self):
        '''Return whether the accordion is collapsed'''
        return 'ui-icon-triangle-1-e' in self.find_element(*self._icon_locator).get_attribute('class')

    def is_expanded(self):
        '''Return whether the accordion is expanded'''
        return not self.is_collapsed()

    @property
    def title(self):
        '''Return the accordion title'''
        return self._root_element.text

    def click(self):
        '''Click the accordion title'''
        return self._root_element.click()
