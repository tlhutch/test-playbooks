from qe.api import resources
import base


class Setting_Page(base.Base):
    pass

base.register_page(resources.v1_setting, Setting_Page)


class Settings_Page(base.BaseList, Setting_Page):
    def get_endpoint(self, endpoint):
        """Helper method used to navigate to a specific settings endpoint.
        (Pdb) settings_pg.get_endpoint('all')
        """
        base_url = '{0}{1}/'.format(self.base_url, endpoint)
        return self.walk(base_url)

base.register_page(resources.v1_settings, Settings_Page)
