from qe.api import resources
import base


class Setting(base.Base):
    pass

base.register_page([resources.v1_setting,
                    resources.v1_settings_all,
                    resources.v1_settings_authentication,
                    resources.v1_settings_changed,
                    resources.v1_settings_github,
                    resources.v1_settings_github_org,
                    resources.v1_settings_github_team,
                    resources.v1_settings_google_oauth2,
                    resources.v1_settings_jobs,
                    resources.v1_settings_ldap,
                    resources.v1_settings_radius,
                    resources.v1_settings_saml,
                    resources.v1_settings_system,
                    resources.v1_settings_ui,
                    resources.v1_settings_user,
                    resources.v1_settings_user_defaults], Setting)


class Settings(base.BaseList, Setting):
    def get_endpoint(self, endpoint):
        """Helper method used to navigate to a specific settings endpoint.
        (Pdb) settings_pg.get_endpoint('all')
        """
        base_url = '{0}{1}/'.format(self.base_url, endpoint)
        return self.walk(base_url)

base.register_page(resources.v1_settings, Settings)
