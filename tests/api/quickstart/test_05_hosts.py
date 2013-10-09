import pytest
import httplib
from common.api.schema import validate
from tests.api import Base_Api_Test
from unittestzero import Assert

@pytest.fixture(scope="module")
def api_hosts(request):
    '''
    Navigate the API and return a link to hosts
    '''
    api = request.getfuncargvalue('api')
    api_version = request.config.getvalue('api_version')

    if api_version == 'current_version':
        api_hosts = api.get('/api/').json().get('current_version')
    else:
        api_hosts = api.get('/api/').json().get('available_versions').get(api_version, None)

    Assert.not_none(api_hosts, "Unsupported api-version specified: %s" % api_version)

    return api.get(api_hosts).json().get('hosts')


class Test_Hosts(Base_Api_Test):
    @pytest.mark.nondestructive
    def test_unauthorized(self, api, api_hosts):
        r = api.get(api_hosts)
        assert r.status_code == httplib.UNAUTHORIZED
        validate(r.json(), '/hosts', 'unauthorized')

    @pytest.mark.nondestructive
    def test_authorized(self, api, api_hosts):
        # login
        api.login(self.testsetup.credentials['default']['username'],
                  self.testsetup.credentials['default']['password'])

        # Get list of available hosts
        data = api.get(api_hosts).json()

        # Validate schema
        validate(data, '/hosts', 'get')

    @pytest.mark.destructive
    def test_post(self, api, api_hosts, api_base):
        # login
        api.login(self.testsetup.credentials['default']['username'],
                  self.testsetup.credentials['default']['password'])

        # Find desired inventory
        params = dict(name__exact='Web Servers')
        r = api.get(api_base + 'inventories', params)
        data = r.json()
        assert data.get('results')[0]['name'] == 'Web Servers'
        inventory_id = data.get('results')[0].get('id',None)

        # Create a new inventory
        payload = dict(name='127.0.0.1',
                       description='Localhost',
                       inventory=inventory_id,
                       variables='')

        r = api.post(api_hosts, payload)
        data = r.json()

        # support idempotency
        if r.status_code == httplib.BAD_REQUEST:
            validate(data, '/hosts', 'duplicate')
            pytest.xfail("host already created")
        else:
            assert r.status_code == httplib.CREATED
            validate(data, '/hosts', 'post')

    @pytest.mark.destructive
    def test_add_host_to_group(self, api, api_hosts, api_base):
        # login
        api.login(self.testsetup.credentials['default']['username'],
                  self.testsetup.credentials['default']['password'])

        # Find desired host
        params = dict(name__exact='127.0.0.1')
        data = api.get(api_hosts, params).json()
        assert data.get('results')[0]['name'] == '127.0.0.1'
        host_id = data.get('results')[0].get('id',None)

        # Find desired group
        params = dict(name__exact='CMS Web')
        data = api.get(api_base + 'groups', params).json()
        assert data.get('results')[0]['name'] == 'CMS Web'
        group_hosts_link = data.get('results')[0].get('related',{}).get('hosts',None)

        # Add host to group
        payload = dict(id=host_id)
        r = api.post(group_hosts_link, payload)

        assert r.status_code == httplib.NO_CONTENT
        assert r.text == ''
