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

class Test_Users(Base_Api_Test):
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
    def test_post(self, api, api_inventories):
        # login
        api.login(self.testsetup.credentials['default']['username'],
                  self.testsetup.credentials['default']['password'])

        # Create a new user
        payload = dict(name='',
                       description='',
                       organization='',)
        r = api.post(api_inventories, payload)
        data = r.json()

        # support idempotency
        assert r.status_code == httplib.CREATED
        validate(data, '/inventories', 'post')

    @pytest.mark.destructive
    def test_get_list(self, api, api_inventories):
        # login
        api.login(self.testsetup.credentials['default']['username'],
                  self.testsetup.credentials['default']['password'])

        # Get list of available inventories
        params = dict(username__exact='dsmith')
        data = api.get(api_inventories, params=params).json()

        # Validate schema
        validate(data, '/inventories', 'get')

        num_inventories = len(data.get('results',[]))
        Assert.true(num_inventories > 0, 'Expecting >0 inventories (%s)' % num_inventories)

    @pytest.mark.destructive
    def test_add_user_to_org(self, api, api_base):
        # login
        api.login(self.testsetup.credentials['default']['username'],
                  self.testsetup.credentials['default']['password'])

        # Find the desired user
        params = dict(username__icontains='dsmith')
        r = api.get(api_base + 'inventories', params)
        data = r.json()
        assert data.get('results')[0]['username'] == 'dsmith'
        user_id = data.get('results')[0]['id']

        # Find desired org
        params = dict(name__icontains='Bender Products')
        r = api.get(api_base + 'organizations', params)
        data = r.json()
        assert data.get('results')[0]['name'] == 'Bender Products'
        org_inventories_link = data.get('results')[0].get('related',{}).get('inventories','')

        # Add user to org
        payload = dict(id=user_id)
        r = api.post(org_inventories_link, payload)

        assert r.status_code == httplib.NO_CONTENT
        assert r.text == ''
