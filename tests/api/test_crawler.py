import pytest
import httplib
from qe.api.schema import validate
from qe.api.client import Connection


# Generate fixture values for 'method' and 'resource'
def pytest_generate_tests(metafunc):

    # Don't attempt to crawl if we weren't asked to do so
    for_reals = not (metafunc.config.option.help or metafunc.config.option.showfixtures or
                     metafunc.config.option.markers) and metafunc.config.option.base_url not in [None, '']
    if for_reals:
        for fixture in metafunc.fixturenames:
            test_set = list()
            id_list = list()

            # Skip if running with --help or --collectonly
            if pytest.config.option.help or pytest.config.option.collectonly:
                return

            if fixture == 'method':
                request_methods = ['HEAD', 'GET', 'POST', 'PUT', 'PATCH', 'OPTIONS', ]
                test_set.extend(request_methods)
                id_list.extend(request_methods)

            if fixture == 'resource':
                # Discover available API resources
                api = Connection(pytest.config.option.base_url)
                r = api.get('/api/')
                data = r.json()
                current_version = data.get('current_version')
                r = api.get(current_version)
                api_resources = r.json().values()

                test_set.extend(api_resources)
                id_list.extend(api_resources)

            if test_set and id_list:
                metafunc.parametrize(fixture, test_set, ids=id_list)


def assert_response(api, resource, method, response_code=httplib.OK, response_schema='unauthorized', data={}):
    '''Issue the desired API method on the provided resource.  Assert that the
    http response and JSON schema are valid
    '''

    # Determine requested api method
    method = method.lower()

    # Call the desired API $method on the provided $resource (e.g.
    # api.get('/api/v1/me/')
    if method in ['get', 'head', 'options']:
        r = getattr(api, method)(resource)
    else:
        r = getattr(api, method)(resource, data)

    # Assert api response code matches expected
    assert r.code == response_code

    # Extract JSON response
    try:
        json = r.json()
    except ValueError:
        json = dict()

    # Validate API JSON response
    validate(json, resource, response_schema)


@pytest.fixture(scope="function")
def logout(api):
    '''Logout of the API on each function call'''
    api.logout()


@pytest.fixture(scope="function")
def login(api, testsetup):
    '''Login to the API on each function call'''
    api.login(*testsetup.credentials['default'].values())


@pytest.mark.api
@pytest.mark.skip_selenium
@pytest.mark.nondestructive
def test_unauthenticated(api, resource, method, authtoken, no_license):

    expected_response = {
        'HEAD': (httplib.UNAUTHORIZED, 'head'),
        'GET': (httplib.UNAUTHORIZED, 'unauthorized'),
        'POST': (httplib.UNAUTHORIZED, 'unauthorized'),
        'PUT': (httplib.UNAUTHORIZED, 'unauthorized'),
        'PATCH': (httplib.UNAUTHORIZED, 'unauthorized'),
        'OPTIONS': (httplib.UNAUTHORIZED, 'unauthorized'),
    }

    exception_matrix = {
        '/api/v1/ping/': {
            'HEAD': (httplib.OK, 'head'),
            'GET': (httplib.OK, 'get'),
            'PUT': (httplib.METHOD_NOT_ALLOWED, 'put'),
            'PATCH': (httplib.METHOD_NOT_ALLOWED, 'patch'),
            'OPTIONS': (httplib.OK, 'options'),
            'POST': (httplib.METHOD_NOT_ALLOWED, 'post'),
        },
        '/api/v1/authtoken/': {
            'HEAD': (httplib.METHOD_NOT_ALLOWED, 'head'),
            'GET': (httplib.METHOD_NOT_ALLOWED, 'get'),
            'PUT': (httplib.METHOD_NOT_ALLOWED, 'put'),
            'PATCH': (httplib.METHOD_NOT_ALLOWED, 'patch'),
            'OPTIONS': (httplib.OK, 'options'),
            'POST': (httplib.BAD_REQUEST, 'bad_request'),
        },
    }

    # Generic response
    (expected_response_code, expected_response_schema) = expected_response[method]

    # Check if any api link requires special handling
    if resource in exception_matrix:
        if method in exception_matrix[resource]:
            (expected_response_code, expected_response_schema) = exception_matrix[resource][method]

    # Query API with no auth credentials
    try:
        previous_auth = api.session.auth
        api.logout()
        assert_response(api, resource, method, expected_response_code, expected_response_schema)
    finally:
        api.session.auth = previous_auth


@pytest.mark.api
@pytest.mark.skip_selenium
@pytest.mark.nondestructive
def test_authenticated(api, resource, method, authtoken, no_license):
    '''
    Schema validation methods (e.g. 'head', 'get', 'method_not_allowed')
    are found in schema/SCHEMA_VERSION/__init__.py::Awx_Schema
    '''
    expected_response = {
        'HEAD': (httplib.OK, 'head'),
        'GET': (httplib.OK, 'get'),
        'POST': (httplib.BAD_REQUEST, 'bad_request'),
        'PUT': (httplib.METHOD_NOT_ALLOWED, 'method_not_allowed'),
        'PATCH': (httplib.METHOD_NOT_ALLOWED, 'method_not_allowed'),
        'OPTIONS': (httplib.OK, 'options'),
    }

    exception_matrix = {
        '/api/v1/organizations/': {
            'POST': (httplib.PAYMENT_REQUIRED, 'payment_required'),
        },
        '/api/v1/activity_stream/': {
            'GET': (httplib.PAYMENT_REQUIRED, 'payment_required'),
            'HEAD': (httplib.PAYMENT_REQUIRED, 'head'),
            'POST': (httplib.METHOD_NOT_ALLOWED, 'method_not_allowed'),
        },
        '/api/v1/authtoken/': {
            'HEAD': (httplib.METHOD_NOT_ALLOWED, 'head'),
            'GET': (httplib.METHOD_NOT_ALLOWED, 'method_not_allowed'),
            'POST': (httplib.BAD_REQUEST, 'bad_request'),
        },
        '/api/v1/dashboard/': {
            'POST': (httplib.METHOD_NOT_ALLOWED, 'method_not_allowed'),
        },
        '/api/v1/config/': {
            'POST': (httplib.BAD_REQUEST, 'license_invalid'),
        },
        '/api/v1/me/': {
            'POST': (httplib.METHOD_NOT_ALLOWED, 'method_not_allowed'),
        },
        '/api/v1/hosts/': {
            'POST': (httplib.BAD_REQUEST, 'bad_request'),
        },
        '/api/v1/inventory_sources/': {
            'POST': (httplib.METHOD_NOT_ALLOWED, 'method_not_allowed'),
        },
        '/api/v1/inventory_updates/': {
            'POST': (httplib.METHOD_NOT_ALLOWED, 'method_not_allowed'),
        },
        '/api/v1/project_updates/': {
            'POST': (httplib.METHOD_NOT_ALLOWED, 'method_not_allowed'),
        },
        '/api/v1/unified_jobs/': {
            'POST': (httplib.METHOD_NOT_ALLOWED, 'method_not_allowed'),
        },
        '/api/v1/unified_job_templates/': {
            'POST': (httplib.METHOD_NOT_ALLOWED, 'method_not_allowed'),
        },
        '/api/v1/system_job_templates/': {
            'POST': (httplib.METHOD_NOT_ALLOWED, 'method_not_allowed'),
        },
        '/api/v1/schedules/': {  # Doesn't yet support POST
            'POST': (httplib.METHOD_NOT_ALLOWED, 'method_not_allowed'),
        },
        '/api/v1/settings/': {
            'POST': (httplib.METHOD_NOT_ALLOWED, 'method_not_allowed'),
        },
        '/api/v1/ping/': {
            'POST': (httplib.METHOD_NOT_ALLOWED, 'method_not_allowed'),
        },
        '/api/v1/notifications/': {
            'POST': (httplib.METHOD_NOT_ALLOWED, 'method_not_allowed'),
        },
        '/api/v1/roles/': {
            'POST': (httplib.METHOD_NOT_ALLOWED, 'method_not_allowed'),
        },
        '/api/v1/job_events/': {
            'POST': (httplib.METHOD_NOT_ALLOWED, 'method_not_allowed'),
        },
        # Posting {} to workflow_job_template_nodes creates a resource
        # Behavior is being evaluated in https://github.com/ansible/ansible-tower/issues/3552
        '/api/v1/workflow_job_template_nodes/': {
            'POST': (httplib.CREATED, 'workflow_job_template_node_created'),
        }
    }

    # Generic response
    (expected_response_code, expected_response_schema) = expected_response[method]

    # Check if any api link requires special handling
    if resource in exception_matrix:
        if method in exception_matrix[resource]:
            (expected_response_code, expected_response_schema) = exception_matrix[resource][method]

    assert_response(api, resource, method, expected_response_code, expected_response_schema)
