import pytest


@pytest.fixture
def update_setting_pg(request):
    """Helper fixture used in testing Tower settings."""
    def func(api_setting_pg, payload):
        """:param api_setting_pg: the name of the fixture of our setting page fixture.
        :param payload: a payload used for patching our setting page.

        Examples:
        (Pdb) update_setting_pg('api_settings_ui_pg', {'PENDO_TRACKING_STATE': 'detailed'})
        {"PENDO_TRACKING_STATE": "detailed"}
        (Pdb) update_setting_pg('api_settings_ui_pg', {'PENDO_TRACKING_STATE': 'off'})
        {"PENDO_TRACKING_STATE": "off"}
        """
        setting_pg = request.getfuncargvalue(api_setting_pg)
        request.addfinalizer(setting_pg.delete)
        return setting_pg.patch(**payload)
    return func


@pytest.fixture
def oauth_settings_pgs(v1):
    """Returns a list of all of our oauth settings_pgs."""
    endpoints = ['github', 'github-team', 'github-org', 'google-oauth2', 'azuread-oauth2']
    return [v1.settings.get().get_endpoint(endpoint) for endpoint in endpoints]


@pytest.fixture
def enterprise_auth_settings_pgs(api_settings_ldap_pg, api_settings_radius_pg, api_settings_saml_pg):
    """Returns a list of all of our enterprise auth settings_pgs. Enterprise auth includes: LDAP,
    SAML, and RADIUS.
    """
    return [api_settings_radius_pg, api_settings_saml_pg, api_settings_ldap_pg]


@pytest.fixture(scope="function", params=["all", "auth", "azuread", "changed", "github_org", "github_team", "google", "jobs",
                                          "ldap", "radius", "saml", "system", "ui"])
def setting_pg(request):
    """Returns each of our nested /api/v1/settings/ endpoints.

    FIXME: we do not include "github" here because tests will
    choke on pytest-github.
    """
    return request.getfuncargvalue("api_settings_" + request.param + "_pg")
