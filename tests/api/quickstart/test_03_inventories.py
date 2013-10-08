import pytest
import httplib
from common.api.schema import validate
from tests.api import Base_Api_Test
from unittestzero import Assert

@pytest.fixture(scope="module")
def api_inventories(request):
    '''
    Navigate the API and return a link to inventories
    '''
    api = request.getfuncargvalue('api')
    api_version = request.config.getvalue('api_version')

    if api_version == 'current_version':
        api_inventories = api.get('/api/').json().get('current_version')
    else:
        api_inventories = api.get('/api/').json().get('available_versions').get(api_version, None)

    Assert.not_none(api_inventories, "Unsupported api-version specified: %s" % api_version)

    return api.get(api_inventories).json().get('inventory')

class Test_Inventories(Base_Api_Test):
    @pytest.mark.nondestructive
    def test_unauthorized(self, api, api_inventories):
        r = api.get(api_inventories)
        assert r.status_code == httplib.UNAUTHORIZED
        validate(r.json(), '/inventories', 'unauthorized')

    @pytest.mark.nondestructive
    def test_authorized(self, api, api_inventories):
        # login
        api.login(self.testsetup.credentials['default']['username'],
                  self.testsetup.credentials['default']['password'])

        # Get list of available inventories
        data = api.get(api_inventories).json()

        # Validate schema
        validate(data, '/inventories', 'get')

    @pytest.mark.destructive
    def test_post(self, api, api_inventories, api_base):
        # login
        api.login(self.testsetup.credentials['default']['username'],
                  self.testsetup.credentials['default']['password'])

        # Find desired org
        params = dict(name__icontains='Bender Products')
        r = api.get(api_base + 'organizations', params)
        data = r.json()
        assert data.get('results')[0]['name'] == 'Bender Products'
        org_id = data.get('results')[0].get('id',None)

        # Create a new inventory
        payload = dict(name='Web Servers',
                       description='Web server hosts',
                       organization=org_id,)
        r = api.post(api_inventories, payload)
        data = r.json()

        # support idempotency
        if r.status_code == httplib.BAD_REQUEST:
            validate(data, '/inventories', 'duplicate')
            pytest.xfail("inventory already created")
        else:
            assert r.status_code == httplib.CREATED
            validate(data, '/inventories', 'post')
