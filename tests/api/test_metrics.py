from tests.api import APITest
import pytest
from towerkit.utils import logged_sleep
from towerkit.config import config

@pytest.fixture(scope='class')
def k8s_prometheus(gke_client_cscope, request):
    K8sClient = gke_client_cscope(config.credentials)
    prefix = 'prometheus'
    cluster_domain = 'services.k8s.tower-qe.testing.ansible.com'
    deployment_name = K8sClient.random_deployment_name(prefix)
    containerspec = [{'name': '{}-{}'.format(deployment_name, 'app'),
                        'image': 'prom/prometheus',
                        'ports': [{'containerPort': 9090, 'protocol': 'TCP'}],
                        'env': []}]
    portspec = [{'name': 'prometheus',
                     'port': 9090,
                     'protocol': 'TCP',
                     'targetPort': 9090}]
    conjur_deployment = K8sClient.generate_deployment(deployment_name, containerspec)
    conjur_service = K8sClient.generate_service(deployment_name, portspec)
    K8sClient.apps.create_namespaced_deployment(body=conjur_deployment, namespace='default')
    K8sClient.core.create_namespaced_service(body=conjur_service, namespace='default')
    request.addfinalizer(lambda: K8sClient.destroy(deployment_name))
    prometheus_url = "https://http-{}-port-9090.{}".format(deployment_name, cluster_domain)

@pytest.mark.api
@pytest.mark.destructive
@pytest.mark.usefixtures('authtoken', 'install_enterprise_license_unlimited')
class TestMetrics(APITest):
