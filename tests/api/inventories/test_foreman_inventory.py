import fauxfactory
import pytest

from awxkit.config import config

from tests.api import APITest


@pytest.fixture(scope='class')
def k8s_foreman_sim(gke_client_cscope, request):
    pytest.skip("Currently this does not work with the inventory script that is in ansible, more research is needed.")
    # Ostensibly works with the modern plugin
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


@pytest.mark.usefixtures('authtoken')
class TestForemanSim(APITest):

    @pytest.fixture
    def foreman_credential(self, factories, k8s_foreman_sim):
        return factories.credential(name=f'foreman-cred-{fauxfactory.gen_utf8()}',
                                    kind='satellite6', inputs={'host': k8s_foreman_sim})

    @pytest.fixture
    def foreman_inventory_source(self, factories, foreman_credential):
        return factories.inventory_source(name=f'foreman-inventory-source{fauxfactory.gen_utf8()}',
                                          source='satellite6', credential=foreman_credential)

    def test_foreman_inventory_source(self, foreman_inventory_source):
        update = foreman_inventory_source.update()
        update.wait_until_completed().assert_successful()
