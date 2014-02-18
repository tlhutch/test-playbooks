import pytest
import httplib
from tests.api import Base_Api_Test
from common.api.schema import validate

@pytest.mark.nondestructive
class Test_Api_Basics(Base_Api_Test):
    def test_get_200(self, api):
        r = api.get('/api/')
        assert r.status_code == httplib.OK, "Unable to connect"

    def test_get_404(self, api, random_string):
        r = api.get('/api/%s/' % random_string)
        assert r.status_code == httplib.NOT_FOUND

    def test_get_schema(self, api):
        r = api.get('/api/')
        assert r.status_code == httplib.OK
        validate(r.json(), '/api/', 'get')

    def test_options_schema(self, api):
        r = api.options('/api/')
        assert r.status_code == httplib.OK
        validate(r.json(), '/api/', 'options')

    def test_head_empty(self, api):
        r = api.head('/api/')
        assert r.text == '', 'Expected no output from HEAD request'
        assert r.status_code == httplib.OK

    def test_post_fail(self, api):
        r = api.post('/api/', {})
        assert r.status_code == httplib.METHOD_NOT_ALLOWED

    def test_patch_fail(self, api):
        r = api.patch('/api/', {})
        assert r.status_code == httplib.METHOD_NOT_ALLOWED

    def test_current_version(self, api):
        r = api.get('/api/')
        data = r.json()
        current_version = data.get('current_version')
        available_versions = data.get('available_versions')
        assert current_version in available_versions.values(), \
            "Unable to find current_version (%s) in list of " \
            "available_versions (%s)" % \
            (current_version, available_versions.values())

        # Does current_version path work?
        r = api.get(current_version)
        assert r.status_code == httplib.OK, 'Unexpected response code'
        assert isinstance(r.json(), dict), 'Unexpected response data'

    def test_description(self, api):
        r = api.get('/api/')
        data = r.json()
        description = data.get('description')
        assert description == 'Ansible Tower REST API'
