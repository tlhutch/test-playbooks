import pytest


@pytest.fixture
def update_setting_pg(request):
    """Helper fixture used in testing Tower settings.
    """
    def func(api_setting_pg, payload):
        """
        :param api_setting_pg: the name of the fixture of our setting page fixture.
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
def enterprise_auth_settings_pgs(api_settings_ldap_pg, api_settings_radius_pg, api_settings_saml_pg):
    return [api_settings_radius_pg, api_settings_saml_pg, api_settings_ldap_pg]
