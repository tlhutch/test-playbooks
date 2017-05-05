import pytest
import fauxfactory


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


@pytest.fixture(scope="function", params=["api_settings_azuread_pg",
                                          "api_settings_github_pg",
                                          "api_settings_github_org_pg",
                                          "api_settings_github_team_pg",
                                          "api_settings_google_pg"])
def sso_settings_pg(request):
    """Returns each of our SSO settings pages."""
    return request.getfuncargvalue(request.param)


@pytest.fixture
def configure_auth(update_setting_pg):
    """Configure an authentication service with dummy settings."""
    def func(settings_pg):
        v = fauxfactory.gen_utf8()
        if settings_pg.endpoint.endswith("azuread-oauth2/"):
            payload = {k: v for k in ["SOCIAL_AUTH_AZUREAD_OAUTH2_KEY", "SOCIAL_AUTH_AZUREAD_OAUTH2_SECRET"]}
        elif settings_pg.endpoint.endswith("github/"):
            payload = {k: v for k in ["SOCIAL_AUTH_GITHUB_KEY", "SOCIAL_AUTH_GITHUB_SECRET"]}
        elif settings_pg.endpoint.endswith("github-org/"):
            payload = {k:v for k in ["SOCIAL_AUTH_GITHUB_ORG_KEY", "SOCIAL_AUTH_GITHUB_ORG_SECRET", "SOCIAL_AUTH_GITHUB_ORG_NAME"]}
        elif settings_pg.endpoint.endswith("github-team/"):
            payload = {k:v for k in ["SOCIAL_AUTH_GITHUB_TEAM_KEY", "SOCIAL_AUTH_GITHUB_TEAM_SECRET", "SOCIAL_AUTH_GITHUB_TEAM_ID"]}
        elif settings_pg.endpoint.endswith("google-oauth2/"):
            payload = {k:v for k in ["SOCIAL_AUTH_GOOGLE_OAUTH2_KEY", "SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET"]}
        update_setting_pg(settings_pg, payload)
    return func


@pytest.fixture(scope="function", params=["all", "auth", "azuread", "changed", "github_org", "github_team", "google", "jobs",
                                          "ldap", "radius", "saml", "system", "ui"])
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
