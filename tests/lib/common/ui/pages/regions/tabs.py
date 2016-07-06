from clickable import Clickable


class PanelButton(Clickable):

    _bg_enabled = (
        'rgba(215, 215, 215, 1)', 'rgb(215, 215, 215)',
        'rgba(132, 137, 146, 1)', 'rgb(132, 137, 146)')

    _bg_disabled = (
        'rgba(255, 255, 255, 1)', 'rgb(255, 255, 255)',
        'rgba(250, 250, 250, 1)', 'rgb(250, 250, 250)')

    @property
    def background_color(self):
        return self.root.value_of_css_property('background-color')

    def is_enabled(self):
        return self.background_color in self._bg_enabled

    def is_disabled(self):
        return self.background_color in self._bg_disabled

    def wait_until_enabled(self):
        self.wait.until(lambda _: self.is_enabled())

    def wait_until_disabled(self):
        self.wait.until(lambda _: self.is_disabled())


class PanelToggleTab(PanelButton):

    def enable(self):
        if self.is_disabled():
            self.click()
            self.wait_until_enabled()

        return self.page

    def disable(self):
        if self.is_enabled():
            self.click()
            self.wait_until_disabled()

        return self.page


class PanelTab(PanelButton):

    def enable(self):
        if self.is_disabled():
            self.click()
            self.wait_until_enabled()

        return self.page

    def click(self):
        super(PanelTab, self).click()
        self.wait_until_enabled()
        return self.page
