import pytest
import httplib
import requests
from tests.api import Base_Api_Test


@pytest.mark.api
@pytest.mark.ha
@pytest.mark.skip_selenium
@pytest.mark.destructive
class Test_HA(Base_Api_Test):
    pytestmark = pytest.mark.usefixtures('authtoken', 'install_enterprise_license')

    @pytest.mark.ansible(host_pattern='primary')
    def test_primary_ping_endpoint(self, api_ping_pg, ansible_module):
        '''
        Verify /api/v1/ping on the HA primary
        '''
        api_ping_pg.get()
        assert api_ping_pg.ha
        assert api_ping_pg.role == 'primary'

    @pytest.mark.ansible(host_pattern='primary')
    def test_secondary_ping_endpoint(self, api_ping_pg, api_ping_url, ansible_module):
        '''
        Verify /api/v1/ping on the HA primary
        '''

        api_ping_pg.get()
        secondaries = api_ping_pg.instances['secondaries']
        import json
        print json.dumps(api_ping_pg.json, indent=2)
        assert len(secondaries) > 0

        for secondary in secondaries:
            result = requests.get("https://" + secondary + api_ping_url, verify=False)
            assert result.status_code == httplib.OK

            # assert that http traffic was *NOT* redirected
            assert len(result.history) == 0, "No http redirects were expected"
            json = result.json()

            # assert various JSON response attributes
            assert json['ha']
            assert json['role'] == 'secondary'
            assert len(json['instances']['secondaries']) == len(api_ping_pg.instances['secondaries'])

    @pytest.mark.ansible(host_pattern='primary')
    def test_secondary_endpoint_redirect(self, api_ping_pg, api_v1_url, ansible_module):
        '''
        Verify secondary endpoints redirect to the primary
        '''

        api_ping_pg.get()
        primary = api_ping_pg.instances['primary']
        secondaries = api_ping_pg.instances['secondaries']
        assert len(secondaries) > 0
        assert primary not in secondaries

        # Assert that each secondary redirects traffic to the primary
        for secondary in secondaries:
            result = requests.get("https://" + secondary + api_v1_url, verify=False)
            assert result.status_code == httplib.OK

            # assert that HTTP traffic *was* redirected
            assert len(result.history) == 1, "HTTP redirects where expected"
            assert result.history[0].status_code == httplib.FOUND
            assert primary in result.history[0].headers['location']

#    @pytest.mark.ansible(host_pattern='secondary')
#    def test_secondary_promotion(self, ansible_module):
#        contacted = ansible_module.ping()
#        import json
#        print json.dumps(contacted)
#        assert False
