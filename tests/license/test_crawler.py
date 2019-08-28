import http.client

from awxkit.api.client import Connection
from awxkit.config import config
import pytest


# Generate fixture values for 'method' and 'resource'
def pytest_generate_tests(metafunc):

    # Don't attempt to crawl if we weren't asked to do so
    for_reals = not (metafunc.config.option.help or metafunc.config.option.showfixtures or
                     metafunc.config.option.markers) and metafunc.config.option.base_url not in [None, '']
    if for_reals:
        for fixture in metafunc.fixturenames:
            test_set = list()

            # Skip if running with --help or --collectonly
            if metafunc.config.option.help or metafunc.config.option.collectonly:
                return

            if fixture == 'method':
                request_methods = ['HEAD', 'GET', 'POST', 'PUT', 'PATCH', 'OPTIONS']
                test_set.extend(request_methods)

            if fixture == 'resource':
                # Discover available API resources
                api = Connection(config.base_url)
                r = api.get('/api/')
                data = r.json()
                for version in data.get('available_versions').values():
                    r = api.get(version)
                    api_resources = r.json().values()
                    test_set.extend(api_resources)

            if test_set:
                metafunc.parametrize(fixture, test_set, ids=test_set)


def assert_response(connection, resource, method, response_code=http.client.OK, response_schema='unauthorized', data={}):
    """Issue the desired API method on the provided resource.  Assert that the
    http response is as expected.
    """
    # Determine requested api method
    method = method.lower()

    # Call the desired API $method on the provided $resource (e.g.
    # api.get('/api/v2/me/')
    if method in ['get', 'head', 'options']:
        r = getattr(connection, method)(resource)
    else:
        r = getattr(connection, method)(resource, data)

    # Assert api response code matches expected
    assert r.status_code == response_code


bad_request = (http.client.BAD_REQUEST, 'bad_request')
forbidden = (http.client.FORBIDDEN, 'forbidden')
method_not_allowed = (http.client.METHOD_NOT_ALLOWED, 'method_not_allowed')
unauthorized = (http.client.UNAUTHORIZED, 'unauthorized')


@pytest.mark.serial
def test_unauthenticated(authtoken, resource, method):
    expected = {'HEAD': (http.client.UNAUTHORIZED, 'head'),
                'GET': unauthorized,
                'OPTIONS': unauthorized,
                'PATCH': unauthorized,
                'POST': unauthorized,
                'PUT': unauthorized}

    exceptions = {'authtoken/': {'HEAD': (http.client.METHOD_NOT_ALLOWED, 'head'),
                                 'GET': (http.client.METHOD_NOT_ALLOWED, 'get'),
                                 'OPTIONS': (http.client.OK, 'options'),
                                 'PATCH': (http.client.METHOD_NOT_ALLOWED, 'patch'),
                                 'POST': bad_request,
                                 'PUT': (http.client.METHOD_NOT_ALLOWED, 'put')},
                  'ping/': {'HEAD': (http.client.OK, 'head'),
                            'GET': (http.client.OK, 'get'),
                            'OPTIONS': (http.client.OK, 'options'),
                            'PATCH': (http.client.METHOD_NOT_ALLOWED, 'patch'),
                            'POST': (http.client.METHOD_NOT_ALLOWED, 'post'),
                            'PUT': (http.client.METHOD_NOT_ALLOWED, 'put')}}

    # Generic response
    (expected_response_code, expected_response_schema) = expected[method]

    # Check if any api link requires special handling
    versionless_endpoint = resource[8:]
    if versionless_endpoint in exceptions and method in exceptions[versionless_endpoint]:
        expected_response_code, expected_response_schema = exceptions[versionless_endpoint][method]

    # use new Connection() instances for their lack of valid session
    assert_response(Connection(config.base_url, verify=not config.assume_untrusted), resource, method,
                    expected_response_code, expected_response_schema)


@pytest.mark.serial
@pytest.mark.usefixtures('authtoken', 'no_license')
def test_authenticated(connection, resource, method):

    expected = {'HEAD': (http.client.OK, 'head'),
                'GET': (http.client.OK, 'get'),
                'POST': bad_request,
                'PUT': method_not_allowed,
                'PATCH': method_not_allowed,
                'OPTIONS': (http.client.OK, 'options')}

    exceptions = {'activity_stream/': {'POST': method_not_allowed},
                  'authtoken/': {'HEAD': (http.client.METHOD_NOT_ALLOWED, 'head'),
                                 'GET': method_not_allowed},
                  'config/': {'POST': (http.client.BAD_REQUEST, 'license_invalid')},
                  'dashboard/': {'POST': method_not_allowed},
                  'instances/': {'POST': method_not_allowed},
                  'inventory_updates/': {'POST': method_not_allowed},
                  'job_events/': {'POST': method_not_allowed},
                  '/api/v2/jobs/': {'POST': method_not_allowed},
                  '/api/v2/tokens/': {'POST': (http.client.CREATED, 'post')},
                  'me/': {'POST': method_not_allowed},
                  'metrics/': {'POST': method_not_allowed},
                  'notifications/': {'POST': method_not_allowed},
                  'ping/': {'POST': method_not_allowed},
                  'project_updates/': {'POST': method_not_allowed},
                  'roles/': {'POST': method_not_allowed},
                  'settings/': {'POST': method_not_allowed},
                  'system_job_templates/': {'POST': method_not_allowed},
                  'system_jobs/': {'POST': method_not_allowed},
                  'unified_jobs/': {'POST': method_not_allowed},
                  'unified_job_templates/': {'POST': method_not_allowed},
                  'workflow_jobs/': {'POST': method_not_allowed},
                  'workflow_job_nodes/': {'POST': method_not_allowed},
                  'workflow_job_templates/': {'PATCH': method_not_allowed,
                                              'PUT': method_not_allowed},
    }

    # Generic response
    (expected_response_code, expected_response_schema) = expected[method]

    # Check if any api link requires special handling
    if resource in exceptions and method in exceptions[resource]:
        expected_response_code, expected_response_schema = exceptions[resource][method]
    else:
        versionless_endpoint = resource[8:]
        if versionless_endpoint in exceptions and method in exceptions[versionless_endpoint]:
            expected_response_code, expected_response_schema = exceptions[versionless_endpoint][method]

    assert_response(connection, resource, method, expected_response_code, expected_response_schema)
