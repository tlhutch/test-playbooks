from selenium.webdriver.common.by import By

from common.ui.pages.page import Region, RegionMap
from common.ui.pages.regions import Clickable

from groups import *  # NOQA
from lookup import Lookup


class FormPanel(RegionMap):

    _root_locator = ((By.CLASS_NAME, 'Form-header'), (By.XPATH, '..'))
    _cancel = (By.CSS_SELECTOR, "[id$='_cancel_btn']")
    _exit = (By.CSS_SELECTOR, '.Form-exit')
    _save = (By.CSS_SELECTOR, "[id$='_save_btn']")
    _title = (By.CSS_SELECTOR, '.Form-title')

    # register FormGroups as mappable regions that subclasses can reference
    # in their region_spec
    _region_registry = {
        'checkbox': Checkbox,
        'clickable': Clickable,
        'code_mirror': CodeMirror,
        'form_group': FormGroup,
        'lookup': Lookup,
        'password': Password,
        'radio_buttons': RadioButtons,
        'select': SelectDropDown,
        'text_input': TextInput
    }

    @property
    def title(self):
        return Region(
            self.page,
            root=self.root,
            root_extension=self._title)

    @property
    def cancel(self):
        return Clickable(
            self.page,
            spinny=True,
            root=self.root,
            root_extension=self._cancel)

    @property
    def save(self):
        return Clickable(
            self.page,
            spinny=True,
            root=self.root,
            root_extension=self._save)

    @property
    def exit(self):
        return Clickable(
            self.page,
            root=self.root,
            root_extension=self._exit)
