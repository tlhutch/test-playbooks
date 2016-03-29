from selenium.webdriver.common.by import By

from common.ui.pages.page import Region
from common.ui.pages.regions.clickable import Clickable

from form_group import FormGroup, TextInputMixin


class LookupModal(Region):

    _root_locator = (By.CLASS_NAME, 'ui-dialog')


class LookupButton(Clickable):

    def after_click(self):
        super(LookupButton, self).after_click()
        return LookupModal(self.page)


class Lookup(TextInputMixin, FormGroup):

    _lookup_button = (By.CLASS_NAME, 'Form-lookupButton')

    @property
    def spinny(self):
        return self.kwargs.get('spinny', True)

    @property
    def lookup_button(self):
        return LookupButton(
            self.page,
            spinny=True,
            root=self.root,
            root_extension=self._lookup_button)

    @property
    def selected_option(self):
        return self.text

    def select(self, option):
        if option != self.selected_option:
            pass
            # TODO: make modal open, search, and select process opaque
            # to the test writer by modeling it as a generic form
            # widget select operation
