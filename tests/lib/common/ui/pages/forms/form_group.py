from selenium.webdriver.common.by import By

from common.ui.pages.page import Region
from common.ui.pages.regions.spinny import Spinny


class FormGroup(Region):
    # Subclasses of FormGroup must define a root locator that uniquely
    # identifies the Form-formGroup element associated with the widget
    # being modeled.
    _root_locator = None

    _label = (By.CSS_SELECTOR, 'label')
    _help = (By.CSS_SELECTOR, "a[id*='awp-']")

    @property
    def required(self):
        return self.kwargs.get('required', False)

    @property
    def help(self):
        """Get the formGroup help popover region
        """
        return Region(self.page, root=self.root, root_extension=self._help)

    @property
    def label(self):
        """Get the formGroup label region
        """
        return Region(self.page, root=self.root, root_extension=self._label)


class TextInputMixin(object):
    """Adds form text input properties and methods to a FormGroup region
    """
    _text_input = (By.CLASS_NAME, 'Form-textInput')

    @property
    def spinny(self):
        return self.kwargs.get('spinny', False)

    @property
    def _text_input_region(self):
        return Region(self.page, root=self.root, root_extension=self._text_input)

    @property
    def text(self):
        self._text_input_region.wait_until_displayed()
        return self._text_input_region.root.get_attribute('value')

    @property
    def value(self):
        self._text_input_region.wait_until_displayed()
        return self._text_input_region.root.get_attribute('value')

    def clear(self):
        self._text_input_region.root.clear()

    def is_hidden(self):
        self._text_input_region.wait_until_displayed()
        return self._text_input_region.root.get_attribute('type') == 'password'

    def set_text(self, text):
        if self.text != text:
            self.clear()
            self._text_input_region.root.send_keys(text)
            if self.spinny:
                Spinny(self.page).wait_cycle()
