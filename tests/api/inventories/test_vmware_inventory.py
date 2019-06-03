import fauxfactory
import pytest
import requests
from urllib.parse import urljoin

from towerkit.config import config
from towerkit import utils, exceptions
from kubernetes.stream import stream

from tests.api import APITest

@pytest.fixture(scope='class')
def k8s_govcsim(gke_client_cscope, request):
    K8sClient = gke_client_cscope(config.credentials)
    prefix = 'govcsim'
    cluster_domain = 'services.k8s.tower-qe.testing.ansible.com'
    deployment_name = K8sClient.random_deployment_name(prefix)
    containerspec = [{'name': '{}-{}'.format(deployment_name, 'app'),
                        'image': 'quay.io/ansible/vcenter-test-container',
                        'ports': [{'containerPort': 5000, 'protocol': 'TCP'},
                                  {'containerPort': 443, 'protocol': 'TCP'}],
                        'env': []}]
    portspec = [{'name': 'govcsimcontrol',
                 'port': 5000,
                 'protocol': 'TCP',
                 'targetPort': 5000},
                {'name': 'govcsimserver',
                 'port': 443,
                 'protocol': 'TCP',
                 'targetPort': 443}]
    govcsim_deployment = K8sClient.generate_deployment(deployment_name, containerspec)
    govcsim_service = K8sClient.generate_service(deployment_name, portspec)
    K8sClient.apps.create_namespaced_deployment(body=govcsim_deployment, namespace='default')
    K8sClient.core.create_namespaced_service(body=govcsim_service, namespace='default')
    request.addfinalizer(lambda: K8sClient.destroy(deployment_name))
    controller_url = "https://http-{}-port-5000.{}".format(deployment_name, cluster_domain)
    sim_url = "https://https-{}-port-443.{}".format(deployment_name, cluster_domain)

    sess = requests.Session()
    sim = sess.get('{}/spawn?username=user&password=pass&cluster=1&port=443&vm=5'.format(controller_url))
    return sim_url


@pytest.mark.api
@pytest.mark.destructive
@pytest.mark.usefixtures('authtoken', 'install_enterprise_license_unlimited')
class TestGovcsim(APITest):
    def test_govcsim_spawn(self, k8s_govcsim):
    