import httplib

from towerkit.utils import version_from_endpoint
from towerkit.api.client import Connection
from towerkit.api.schema import validate
from towerkit.config import config
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
            if pytest.config.option.help or pytest.config.option.collectonly:
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
                metafunc.parametrize(fixture, test_set, ids=list(test_set))


def assert_response(connection, resource, method, response_code=httplib.OK, response_schema='unauthorized', data={}):
    """Issue the desired API method on the provided resource.  Assert that the
    http response and JSON schema are valid
    """
    # Determine requested api method
    method = method.lower()

    # Call the desired API $method on the provided $resource (e.g.
    # api.get('/api/v1/me/')
    if method in ['get', 'head', 'options']:
        r = getattr(connection, method)(resource)
    else:
        r = getattr(connection, method)(resource, data)

    # Assert api response code matches expected
    assert r.status_code == response_code

    # Extract JSON response
    try:
        json = r.json()
    except ValueError:
        json = dict()

    # Validate API JSON response:
    # Schema validation methods (e.g. 'head', 'get', 'method_not_allowed')
    # are found in schema/SCHEMA_VERSION/__init__.py::Awx_Schema
    validate(json, resource, response_schema, version=version_from_endpoint(resource))


bad_request = (httplib.BAD_REQUEST, 'bad_request')
forbidden = (httplib.FORBIDDEN, 'forbidden')
method_not_allowed = (httplib.METHOD_NOT_ALLOWED, 'method_not_allowed')
payment_required = (httplib.PAYMENT_REQUIRED, 'payment_required')
unauthorized = (httplib.UNAUTHORIZED, 'unauthorized')


@pytest.mark.api
@pytest.mark.nondestructive
@pytest.mark.mp_group('TestCrawler', 'isolated_free')
def test_unauthenticated(authtoken, no_license, resource, method):
    expected = {'HEAD': (httplib.UNAUTHORIZED, 'head'),
                'GET': unauthorized,
                'OPTIONS': unauthorized,
                'PATCH': unauthorized,
                'POST': unauthorized,
                'PUT': unauthorized}

    exceptions = {'authtoken/': {'HEAD': (httplib.METHOD_NOT_ALLOWED, 'head'),
                                 'GET': (httplib.METHOD_NOT_ALLOWED, 'get'),
                                 'OPTIONS': (httplib.OK, 'options'),
                                 'PATCH': (httplib.METHOD_NOT_ALLOWED, 'patch'),
                                 'POST': bad_request,
                                 'PUT': (httplib.METHOD_NOT_ALLOWED, 'put')},
                  'activity_stream/': {'HEAD': (httplib.PAYMENT_REQUIRED, 'head'),
                                       'GET': payment_required,
                                       'OPTIONS': payment_required,
                                       'PATCH': payment_required,
                                       'POST': payment_required,
                                       'PUT': payment_required},
                  'ping/': {'HEAD': (httplib.OK, 'head'),
                            'GET': (httplib.OK, 'get'),
                            'OPTIONS': (httplib.OK, 'options'),
                            'PATCH': (httplib.METHOD_NOT_ALLOWED, 'patch'),
                            'POST': (httplib.METHOD_NOT_ALLOWED, 'post'),
                            'PUT': (httplib.METHOD_NOT_ALLOWED, 'put')},
                  'workflow_job_nodes/': {'HEAD': (httplib.PAYMENT_REQUIRED, 'head'),
                                          'GET': unauthorized,
                                          'OPTIONS': unauthorized,
                                          'PATCH': payment_required,
                                          'POST': payment_required,
                                          'PUT': payment_required},
                  'workflow_job_template_nodes/': {'HEAD': (httplib.PAYMENT_REQUIRED, 'head'),
                                                   'GET': unauthorized,
                                                   'OPTIONS': unauthorized,
                                                   'PATCH': payment_required,
                                                   'POST': payment_required,
                                                   'PUT': payment_required},
                  'workflow_job_templates/': {'HEAD': (httplib.PAYMENT_REQUIRED, 'head'),
                                              'GET': unauthorized,
                                              'OPTIONS': unauthorized,
                                              'PATCH': payment_required,
                                              'POST': payment_required,
                                              'PUT': payment_required},
                  'workflow_jobs/': {'HEAD': (httplib.PAYMENT_REQUIRED, 'head'),
                                     'GET': unauthorized,
                                     'OPTIONS': unauthorized,
                                     'PATCH': payment_required,
                                     'POST': payment_required,
                                     'PUT': payment_required}}

    # Generic response
    (expected_response_code, expected_response_schema) = expected[method]

    # Check if any api link requires special handling
    versionless_endpoint = resource[8:]
    if versionless_endpoint in exceptions and method in exceptions[versionless_endpoint]:
        expected_response_code, expected_response_schema = exceptions[versionless_endpoint][method]

    # use new Connection() instances for their lack of valid session
    assert_response(Connection(config.base_url, verify=not config.assume_untrusted), resource, method,
                    expected_response_code, expected_response_schema)


@pytest.mark.api
@pytest.mark.nondestructive
@pytest.mark.mp_group('TestCrawler')
def test_authenticated(connection, authtoken, no_license, resource, method):

    expected = {'HEAD': (httplib.OK, 'head'),
                'GET': (httplib.OK, 'get'),
                'POST': bad_request,
                'PUT': method_not_allowed,
                'PATCH': method_not_allowed,
                'OPTIONS': (httplib.OK, 'options')}

    exceptions = {'activity_stream/': {'HEAD': (httplib.PAYMENT_REQUIRED, 'head'),
                                       'GET': payment_required,
                                       'OPTIONS': payment_required,
                                       'PATCH': payment_required,
                                       'POST': payment_required,
                                       'PUT': payment_required},
                  'authtoken/': {'HEAD': (httplib.METHOD_NOT_ALLOWED, 'head'),
                                 'GET': method_not_allowed},
                  'config/': {'POST': (httplib.BAD_REQUEST, 'license_invalid')},
                  'dashboard/': {'POST': method_not_allowed},
                  'instance_groups/': {'POST': method_not_allowed},
                  'instances/': {'POST': method_not_allowed},
                  '/api/v1/inventory_sources/': {'POST': method_not_allowed},
                  'inventory_updates/': {'POST': method_not_allowed},
                  'job_events/': {'POST': method_not_allowed},
                  '/api/v2/jobs/': {'POST': method_not_allowed},
                  'me/': {'POST': method_not_allowed},
                  'notifications/': {'POST': method_not_allowed},
                  'organizations/': {'POST': payment_required},
                  'ping/': {'POST': method_not_allowed},
                  'project_updates/': {'POST': method_not_allowed},
                  'roles/': {'POST': method_not_allowed},
                  'schedules/': {'POST': method_not_allowed},
                  'settings/': {'POST': method_not_allowed},
                  'system_job_templates/': {'POST': method_not_allowed},
                  'unified_jobs/': {'POST': method_not_allowed},
                  'unified_job_templates/': {'POST': method_not_allowed},
                  'workflow_job_nodes/': {'HEAD': (httplib.PAYMENT_REQUIRED, 'head'),
                                          'PATCH': payment_required,
                                          'POST': payment_required,
                                          'PUT': payment_required},
                  'workflow_job_template_nodes/': {'HEAD': (httplib.PAYMENT_REQUIRED, 'head'),
                                                   'PATCH': payment_required,
                                                   'POST': payment_required,
                                                   'PUT': payment_required},
                  'workflow_job_templates/': {'HEAD': (httplib.PAYMENT_REQUIRED, 'head'),
                                              'PATCH': payment_required,
                                              'POST': payment_required,
                                              'PUT': payment_required},
                  'workflow_jobs/': {'HEAD': (httplib.PAYMENT_REQUIRED, 'head'),
                                     'PATCH': payment_required,
                                     'POST': payment_required,
                                     'PUT': payment_required}}

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
