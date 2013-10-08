import pytest
import httplib
from common.api.schema import validate
from tests.api import Base_Api_Test
from unittestzero import Assert

@pytest.fixture(scope="module")
def api_organizations(request):
    '''
    Navigate the API and return a link to organizations
    '''
    api = request.getfuncargvalue('api')
    api_version = request.config.getvalue('api_version')

    if api_version == 'current_version':
        api_base = api.get('/api/').json().get('current_version')
    else:
        api_base = api.get('/api/').json().get('available_versions').get(api_version, None)

    Assert.not_none(api_base, "Unsupported api-version specified: %s" % api_version)

    return api.get(api_base).json().get('organizations')


class Test_Organizations(Base_Api_Test):
    @pytest.mark.nondestructive
    def test_unauthorized(self, api, api_organizations):
        # Validate Unauthorized access schema
        data = api.get(api_organizations).json()
        validate(data, '/organizations', 'unauthorized')

        # Validate Unauthorized access schema
        data = api.get(api_organizations + '/1').json()
        validate(data, '/organizations', 'unauthorized')

    @pytest.mark.nondestructive
    def test_authorized(self, api, api_organizations):
        # login
        api.login(self.testsetup.credentials['default']['username'],
                  self.testsetup.credentials['default']['password'])

        # Get list of available organizations
        data = api.get(api_organizations).json()

        # Validate schema
        validate(data, '/organizations', 'get')

    @pytest.mark.destructive
    def test_post(self, api, api_organizations):
        # login
        api.login(self.testsetup.credentials['default']['username'],
                  self.testsetup.credentials['default']['password'])

        # Create a new organization
        payload = dict(name="Bender Products",
                       description="Bender Products Ltd")
        r = api.post(api_organizations, payload)
        data = r.json()

        # support idempotency
        if r.status_code == httplib.BAD_REQUEST and \
            data.get('name','') == ['Organization with this Name already exists.']:
            Assert.equal(r.status_code, httplib.BAD_REQUEST)
            validate(data, '/organizations', 'duplicate')
            pytest.xfail("Organization already exists")
        else:
            assert r.status_code == httplib.CREATED
            validate(data, '/organizations', 'post')

    @pytest.mark.destructive
    def test_get_list(self, api, api_organizations):
        # login
        api.login(self.testsetup.credentials['default']['username'],
                  self.testsetup.credentials['default']['password'])

        # Get list of available organizations
        params = dict(name__iexact='Bender Products')
        data = api.get(api_organizations, params=params).json()

        # validate schema
        validate(data, '/organizations', 'get')

        num_orgs = len(data.get('results',[]))
        Assert.true(num_orgs > 0, 'Expecting >0 organizations (%s)' % num_orgs)
