import pytest


@pytest.fixture
def update_setting_pg(request):
    """Helper fixture used in testing Tower settings."""
    def func(setting_pg, payload):
        """:param setting_pg: a settings page model.
        :param payload: a payload used for patching our setting page.

        Examples:
        (Pdb) update_setting_pg('api_settings_ui_pg', {'PENDO_TRACKING_STATE': 'detailed'})
        {"PENDO_TRACKING_STATE": "detailed"}
        (Pdb) update_setting_pg('api_settings_ui_pg', {'PENDO_TRACKING_STATE': 'off'})
        {"PENDO_TRACKING_STATE": "off"}
        """
        request.addfinalizer(setting_pg.delete)
        return setting_pg.patch(**payload)
    return func


@pytest.fixture
def oauth_settings_pgs(v1):
    """Returns a list of all of our oauth settings_pgs."""
    endpoints = ['github', 'github-team', 'github-org', 'google-oauth2', 'azuread-oauth2']
    return [v1.settings.get().get_endpoint(endpoint) for endpoint in endpoints]


@pytest.fixture
def enterprise_auth_settings_pgs(v1):
    """Returns a list of all of our enterprise auth endpoints. Enterprise auth includes: LDAP,
    SAML, and RADIUS.
    """
    endpoints = ['radius', 'saml', 'ldap']
    return [v1.settings.get().get_endpoint(endpoint) for endpoint in endpoints]


@pytest.fixture(scope="function", params=['all', 'authentication', 'azuread-oauth2', 'changed', 'github-org',
                                          'github-team', 'google-oauth2', 'jobs', 'ldap', 'logging', 'radius',
                                          'saml', 'system', 'ui'])
def setting_pg(request, v1):
    """Returns each of our nested /api/v1/settings/ endpoints.

    FIXME: we do not include "github" here because tests will
    choke on pytest-github.
    """
    return v1.settings.get().get_endpoint(request.param)
