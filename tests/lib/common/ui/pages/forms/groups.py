from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select

from common.ui.pages.page import Region
from common.ui.pages.regions.clickable import Clickable

from form_group import FormGroup, TextInputMixin


class SelectDropDown(FormGroup):

    _select = (By.CSS_SELECTOR, 'select')

    @property
    def options(self):
        select_model = Select(self.find_element(self._select))
        return [e.text for e in select_model.options]

    @property
    def selected_option(self):
        select_model = Select(self.find_element(self._select))
        return select_model.first_selected_option.text

    def select(self, option):
        select_model = Select(self.find_element(self._select))
        return select_model.select_by_visible_text(option)


class Checkbox(FormGroup):

    _checkbox = (By.CSS_SELECTOR, "input[type='checkbox']")

    @property
    def options(self):
        return [True, False]

    @property
    def label(self):
        """Get the formGroup label region
        """
        return Region(self.page, root=self.root)

    @property
    def selected_option(self):

        checkbox = Clickable(
            self.page,
            root=self.root,
            root_extension=self._checkbox)

        checkbox.wait_until_displayed()

        return checkbox.root.is_selected()

    def select(self, option):

        if option not in self.options:
            raise ValueError('Invalid selection')

        checkbox = Clickable(
            self.page,
            root=self.root,
            root_extension=self._checkbox)

        checkbox.wait_until_displayed()

        if option != checkbox.root.is_selected():
            checkbox.click()

        return self


class RadioButtons(FormGroup):

    _item_locator = (By.CSS_SELECTOR, "input[type='radio']")

    @property
    def options(self):
        elements = self.find_elements(self._item_locator)
        return [e.get_attribute('value') for e in elements]

    @property
    def selected_option(self):
        selected = self.lookup_element(self._item_locator, selected='true')
        return selected.get_attribute('value')

    def select(self, option):
        self.lookup_element(self._item_locator, value=option).click()


class Password(TextInputMixin, FormGroup):

    _password_button = (By.CLASS_NAME, 'Form-passwordButton')

    @property
    def options(self):
        return ['show', 'hide']

    @property
    def selected_option(self):
        password_button = Clickable(
            self.page,
            root=self.root,
            root_extension=self._password_button)

        return password_button.normalized_text

    def select(self, option):

        if option not in self.options:
            raise ValueError('Invalid selection')

        password_button = Clickable(
            self.page,
            root=self.root,
            root_extension=self._password_button)

        if option != password_button.normalized_text:
            password_button.click()

        return self


class TextInput(TextInputMixin, FormGroup):
    pass


class CodeMirror(TextInputMixin, FormGroup):
    pass


class FormSearch(TextInputMixin, FormGroup):
    pass
