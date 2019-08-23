import uuid

import pytest
import requests
import xml.etree.ElementTree as ET
import xml
from requests.auth import HTTPBasicAuth

from awxkit.config import config
from awxkit import utils

from tests.api import APITest


@pytest.fixture(scope='class')
def k8s_splunk(gke_client_cscope, request):
    K8sClient = gke_client_cscope(config.credentials)
    prefix = 'splunk'
    deployment_name = K8sClient.random_deployment_name(prefix)
    cluster_domain = 'services.k8s.tower-qe.testing.ansible.com'
    containerspec = [{'name': 'splunk',
                        'image': 'chrismeyers/splunk:latest',
                        'ports': [{'containerPort': 8000,
                                   'protocol': 'TCP'},
                                  {'containerPort': 8088,
                                   'protocol': 'TCP'},
                                  {'containerPort': 8089,
                                   'protocol': 'TCP'}],
                        'env': [{'name': 'SPLUNK_START_ARGS',
                                'value': '--accept-license'},
                                {'name': 'SPLUNK_PASSWORD',
                                 'value': 'password'}],
                    }]
    portspec = [{'name': 'spunk-web',
                     'port': 8000,
                     'protocol': 'TCP',
                     'targetPort': 8000},
                {'name': 'spunk-logger',
                     'port': 8088,
                     'protocol': 'TCP',
                     'targetPort': 8088},
                {'name': 'spunk-api',
                     'port': 8089,
                     'protocol': 'TCP',
                     'targetPort': 8089}]

    splunk_deployment = K8sClient.generate_deployment(deployment_name, containerspec)
    splunk_service = K8sClient.generate_service(deployment_name, portspec)
    K8sClient.apps.create_namespaced_deployment(body=splunk_deployment, namespace='default')
    K8sClient.core.create_namespaced_service(body=splunk_service, namespace='default')
    splunk_url = "https://http-{}-port-8000.{}".format(deployment_name, cluster_domain)
    splunk_api_url = 'https://https-{}-port-8089.{}'.format(deployment_name, cluster_domain)
    splunk_logger_url = 'https://https-{}-port-8088.{}'.format(deployment_name, cluster_domain)
    request.addfinalizer(lambda: K8sClient.destroy(deployment_name))

    # Wait for HTTP service to become ready
    utils.poll_until(lambda: requests.get(splunk_api_url).status_code == 200,
                     interval=5, timeout=120)
    return splunk_url, splunk_api_url, splunk_logger_url


@pytest.fixture
def splunk_url(k8s_splunk):
    return k8s_splunk[0]


@pytest.fixture
def splunk_api_url(k8s_splunk):
    return k8s_splunk[1]


@pytest.fixture
def splunk_logger_url(k8s_splunk):
    return k8s_splunk[2]


@pytest.fixture
def splunk_api_session():
    api = requests.Session()
    api.auth = HTTPBasicAuth('admin', 'password')
    return api


@pytest.fixture
def splunk_logger_token(splunk_api_session, splunk_api_url):
    api = splunk_api_session
    # Delete the token, helpful when debugging
    res = api.delete('{}/servicesNS/admin/splunk_httpinput/data/inputs/http/logtoken'.format(splunk_api_url))
    res = api.post('{}/servicesNS/admin/splunk_httpinput/data/inputs/http'.format(splunk_api_url), data={'name': 'logtoken'})
    token = ET.fromstring(res.content).findall(".//*[@name='token']")[0].text
    return token


@pytest.fixture
def splunk_logger_session(splunk_logger_token):
    log = requests.Session()
    log.headers.update({'Authorization': 'Splunk {}'.format(splunk_logger_token)})
    return log


class TestSplunkLogging(APITest):

    '''
    Create 2 events in splunk; then find those 2 created events.
    '''
    def test_splunk_log(self, factories, v2, splunk_logger_url, splunk_api_url, splunk_logger_session, splunk_api_session):
        _api = splunk_api_session
        _log = splunk_logger_session

        my_uuid1 = uuid.uuid4()
        my_uuid2 = uuid.uuid4()

        assert 200 == _log.post('{}/services/collector'.format(splunk_logger_url),
                                json={'event': "my uuid is {}".format(str(my_uuid1))}).status_code
        assert 200 == _log.post('{}/services/collector'.format(splunk_logger_url),
                                json={'event': "my uuid is {}".format(str(my_uuid2))}).status_code

        results = []

        def get_log_results():
            res = _api.post('{}/services/search/jobs/export'.format(splunk_api_url), data={'search': 'search *'})
            try:
                found = list(ET.fromstring(res.content).findall('.//*v'))
            except xml.etree.ElementTree.ParseError:
                return False

            if not found:
                return False

            results.extend([f.text for f in found])

            if len(results) < 2:
                return False

            return True

        # It can take time for the event to be processed and end up in the search results
        utils.poll_until(get_log_results, interval=5, timeout=120)

        assert "my uuid is {}".format(str(my_uuid1)) in results
        assert "my uuid is {}".format(str(my_uuid2)) in results
