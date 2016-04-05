import time

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
        return self.kwargs.get('spinny', False)

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

    #
    # The retry + poll logic in the two methods below are a temporary
    # workaround for https://github.com/ansible/ansible-tower/issues/1461
    # and should be removed when this issue is resolved.
    #
    def set_text(self, text, retry=True):
        if retry:
            self._set_text_with_retry(text)
        else:
            TextInputMixin.set_text(self, text)

    def _set_text_with_retry(self, text):
        timeout = time.time() + 25
        while True:
            self.clear()
            TextInputMixin.set_text(self, text)
            time.sleep(1)
            if not self.errors or time.time() > timeout:
                break
