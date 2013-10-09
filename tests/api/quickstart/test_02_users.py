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

@pytest.fixture(scope="module")
def api_credentials(request):
    '''
    Navigate the API and return a link to users
    '''
    api = request.getfuncargvalue('api')
    api_version = request.config.getvalue('api_version')

    if api_version == 'current_version':
        api_credentials = api.get('/api/').json().get('current_version')
    else:
        api_credentials = api.get('/api/').json().get('available_versions').get(api_version, None)

    Assert.not_none(api_credentials, "Unsupported api-version specified: %s" % api_version)

    return api.get(api_credentials).json().get('credentials')


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
            pytest.xfail("User already exists")
        else:
            assert r.status_code == httplib.CREATED
            validate(data, '/users', 'post')

    @pytest.mark.destructive
    def test_get_list(self, api, api_users):
        # login
        api.login(self.testsetup.credentials['default']['username'],
                  self.testsetup.credentials['default']['password'])

        # Get list of available users
        params = dict(username__exact='dsmith')
        data = api.get(api_users, params=params).json()

        # Validate schema
        validate(data, '/users', 'get')

        num_users = len(data.get('results',[]))
        Assert.true(num_users > 0, 'Expecting >0 users (%s)' % num_users)

    @pytest.mark.destructive
    def test_add_user_to_org(self, api, api_users, api_base):
        # login
        api.login(self.testsetup.credentials['default']['username'],
                  self.testsetup.credentials['default']['password'])

        # Find the desired user
        params = dict(username__icontains='dsmith')
        r = api.get(api_users, params)
        data = r.json()
        assert data.get('results')[0]['username'] == 'dsmith'
        user_id = data.get('results')[0]['id']

        # Find desired org
        params = dict(name__icontains='Bender Products')
        r = api.get(api_base + 'organizations', params)
        data = r.json()
        assert data.get('results')[0]['name'] == 'Bender Products'
        org_users_link = data.get('results')[0].get('related',{}).get('users','')

        # Add user to org
        payload = dict(id=user_id)
        r = api.post(org_users_link, payload)

        assert r.status_code == httplib.NO_CONTENT
        assert r.text == ''

    @pytest.mark.destructive
    def test_create_credential(self, api, api_users, api_credentials):
        # login
        api.login(self.testsetup.credentials['default']['username'],
                  self.testsetup.credentials['default']['password'])

        # Find the desired user
        params = dict(username__icontains='dsmith')
        data = api.get(api_users, params).json()
        assert data.get('results')[0]['username'] == 'dsmith'
        user_id = data.get('results')[0].get('id')
        user_credential_link = data.get('results')[0].get('related', {}).get('credentials')

        # Add user to org
        payload = dict(name='root (ask)',
                       description='user:root, password:ask',
                       ssh_username='root',
                       ssh_password='ASK',
                       user=user_id)
        r = api.post(user_credential_link, payload)

        assert r.status_code == httplib.CREATED
        validate(data, '/users', 'get')
