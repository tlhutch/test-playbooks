import pytest
import httplib
from common.api.schema import validate
from tests.api import Base_Api_Test
from unittestzero import Assert

@pytest.fixture(scope="module")
def api_users(request):
    '''
    Navigate the API and return a link to users
    '''
    api = request.getfuncargvalue('api')
    api_version = request.config.getvalue('api_version')

    if api_version == 'current_version':
        api_users = api.get('/api/').json().get('current_version')
    else:
        api_users = api.get('/api/').json().get('available_versions').get(api_version, None)

    Assert.not_none(api_users, "Unsupported api-version specified: %s" % api_version)

    return api.get(api_users).json().get('users')

class Test_Users(Base_Api_Test):
    @pytest.mark.nondestructive
    def test_unauthorized(self, api, api_users):
        # Validate Unauthorized access schema
        data = api.get(api_users).json()
        validate(data, '/users', 'unauthorized')

        # Validate Unauthorized access schema
        data = api.get(api_users + '/1').json()
        validate(data, '/users', 'unauthorized')

    @pytest.mark.nondestructive
    def test_authorized(self, api, api_users):
        # login
        api.login(self.testsetup.credentials['default']['username'],
                  self.testsetup.credentials['default']['password'])

        # Get list of available users
        data = api.get(api_users).json()

        # Validate schema
        validate(data, '/users', 'get')

    @pytest.mark.destructive
    def test_post(self, api, api_users):
        # login
        api.login(self.testsetup.credentials['default']['username'],
                  self.testsetup.credentials['default']['password'])

        # Create a new user
        payload = dict(username="dsmith",
                       first_name="Dave",
                       last_name="Smith",
                       email="dsmith@example.com",
                       is_superuser=False,
                       password=False,)
        r = api.post(api_users, payload)
        data = r.json()

        # support idempotency
        if r.status_code == httplib.BAD_REQUEST and \
           data.get('username','') == ['User with this Username already exists.']:
            Assert.equal(r.status_code, httplib.BAD_REQUEST)
            validate(data, '/users', 'duplicate')
            pytest.skip("User already exists")
        else:
            assert r.status_code == httplib.OK
            validate(data, '/users', 'post')

    @pytest.mark.destructive
    def test_get_one(self, api, api_users):
        # login
        api.login(self.testsetup.credentials['default']['username'],
                  self.testsetup.credentials['default']['password'])

        # Get and validate a single user
        data = api.get(api_users + '/1').json()
        validate(data, '/users', 'post')

    @pytest.mark.destructive
    def test_get_list(self, api, api_users):
        # login
        api.login(self.testsetup.credentials['default']['username'],
                  self.testsetup.credentials['default']['password'])

        # Get list of available users
        data = api.get(api_users).json()

        # Validate schema
        validate(data, '/users', 'get')

        num_orgs = len(data.get('results',[]))
        Assert.true(num_orgs > 0, 'Expecting >0 users (%s)' % num_orgs)

    @pytest.mark.destructive
    def test_add_user_to_org(self, api, api_base):
        # login
        api.login(self.testsetup.credentials['default']['username'],
                  self.testsetup.credentials['default']['password'])

        # Find desired org
        params = dict(icontains='Bender Products')
        data = api.get(api_base + '/organizations', params)
        validate(data, '/organizations', 'get')
        print data

        # Get list of available users
        #data = api.get(api_base + '/organizations/1/users/').json()

        # Validate schema

        #num_orgs = len(data.get('results',[]))
        #Assert.true(num_orgs > 0, 'Expecting >0 users (%s)' % num_orgs)
