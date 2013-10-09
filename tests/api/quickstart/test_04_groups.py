import pytest
import httplib
from common.api.schema import validate
from tests.api import Base_Api_Test
from unittestzero import Assert

@pytest.fixture(scope="module")
def api_groups(request):
    '''
    Navigate the API and return a link to groups
    '''
    api = request.getfuncargvalue('api')
    api_version = request.config.getvalue('api_version')

    if api_version == 'current_version':
        api_groups = api.get('/api/').json().get('current_version')
    else:
        api_groups = api.get('/api/').json().get('available_versions').get(api_version, None)

    Assert.not_none(api_groups, "Unsupported api-version specified: %s" % api_version)

    return api.get(api_groups).json().get('groups')


class Test_Groups(Base_Api_Test):
    @pytest.mark.nondestructive
    def test_unauthorized(self, api, api_groups):
        r = api.get(api_groups)
        assert r.status_code == httplib.UNAUTHORIZED
        validate(r.json(), '/groups', 'unauthorized')

    @pytest.mark.nondestructive
    def test_authorized(self, api, api_groups):
        # login
        api.login(self.testsetup.credentials['default']['username'],
                  self.testsetup.credentials['default']['password'])

        # Get list of available groups
        data = api.get(api_groups).json()

        # Validate schema
        validate(data, '/groups', 'get')

    @pytest.mark.destructive
    def test_post(self, api, api_groups, api_base):
        # login
        api.login(self.testsetup.credentials['default']['username'],
                  self.testsetup.credentials['default']['password'])

        # Find desired org
        params = dict(name__exact='Web Servers')
        r = api.get(api_base + 'inventories', params)
        data = r.json()
        assert data.get('results')[0]['name'] == 'Web Servers'
        inventory_id = data.get('results')[0].get('id',None)

        # Create a new inventory
        payload = dict(name='CMS Web',
                       description='CMS web servers',
                       inventory=inventory_id,)
        r = api.post(api_groups, payload)
        data = r.json()

        # support idempotency
        if r.status_code == httplib.BAD_REQUEST:
            validate(data, '/groups', 'duplicate')
            pytest.xfail("Group already created")
        else:
            assert r.status_code == httplib.CREATED
            validate(data, '/groups', 'post')

