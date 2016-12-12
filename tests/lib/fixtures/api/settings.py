import pytest
from towerkit.api.pages import Setting


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
def settings_pgs(api_settings_pg, testsetup):
    """Returns list of settings page objects for each setting posted under the main
    /api/v1/settings/ endpoint.

    Note: list of settings page objects returned will depend on your license.
    """
    endpoint_urls = [entry.json['url'] for entry in api_settings_pg.get().results]

    settings_pgs = []
    for url in endpoint_urls:
        setting_pg = Setting(testsetup, base_url=url)
        settings_pgs.append(setting_pg)

    return settings_pgs
