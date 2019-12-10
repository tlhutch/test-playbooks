import fauxfactory
import pytest
import requests

from awxkit.config import config
from awxkit import utils

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
    sim_fqdn = "https-{}-port-443.{}".format(deployment_name, cluster_domain)

    sess = requests.Session()
    utils.poll_until(lambda: sess.get('{}/spawn?username=user&password=pass&cluster=1&port=443&vm=5'.format(controller_url)).status_code == 200, interval=5, timeout=20)
    return sim_fqdn


@pytest.mark.usefixtures('authtoken')
class TestGovcsim(APITest):

    @pytest.fixture
    def vmware_credential(self, factories, k8s_govcsim):
        return factories.credential(name=f'vmware-cred-{fauxfactory.gen_utf8()}',
                                    kind='vmware', inputs={'host': k8s_govcsim})

    @pytest.fixture
    def vmware_inventory_source(self, factories, vmware_credential):
        return factories.inventory_source(name=f'vmware-inventory-source{fauxfactory.gen_utf8()}',
                                          source='vmware', credential=vmware_credential)

    @pytest.mark.github('https://github.com/ansible/awx/issues/4156', skip=True)
    def test_vmware_inventory_source(self, vmware_inventory_source):
        update = vmware_inventory_source.update()
        update.wait_until_completed().assert_successful()
