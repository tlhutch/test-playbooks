from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select

from common.ui.page import Region

from form_group import FormGroup


class SelectDropdown(FormGroup):

    _select = (By.CSS_SELECTOR, 'select')

    @property
    def select(self):
        return Select(self.find_element(*self._select))

    @property
    def options(self):
        return [e.text.lower() for e in self.select.options]

    def get_value(self):
        return self.select.first_selected_option.text.lower()

    def set_value(self, option):
        select = self.select
        if option.lower() != select.first_selected_option.text.lower():
            select.select_by_visible_text(option)


class Checkbox(FormGroup):

    _checkbox = (By.CSS_SELECTOR, "input[type='checkbox']")

    @property
    def options(self):
        return [True, False]

    @property
    def label(self):
        return self

    def get_value(self):
        return self.find_element(*self._checkbox).is_selected()

    def set_value(self, option):
        if option not in self.options:
            raise ValueError('Invalid selection')

        element = self.find_element(*self._checkbox)

        if option != element.is_selected():
            element.click()

    def wait_until_region_is_loaded(self):
        self.wait.until(lambda _: self.is_element_displayed(*self._checkbox))


class RadioButtons(FormGroup):

    _item_locator = (By.CSS_SELECTOR, "input[type='radio']")

    @property
    def options(self):
        elements = self.find_elements(self._item_locator)
        return [e.get_attribute('value') for e in elements]

    def get_value(self):
        for element in self.find_elements(*self._item_locator):
            if element.get_attribute('selected'):
                return element.get_attribute('value')
        raise NoSuchElementException

    def set_value(self, option):
        for element in self.find_elements(*self._item_locator):
            if option == element.get_attribute('value'):
                element.click()
                return
        raise NoSuchElementException


class TextInput(FormGroup):

    _text_input = (By.CLASS_NAME, 'Form-textInput')

    def clear(self):
        element = self.find_element(*self._text_input)
        element.clear()

    def get_value(self):
        element = self.find_element(*self._text_input)
        return element.get_attribute('value')

    def is_hidden(self):
        element = self.find_element(*self._text_input)
        return element.get_attribute('type') == 'password'

    def set_value(self, text):
        element = self.find_element(*self._text_input)
        if element.get_attribute('value') != text:
            element.clear()
            element.send_keys(text)

    def wait_until_region_is_loaded(self):
        self.wait.until(lambda _: self.is_element_displayed(*self._text_input))


class Password(TextInput):

    _password_button = (By.CLASS_NAME, 'Form-passwordButton')

    @property
    def password_button(self):
        return self.find_element(*self._password_button)

    def show(self):
        if self.is_hidden():
            self.password_button.click()

    def hide(self):
        if not self.is_hidden():
            self.password_button.click()


class TextArea(TextInput):

    _text_input = (By.TAG_NAME, 'textarea')


class Email(TextInput):
    pass


class CodeMirror(TextInput):
    pass


class FormSearch(TextInput):
    pass
