import pytest
import httplib
from unittestzero import Assert
from common.api.schema import validate
from plugins.pytest_restqa.rest_client import Connection
from plugins.pytest_restqa.pytest_restqa import load_credentials

api = None
credentials = None

# def setup_function(function):
def setup_module(module):
    global api, credentials # yuck
    api = Connection(pytest.config.option.base_url)
    credentials = load_credentials(filename=pytest.config.option.credentials_file)

@pytest.mark.skip_selenium
@pytest.mark.nondestructive
# Not sure the following does anything
## @pytest.yield_fixture(scope='function')
def assert_response(api, link, method, response_code=httplib.OK, response_schema='unauthorized', data={}):

    # Determine requested api method
    method = method.lower()

    # Does the method require a payload argument?
    if method in ['get', 'head', 'options']:
        r = getattr(api, method)(link)
    else:
        r = getattr(api, method)(link, data)

    # Assert api response code matches expected
    assert r.code == response_code

    # Extract JSON response
    try:
        json = r.json()
    except ValueError:
        json = dict()

    # validate api json response matches expected
    validate(json, link[7:-1], response_schema)

@pytest.mark.nondestructive
@pytest.mark.skip_selenium
def test_crawl_unauthorized():
    global api # yuck

    # Clear out any authentication credentials
    api.auth = None

    # Navigate to the api->$current_version
    r = api.get('/api/')
    data = r.json()
    current_version = data.get('current_version')
    r = api.get(current_version)

    expected_response = {
        'HEAD': (httplib.UNAUTHORIZED, 'head'),
        'GET': (httplib.UNAUTHORIZED, 'unauthorized'),
        'POST': (httplib.UNAUTHORIZED, 'unauthorized'),
        'PUT': (httplib.UNAUTHORIZED, 'unauthorized'),
        'PATCH': (httplib.UNAUTHORIZED, 'unauthorized'),
        'OPTIONS': (httplib.UNAUTHORIZED, 'unauthorized'),
    }

    exception_matrix = {
        '/api/v1/authtoken/': {
            'HEAD': (httplib.METHOD_NOT_ALLOWED, 'head'),
            'GET': (httplib.METHOD_NOT_ALLOWED, 'get'),
            'PUT': (httplib.METHOD_NOT_ALLOWED, 'put'),
            'PATCH': (httplib.METHOD_NOT_ALLOWED, 'patch'),
            'OPTIONS': (httplib.OK, 'options'),
            'POST': (httplib.BAD_REQUEST, 'bad_request'),
        },
    }

    # Navigate through top-level API
    for key, link in r.json().items():
        for method in expected_response.keys():

            # Generic response
            (expected_response_code, expected_response_schema) = expected_response[method]

            # Check if any api link requires special handling
            if link in exception_matrix:
                if method in exception_matrix[link]:
                    (expected_response_code, expected_response_schema) = exception_matrix[link][method]

            # assert!
            yield "%s:%s" % (method, link), assert_response, api, link, method, expected_response_code, expected_response_schema

@pytest.mark.nondestructive
@pytest.mark.skip_selenium
@pytest.mark.usefixtures("authtoken")
def test_crawl_authorized():
    global api, credentials # yuck

    # Login
    api.login(*credentials['default'].values())

    # Navigate to the api->$current_version
    r = api.get('/api/')
    data = r.json()
    current_version = data.get('current_version')
    r = api.get(current_version)

    expected_response = {
        'HEAD': (httplib.OK, 'head'),
        'GET': (httplib.OK, 'get'),
        'POST': (httplib.BAD_REQUEST, 'bad_request'),
        'PUT': (httplib.METHOD_NOT_ALLOWED, 'method_not_allowed'),
        'PATCH': (httplib.METHOD_NOT_ALLOWED, 'method_not_allowed'),
        'OPTIONS': (httplib.OK, 'options'),
    }

    exception_matrix = {
        '/api/v1/activity_stream/': {
            'POST': (httplib.METHOD_NOT_ALLOWED, 'method_not_allowed'),
        },
        '/api/v1/authtoken/': {
            'HEAD': (httplib.METHOD_NOT_ALLOWED, 'head'),
            'GET': (httplib.METHOD_NOT_ALLOWED, 'method_not_allowed'),
            'POST': (httplib.BAD_REQUEST, 'bad_request'),
        },
        '/api/v1/config/': {
            'POST': (httplib.METHOD_NOT_ALLOWED, 'method_not_allowed'),
        },
        '/api/v1/dashboard/': {
            'POST': (httplib.METHOD_NOT_ALLOWED, 'method_not_allowed'),
        },
        '/api/v1/me/': {
            'POST': (httplib.METHOD_NOT_ALLOWED, 'method_not_allowed'),
        },
        '/api/v1/inventory_sources/': {
            'POST': (httplib.METHOD_NOT_ALLOWED, 'method_not_allowed'),
        },
    }

    # Navigate through top-level API
    for key, link in r.json().items():
        for method in expected_response.keys():

            # Generic resopnse
            (expected_response_code, expected_response_schema) = expected_response[method]

            # Check if any api link requires special handling
            if link in exception_matrix:
                if method in exception_matrix[link]:
                    (expected_response_code, expected_response_schema) = exception_matrix[link][method]

            # assert!
            yield "%s:%s" % (method, link), assert_response, api, link, method, expected_response_code, expected_response_schema
