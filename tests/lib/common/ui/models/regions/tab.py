from common.ui.page import Region

__all__ = ['Tab', 'ToggleTab']


class BaseTab(Region):

    _bg_enabled = (
        'rgba(215, 215, 215, 1)', 'rgb(215, 215, 215)',  #  D7D7D7
        'rgba(132, 137, 146, 1)', 'rgb(132, 137, 146)')  #  848992

    _bg_disabled = (
        'rgba(255, 255, 255, 1)', 'rgb(255, 255, 255)',  #  FFFFFF
        'rgba(250, 250, 250, 1)', 'rgb(250, 250, 250)')  #  FAFAFA

    @property
    def background_color(self):
        return self.root.value_of_css_property('background-color')

    def is_enabled(self):
        return self.background_color in self._bg_enabled

    def is_disabled(self):
        return self.background_color in self._bg_disabled

    def wait_until_loaded(self):
        if self._root is None and self._root_locator is not None:
            self.wait.until(lambda _: self.page.is_element_displayed(*self._root_locator))


class Tab(BaseTab):

    def enable(self):
        if self.is_disabled():
            self.root.click()
            self.wait.until(lambda _: self.is_enabled())


class ToggleTab(BaseTab):

    def enable(self):
        if self.is_disabled():
            self.root.click()
            self.wait.until(lambda _: self.is_enabled())

    def disable(self):
        if self.is_enabled():
            self.root.click()
            self.wait.until(lambda _: self.is_disabled())
