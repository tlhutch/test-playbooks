import pytest
import jsonschema
from tests.api import Base_Api_Test

# {u'available_versions': {u'v1': u'/api/v1/'}, u'description': u'AWX REST API', u'current_version': u'/api/v1/'}
__schema__ = {
    '$schema': 'http://json-schema.org/draft-04/schema#',
    'type': 'object',
    'title': 'AWX API Schema',
    'properties': {
        'available_versions': {
            'type': 'object',
        },
        'description': {
            'type': 'string',
        },
        'current_version': {
            'type': 'string',
        }
    },
    "required": [ 'available_versions', 'description', 'current_version' ],
    "additionalProperties": False
}

@pytest.mark.nondestructive
class Test_Api_Basics(Base_Api_Test):
    def test_connection(self, api):
        assert api.get('/api'), "Unable to connect"

    def test_api_schema(self, api):
        data = api.get('/api')
        jsonschema.validate(data, __schema__)

    def test_current_version(self, api):
        data = api.get('/api')
        current_version = data.get('current_version')
        available_versions = data.get('available_versions')
        assert current_version in available_versions.values(), \
            "Unable to find current_version (%s) in list of " \
            "available_versions (%s)" % \
            (current_version, available_versions.values())

        # Does current_version path work?
        assert isinstance(api.get(current_version), dict)

