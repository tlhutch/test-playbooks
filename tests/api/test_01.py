import pytest
import jsonschema
import httplib
from tests.api import Base_Api_Test
from common.api import Connection

__get_schema__ = {
    '$schema': 'http://json-schema.org/draft-04/schema#',
    'type': 'object',
    'properties': {
        'available_versions': {
            'type': 'object',
        },
        'description': {
            'type': 'string',
        },
        'current_version': {
            'type': 'string',
        },
    },
    'required': ['available_versions', 'description', 'current_version'],
    'additionalProperties': False,
}

__options_schema__ = {
    '$schema': 'http://json-schema.org/draft-04/schema#',
    'type': 'object',
    'properties': {
        'name': {
            'type': 'string',
        },
        'description': {
            'type': 'string',
        },
        'renders': {
            'type': 'array',
            "items": {
                "type": "string"
            },
            "minItems": 1,
            "uniqueItems": True,
        },
        'parses': {
            'type': 'array',
            "items": {
                "type": "string"
            },
            "minItems": 1,
            "uniqueItems": True,
        },
    },
    'required': [ 'renders', 'parses' ],
    'additionalProperties': False,
}

@pytest.mark.nondestructive
class Test_Api_Basics(Base_Api_Test):
    def test_get_200(self, api):
        r = api.get('/api/')
        assert r.status_code == httplib.OK, "Unable to connect"

    def test_get_404(self, api, random_string):
        r = api.get('/api/%s/' % random_string)
        assert r.status_code == httplib.NOT_FOUND

    def test_get_schema(self, api):
        r = api.get('/api')
        assert r.status_code == httplib.OK
        jsonschema.validate(r.json(), __get_schema__)

    def test_options_schema(self, api):
        r = api.options('/api/')
        assert r.status_code == httplib.OK
        jsonschema.validate(r.json(), __options_schema__)

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

