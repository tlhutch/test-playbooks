import fauxfactory
import pytest
import requests
from urllib.parse import urljoin

from towerkit.config import config
from towerkit import utils, exceptions
from kubernetes.stream import stream

from tests.api import APITest

@pytest.fixture(scope='class')
def k8s_foreman_sim(gke_client_cscope, request):
    K8sClient = gke_client_cscope(config.credentials)
    prefix = 'foreman-sim'
    cluster_domain = 'services.k8s.tower-qe.testing.ansible.com'
    deployment_name = K8sClient.random_deployment_name(prefix)
    containerspec = [{'name': 'foreman-sim',
                        'image': 'quay.io/ansible/foreman-test-container',
                        'ports': [{'containerPort': 8080, 'protocol': 'TCP'}],
                        'env': [{'name': 'PORT',
                                'value': '8080'}
                                ]}]
    portspec = [{'name': 'foreman-sim',
                 'port': 8080,
                 'protocol': 'TCP',
                 'targetPort': 8080}]
    foremansim_deployment = K8sClient.generate_deployment(deployment_name, containerspec)
    foremansim_service = K8sClient.generate_service(deployment_name, portspec)
    K8sClient.apps.create_namespaced_deployment(body=foremansim_deployment, namespace='default')
    K8sClient.core.create_namespaced_service(body=foremansim_service, namespace='default')
    request.addfinalizer(lambda: K8sClient.destroy(deployment_name))
    sim_url = "https://http-{}-port-8080.{}".format(deployment_name, cluster_domain)
    return sim_url


@pytest.mark.api
@pytest.mark.destructive
@pytest.mark.usefixtures('authtoken', 'install_enterprise_license_unlimited')
class TestForemanSim(APITest):
    def test_foremansim_spawn(self, k8s_foreman_sim):
        import pdb; pdb.set_trace()
    