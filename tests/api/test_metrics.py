from tests.api import APITest
import pytest
from towerkit.utils import logged_sleep
from towerkit.config import config
from urllib.parse import urlparse
import jinja2


@pytest.fixture(scope='class')
def k8s_prometheus(gke_client_cscope, request, class_factories):
    auditor = class_factories.user(is_system_auditor=True)
    token = class_factories.access_token(user=auditor, oauth_2_application=True)
    templateLoader = jinja2.FileSystemLoader(searchpath="./scripts/kubernetes/templates/")
    templateEnv = jinja2.Environment(loader=templateLoader)
    template = templateEnv.get_template('prometheus.yml.j2')
    tower_hostname = urlparse(config.base_url).netloc
    prometheus_config = template.render(bearer_token=token.token, tower_hostname=tower_hostname)
    K8sClient = gke_client_cscope(config.credentials)
    prefix = 'prometheus'
    cluster_domain = 'services.k8s.tower-qe.testing.ansible.com'
    deployment_name = K8sClient.random_deployment_name(prefix)

    metadata = K8sClient.objectmeta(annotations=dict(app=deployment_name),
                                    deletion_grace_period_seconds=30,
                                    labels=dict(app=deployment_name, integration='True'),
                                    name=deployment_name,
                                    namespace='default')
    configmap_object = K8sClient.configmapobject(api_version='v1',
                                          kind='ConfigMap',
                                          data={'prometheus.yml': prometheus_config},
                                          metadata=metadata)
    K8sClient.core.create_namespaced_config_map('default', configmap_object)

    containerspec = [{'name': '{}-{}'.format(deployment_name, 'app'),
                      'image': 'prom/prometheus',
                      'ports': [{'containerPort': 9090, 'protocol': 'TCP'}],
                      'env': [],
                      'command': ['prometheus'],
                      'volumeMounts': [{'name': '{}-config'.format(deployment_name), 'mountPath': '/prometheus/prometheus.yml', 'subPath': 'prometheus.yml'}]
                      }]
    portspec = [{'name': 'prometheus',
                     'port': 9090,
                     'protocol': 'TCP',
                     'targetPort': 9090}]
    prometheus_deployment = K8sClient.generate_deployment(deployment_name, containerspec)
    prometheus_deployment.spec['template']['spec']['volumes'] = [{'name': '{}-config'.format(deployment_name), 'configMap': {'name': deployment_name, 'items': [{'key': 'prometheus.yml', 'path': 'prometheus.yml'}]}}]
    prometheus_service = K8sClient.generate_service(deployment_name, portspec)
    K8sClient.apps.create_namespaced_deployment(body=prometheus_deployment, namespace='default')
    K8sClient.core.create_namespaced_service(body=prometheus_service, namespace='default')
    request.addfinalizer(lambda: K8sClient.destroy(deployment_name))
    request.addfinalizer(lambda: K8sClient.core.delete_namespaced_config_map(deployment_name, 'default', body=K8sClient.K8sClient.V1DeleteOptions()))
    prometheus_url = "https://http-{}-port-9090.{}".format(deployment_name, cluster_domain)
    logged_sleep(5)
    return prometheus_url


@pytest.mark.api
@pytest.mark.destructive
@pytest.mark.usefixtures('authtoken', 'install_enterprise_license_unlimited')
class TestMetrics(APITest):
    def test_placeholder():
        pass
