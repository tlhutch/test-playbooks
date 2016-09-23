from qe.api import resources
import base


class Settings_Page(base.Base):
    def get_endpoint(self, endpoint):
        """Helper method used to navigate to a specific settings endpoint.
        (Pdb) settings_pg.get_endpoint('all')
        """
        base_url = '/api/v1/settings/%s/' % endpoint
        return self.walk(base_url)

base.register_page([resources.v1_settings,
                    resources.v1_settings_ui], Settings_Page)
