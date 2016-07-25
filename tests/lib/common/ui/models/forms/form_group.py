from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By

from common.ui.page import Region


class FormGroup(Region):
    # Subclasses of FormGroup must define a root locator that uniquely
    # identifies the Form-formGroup element associated with the widget
    # being modeled.
    _root_locator = None

    _label = (By.CSS_SELECTOR, 'label')
    _help = (By.CSS_SELECTOR, "a[id*='awp-']")
    _errors = (By.CLASS_NAME, 'error')

    options = None

    @property
    def name(self):
        return self.kwargs.get(name)

    @property
    def required(self):
        return self.kwargs.get('required', False)

    @property
    def help(self):
        """Get the formGroup help popover region
        """
        return self.find_element(*self._help)

    @property
    def label(self):
        """Get the formGroup label region
        """
        return self.find_element(*self._label)

    @property
    def errors(self):
        return [e.text for e in self.find_elements(*self._errors) if e.text]

    def is_displayed(self):
        return self.root.is_displayed()
