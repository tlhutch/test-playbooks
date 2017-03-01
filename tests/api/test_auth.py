import pytest
from tests.api import Base_Api_Test


OAUTH_SUBSTRINGS = ['KEY', 'SECRET', 'TEAM_ID', 'ORG_NAME']


def find_settings(endpoint, substrings):
    """Find settings given a list of matching substrings.
    :param endpoint: an API settings page model.
    :param substrings: a list of matching substrings.

    >>> find_settings(api_settings_github_pg, ['CALLBACK'])
    [u'SOCIAL_AUTH_GITHUB_CALLBACK_URL']

    /api/v1/github/ is for reference:
    {
        "SOCIAL_AUTH_GITHUB_CALLBACK_URL": "https://ec2-54-80-169-208.compute-1.amazonaws.com/sso/complete/github/",
        "SOCIAL_AUTH_GITHUB_KEY": "test",
        "SOCIAL_AUTH_GITHUB_SECRET": "$encrypted$",
        "SOCIAL_AUTH_GITHUB_ORGANIZATION_MAP": null,
        "SOCIAL_AUTH_GITHUB_TEAM_MAP": null
    }
    """
    keys = []
    for key in endpoint.json:
        if any(substring in key for substring in substrings):
            keys.append(key)
    return keys


# add teardown
# update update_settings_pg fixture to accept base_urls
def configure_oauth(endpoint):
    # update endpoint
    keys = find_settings(endpoint, OAUTH_SUBSTRINGS)
    payload = {key: "test" for key in keys}
    endpoint.patch(**payload)


@pytest.mark.api
@pytest.mark.destructive
@pytest.mark.skip_selenium
class Test_Auth(Base_Api_Test):

    pytestmark = pytest.mark.usefixtures('authtoken', 'install_enterprise_license_unlimited')

    def test_default(self, v1):
        """By default /api/v1/auth/ should not contain any entries."""
        auth = v1.walk('/api/v1/auth/')
        assert auth.json == {}, \
            "Unexpected value for /api/v1/auth/."

    def test_updated_entries(self, v1, oauth_settings_pgs):
        """Update our oauth settings pages sequentially. Check that:
        * /api/v1/auth/ updates to shows our new entry.
        * Entry contents are as expected.
        """
        for endpoint in oauth_settings_pgs:
            configure_oauth(endpoint)
            auth = v1.walk('/api/v1/auth/')
            # assert that we have one entry returned
            assert len(auth.json) == 1, \
                "Expected to have one entry under /api/v1/auth/."
            # assert entry contains expected contents
            endpoint_name = endpoint.base_url.replace('/api/v1/settings/', '').strip('/')
            assert endpoint_name in auth.json, \
                "Unexpected entry found under /api/v1/auth/. Expected {0}.".format(endpoint_name)
            assert auth.json[endpoint_name]["login_url"] == "/sso/login/" + endpoint_name + "/", \
                "Unexpected value for login_url."
            callback_setting = find_settings(endpoint, ['CALLBACK']).pop()
            assert auth.json[endpoint_name]["complete_url"] == endpoint.json[callback_setting]
