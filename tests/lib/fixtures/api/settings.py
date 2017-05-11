import pytest


@pytest.fixture
def update_setting_pg(request):
    """Helper fixture used in testing Tower settings."""
    def func(setting_pg, payload):
        """:param setting_pg: a settings page model.
        :param payload: a payload used for patching our setting page.

        Examples:
        (Pdb) update_setting_pg(api_settings_ui_pg, {'PENDO_TRACKING_STATE': 'detailed'})
        {"PENDO_TRACKING_STATE": "detailed"}
        (Pdb) update_setting_pg(api_settings_ui_pg, {'PENDO_TRACKING_STATE': 'off'})
        {"PENDO_TRACKING_STATE": "off"}
        """
        request.addfinalizer(setting_pg.delete)
        return setting_pg.patch(**payload)
    return func


@pytest.fixture
def oauth_settings_pgs(api_settings_github_pg, api_settings_github_org_pg, api_settings_github_team_pg, api_settings_google_pg,
                       api_settings_azuread_pg):
    """Returns a list of all of our oauth settings pages. Fixture current with Tower-3.1.1."""
    return [api_settings_github_pg, api_settings_github_org_pg, api_settings_github_team_pg, api_settings_google_pg,
            api_settings_azuread_pg]


@pytest.fixture(scope="function", params=["all", "auth", "azuread", "changed", "github_org", "github_team", "google", "jobs",
                                          "ldap", "radius", "saml", "system", "tacacsplus", "ui"])
def setting_pg(request):
    """Returns each of our nested /api/v1/settings/\w+/ endpoints.

    FIXME: we do not include "github" here because tests will
    choke on pytest-github.
    """
    return request.getfuncargvalue("api_settings_" + request.param + "_pg")


@pytest.fixture
def install_custom_branding(update_setting_pg, api_settings_ui_pg):
    """Update our Tower login modal with a custom image and text field."""
    payload = dict(CUSTOM_LOGIN_INFO="Installed with fixture 'install_custom_branding'",
                   CUSTOM_LOGO="data:image/gif;base64,R0lGODlhAQABAIABAP///wAAACwAAAAAAQABAAACAkQBADs=")
    update_setting_pg(api_settings_ui_pg, payload)
