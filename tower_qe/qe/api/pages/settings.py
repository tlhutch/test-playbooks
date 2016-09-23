from qe.api import resources
import base


class Settings_Page(base.Base):
    def get_setting(self, setting):
        """Helper method used to navigate to a specific settings page.
        """
        base_url = '/api/v1/settings/%s/' % setting
        return self.walk(base_url)

base.register_page(resources.v1_settings, Settings_Page)
