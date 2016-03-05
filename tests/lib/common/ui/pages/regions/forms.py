from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select

from common.ui.pages.page import Region

from clickable import Clickable
from search import Search


class SelectDropDown(Region):

    @property
    def options(self):
        return [e.text for e in Select(self.root).options]

    @property
    def selected_option(self):
        return Select(self.root).first_selected_option.text

    def select(self, option):
        return Select(self.root).select_by_visible_text(option)


class Checkbox(Clickable):

    _root_extension = (By.CSS_SELECTOR, "input[type='checkbox']")

    @property
    def options(self):
        return [True, False]

    @property
    def selected_option(self):
        return self.root.is_selected()

    def select(self, option):
        if option not in self.options:
            raise ValueError('Invalid selection')

        if option != self.selected_option:
            self.click()

        return self


class PasswordButton(Clickable):

    _root_extension = (By.CLASS_NAME, 'Form-passwordButton')

    @property
    def options(self):
        return ['show', 'hide']

    @property
    def selected_option(self):
        return self._normalize_text(self.root.text)

    def select(self, option):
        option = self._normalize_text(option)

        if option not in self.options:
            raise ValueError('Invalid selection')

        if option != self.selected_option:
            self.click()

        return self


class RadioButtons(Region):

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


class Lookup(Region):

    _lookup_button = (By.CLASS_NAME, 'Form-lookupButton')

    @property
    def button(self):
        return Clickable(self.page, root=self.find_element(self._lookup_button))

    @property
    def text_input(self):
        return TextInput(self.page, root=self.root)

    @property
    def text(self):
        return self.text_input.text

    def set_text(self, text):
        return self.text_input.set_text(text)


class Password(Region):

    @property
    def text(self):
        return self.text_input.text

    @property
    def text_input(self):
        return TextInput(self.page, root=self.root)

    @property
    def show_input(self):
        return PasswordButton(self.page, root=self.root)

    def is_hidden(self):
        return self.text_input.is_hidden()

    def set_text(self, text):
        return self.text_input.set_text(text)


class TextInput(Region):

    _root_extension = (By.CLASS_NAME, 'Form-textInput')

    @property
    def text(self):
        return self.root.get_attribute('value')

    def is_hidden(self):
        return self.root.get_attribute('type') == 'password'

    def set_text(self, text):
        self.root.clear()
        self.root.send_keys(text)


class CodeMirror(TextInput):
    _root_extension = (By.CLASS_NAME, 'CodeMirror')


class FormSearch(Search):
    _root_extension = (By.CLASS_NAME, "List-searchWidget")


class FormPanel(Region):

    _root_locator = ((By.CLASS_NAME, 'Form-header'), (By.XPATH, '..'))

    _cancel = (By.CSS_SELECTOR, "[id$='_cancel_btn']")
    _exit = (By.CSS_SELECTOR, '.Form-exit')
    _save = (By.CSS_SELECTOR, "[id$='_save_btn']")
    _title = (By.CSS_SELECTOR, '.Form-title')

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
