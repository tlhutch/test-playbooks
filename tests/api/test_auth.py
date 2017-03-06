import pytest
from tests.api import Base_Api_Test


OAUTH_SUBSTRINGS = ['KEY', 'SECRET', 'TEAM_ID', 'ORG_NAME']


def find_settings(setting_pg, substrings):
    """Find settings given a list of matching substrings.
    :param setting_pg: an API setting page model.
    :param substrings: a list of matching substrings.

    >>> find_settings(api_settings_github_pg, ['CALLBACK'])
    [u'SOCIAL_AUTH_GITHUB_CALLBACK_URL']

    Endpoint JSON for reference:
    {
        "SOCIAL_AUTH_GITHUB_CALLBACK_URL": "https://ec2-54-80-169-208.compute-1.amazonaws.com/sso/complete/github/",
        "SOCIAL_AUTH_GITHUB_KEY": "test",
        "SOCIAL_AUTH_GITHUB_SECRET": "$encrypted$",
        "SOCIAL_AUTH_GITHUB_ORGANIZATION_MAP": null,
        "SOCIAL_AUTH_GITHUB_TEAM_MAP": null
    }
    """
    keys = []
    for key in setting_pg.json:
        if any(substring in key for substring in substrings):
            keys.append(key)
    return keys


@pytest.fixture
def configure_oauth(update_setting_pg):
    """Configure an oauth setting_pg with dummy settings."""
    def func(setting_pg):
        keys = find_settings(setting_pg, OAUTH_SUBSTRINGS)
        payload = {key: "test" for key in keys}
        update_setting_pg(setting_pg, payload)
    return func


@pytest.fixture
def find_configured_settings(oauth_settings_pgs):
    def func():
        changed = 0
        for setting_pg in oauth_settings_pgs:
            if "test" in setting_pg.json.values():
                changed += 1
        return changed
    return func


@pytest.mark.api
@pytest.mark.destructive
@pytest.mark.skip_selenium
class Test_Auth(Base_Api_Test):

    pytestmark = pytest.mark.usefixtures('authtoken', 'install_enterprise_license_unlimited')

    def test_default_entries(self, v1):
        """By default /api/v1/auth/ should not contain any entries."""
        auth = v1.walk('/api/v1/auth/')
        assert auth.json == {}, \
            "Unexpected value for /api/v1/auth/."

    def test_updated_entries(self, v1, oauth_settings_pgs, configure_oauth, find_configured_settings):
        """Update oauth settings pages sequentially and verify that /api/v1/auth/ updates appropriately."""
        for setting_pg in oauth_settings_pgs:
            configure_oauth(setting_pg)
            auth = v1.walk('/api/v1/auth/')
            # assert that we have the right number of entries returned
            assert len(auth.json) == find_configured_settings(), \
                "Expected to have {0} result[s] under /api/v1/auth/.".format(find_configured_settings())
            # assert expected entry found
            endpoint_name = setting_pg.base_url.replace('/api/v1/settings/', '').strip('/')
            assert endpoint_name in auth.json, \
                "Unexpected result[s] found with /api/v1/auth/. Expected '{0}.'".format(endpoint_name)
            # assert entry contains expected contents
            assert auth.json[endpoint_name]["login_url"] == "/sso/login/" + endpoint_name + "/", \
                "Unexpected value for login_url."
            callback_setting = find_settings(setting_pg, ['CALLBACK']).pop()
            assert auth.json[endpoint_name]["complete_url"] == setting_pg.json[callback_setting]

    def test_reset_entries(self, v1):
        """Our /api/v1/auth/ endpoint should not contain any entries after settings reset."""
        auth = v1.walk('/api/v1/auth/')
        assert auth.json == {}, \
            "Unexpected value for /api/v1/auth/."
