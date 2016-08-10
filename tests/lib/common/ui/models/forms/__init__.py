from selenium.webdriver.common.by import By

from common.ui.page import RegionMap

from lookup import Lookup
from groups import (
    Checkbox,
    CodeMirror,
    Email,
    FormGroup,
    Password,
    RadioButtons,
    SelectDropdown,
    TextInput,
    TextArea,
)


class FormPanel(RegionMap):

    _root_locator = [(By.CLASS_NAME, 'Form-header'), (By.XPATH, '..')]
    _cancel = (By.CSS_SELECTOR, "[id$='_cancel_btn']")
    _exit = (By.CSS_SELECTOR, '.Form-exit')
    _save = (By.CSS_SELECTOR, "[id$='_save_btn']")
    _title = (By.CSS_SELECTOR, '.Form-title')

    # register FormGroups as mappable regions that subclasses can reference
    # in their region_spec
    _region_registry = {
        'checkbox': Checkbox,
        'default': FormGroup,
        'code_mirror': CodeMirror,
        'email': Email,
        'form_group': FormGroup,
        'lookup': Lookup,
        'password': Password,
        'radio_buttons': RadioButtons,
        'select': SelectDropdown,
        'text_input': TextInput,
        'text_area': TextArea
    }

    @property
    def title(self):
        return self.find_element(*self._title)

    @property
    def cancel(self):
        return self.find_element(*self._cancel)

    @property
    def save(self):
        return self.find_element(*self._save)

    @property
    def exit(self):
        return self.find_element(*self._exit)

    def scroll_save_into_view(self):
        element = self.find_element(*self._save)
        # scroll to the element and then up another few pixels so it is
        # not obstructed by the menu at the top of the tower page
        js = "arguments[0].scrollIntoView(true);window.scrollBy(0,-120)"
        self.driver.execute_script(js, element)
        return element
