import pytest
import httplib
import jsonschema
from common.api import Connection

api = None

__unauthorized_schema__ = {
    '$schema': 'http://json-schema.org/draft-04/schema#',
    'type': 'object',
    'properties': {
        'detail': {
            'type': 'string',
        },
    },
    'required': ['detail', ],
    'additionalProperties': False,
}

__authtoken_bad_password__ = {
    '$schema': 'http://json-schema.org/draft-04/schema#',
    'type': 'object',
    'properties': {
        "username": {
            'type': 'array',
        },
        "password": {
            'type': 'array',
        },
    },
    'required': ['username', 'password', ],
    'additionalProperties': False,
}

def setup_function(function):
    global api # yuck

    api = Connection(pytest.config.option.base_url)

@pytest.mark.nondestructive
def assert_response(link, method, response_code=httplib.OK, response_schema={}, data={}):
    global api # yuck

    func_method = getattr(api, method.lower())
    if method.lower() in ['get', 'head', 'options']:
        r = func_method(link)
    else:
        r = func_method(link, data)

    assert r.code == response_code

    if response_schema:
        jsonschema.validate(r.json(), response_schema)

@pytest.mark.nondestructive
def test_link_generator():
    global api # yuck

    r = api.get('/api/')
    data = r.json()
    current_version = data.get('current_version')
    r = api.get(current_version)
    for k,v in r.json().items():
        for method in ['GET', 'PUT', 'POST', 'HEAD', 'OPTIONS']:
            expected_response_code = httplib.UNAUTHORIZED
            expected_response_schema = __unauthorized_schema__

            # authtoken only supports POST, OPTIONS
            if k == 'authtoken':
                if method in ['HEAD', 'GET', 'PUT']:
                    expected_response_code = httplib.METHOD_NOT_ALLOWED
                elif method in ['OPTIONS']:
                    expected_response_code = httplib.OK
                    expected_response_schema = {}
                elif method in ['POST']:
                    expected_response_code = httplib.BAD_REQUEST
                    expected_response_schema = __authtoken_bad_password__
                else:
                    expected_response_code = httplib.UNAUTHORIZED

            # No json response for 'HEAD'
            if method == 'HEAD':
                expected_response_schema = {}

            # assert!
            yield "%s:%s" % (method, v), assert_response, v, method, expected_response_code, expected_response_schema

