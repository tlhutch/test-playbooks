import pytest
import httplib
from unittestzero import Assert
from common.api import Connection
from common.api.schema import validate

api = None

def setup_function(function):
    global api # yuck

    api = Connection(pytest.config.option.base_url)

@pytest.mark.nondestructive
def assert_response(link, method, response_code=httplib.OK, response_schema='unauthorized', data={}):
    global api # yuck

    # Call requested api method
    method = method.lower()
    func_method = getattr(api, method)
    if method in ['get', 'head', 'options']:
        r = func_method(link)
    else:
        r = func_method(link, data)

    # Assert api response code matches expected
    Assert.equal(r.code, response_code)

    # validate api json response matches expected
    if response_schema is not None:
        validate(r.json(), link[7:-1], response_schema)

@pytest.mark.nondestructive
def test_link_generator():
    global api # yuck

    r = api.get('/api/')
    data = r.json()
    current_version = data.get('current_version')
    r = api.get(current_version)
    for key, link in r.json().items():
        for method in ['GET', 'PUT', 'POST', 'HEAD', 'OPTIONS']:
            expected_response_code = httplib.UNAUTHORIZED
            expected_response_schema = 'unauthorized'

            # authtoken only supports POST, OPTIONS
            if key == 'authtoken':
                if method in ['HEAD', 'GET', 'PUT']:
                    expected_response_code = httplib.METHOD_NOT_ALLOWED
                elif method in ['OPTIONS']:
                    expected_response_code = httplib.OK
                    expected_response_schema = None
                elif method in ['POST']:
                    expected_response_code = httplib.BAD_REQUEST
                    expected_response_schema = 'bad_password'
                else:
                    expected_response_code = httplib.UNAUTHORIZED

            # No json response for 'HEAD'
            if method == 'HEAD':
                expected_response_schema = None

            # assert!
            yield "%s:%s" % (method, link), assert_response, link, method, expected_response_code, expected_response_schema
