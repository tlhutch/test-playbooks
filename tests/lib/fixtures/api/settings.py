from awxkit.utils import logged_sleep
import fauxfactory
import pytest


@pytest.fixture(scope='class')
def update_setting_pg_class(request):
    """Helper fixture used in testing Tower settings."""
    def func(setting_pg, payload):
        """:param setting_pg: a settings page model.
        :param payload: a payload used for patching our setting page.

        Examples:
        (Pdb) update_setting_pg_class(api_settings_ui_pg, {'PENDO_TRACKING_STATE': 'detailed'})
        {"PENDO_TRACKING_STATE": "detailed"}
        (Pdb) update_setting_pg_class(api_settings_ui_pg, {'PENDO_TRACKING_STATE': 'off'})
        {"PENDO_TRACKING_STATE": "off"}
        """
        def teardown_settings():
            setting_pg.silent_delete()
            logged_sleep(1)  # Tower cache updates are a source of flakiness during settings tests.

        request.addfinalizer(teardown_settings)
        return setting_pg.patch(**payload)
    return func


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
        def teardown_settings():
            setting_pg.silent_delete()
            logged_sleep(1)  # Tower cache updates are a source of flakiness during settings tests.

        request.addfinalizer(teardown_settings)
        return setting_pg.patch(**payload)
    return func


@pytest.fixture(scope="function", params=["all", "auth", "azuread", "changed", "github_org", "github_team", "google", "jobs",
                                          "ldap", "radius", "saml", "system", "tacacsplus", "ui"])
def setting_pg(request):
    """Returns each of our nested /api/v2/settings/\\w+/ endpoints.

    FIXME: we do not include "github" here because tests will
    choke on pytest-github.
    """
    return request.getfixturevalue("api_settings_" + request.param + "_pg")


@pytest.fixture
def configure_auth_azuread(update_setting_pg, api_settings_azuread_pg):
    """Configure Tower with Azure Active Directory SSO."""
    v = fauxfactory.gen_utf8()
    payload = {k: v for k in ["SOCIAL_AUTH_AZUREAD_OAUTH2_KEY", "SOCIAL_AUTH_AZUREAD_OAUTH2_SECRET"]}
    update_setting_pg(api_settings_azuread_pg, payload)
    return api_settings_azuread_pg


@pytest.fixture
def configure_auth_github(update_setting_pg, api_settings_github_pg):
    """Configure Tower with GitHub SSO."""
    v = fauxfactory.gen_utf8()
    payload = {k: v for k in ["SOCIAL_AUTH_GITHUB_KEY", "SOCIAL_AUTH_GITHUB_SECRET"]}
    update_setting_pg(api_settings_github_pg, payload)
    return api_settings_github_pg


@pytest.fixture
def configure_auth_github_org(update_setting_pg, api_settings_github_org_pg):
    """Configure Tower with GitHub organization SSO."""
    v = fauxfactory.gen_utf8()
    payload = {k: v for k in ["SOCIAL_AUTH_GITHUB_ORG_KEY", "SOCIAL_AUTH_GITHUB_ORG_SECRET", "SOCIAL_AUTH_GITHUB_ORG_NAME"]}
    update_setting_pg(api_settings_github_org_pg, payload)
    return api_settings_github_org_pg


@pytest.fixture
def configure_auth_github_team(update_setting_pg, api_settings_github_team_pg):
    """Configure Tower with Github team SSO."""
    v = fauxfactory.gen_utf8()
    payload = {k: v for k in ["SOCIAL_AUTH_GITHUB_TEAM_KEY", "SOCIAL_AUTH_GITHUB_TEAM_SECRET", "SOCIAL_AUTH_GITHUB_TEAM_ID"]}
    update_setting_pg(api_settings_github_team_pg, payload)
    return api_settings_github_team_pg


@pytest.fixture
def configure_auth_google(update_setting_pg, api_settings_google_pg):
    """Configure Tower with Google SSO."""
    v = fauxfactory.gen_utf8()
    payload = {k: v for k in ["SOCIAL_AUTH_GOOGLE_OAUTH2_KEY", "SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET"]}
    update_setting_pg(api_settings_google_pg, payload)
    return api_settings_google_pg


@pytest.fixture(scope="function", params=["configure_auth_azuread",
                                          "configure_auth_github",
                                          "configure_auth_github_org",
                                          "configure_auth_github_team",
                                          "configure_auth_google"])
def configured_auth(request):
    return request.getfixturevalue(request.param)


@pytest.fixture
def install_custom_branding(update_setting_pg, api_settings_ui_pg):
    """Update our Tower login modal with a custom image and text field."""
    payload = dict(CUSTOM_LOGIN_INFO="Installed with fixture 'install_custom_branding'",
                   CUSTOM_LOGO="data:image/gif;base64,R0lGODlhAQABAIABAP///wAAACwAAAAAAQABAAACAkQBADs=")
    update_setting_pg(api_settings_ui_pg, payload)
