from tests.api import APITest
import pytest
from towerkit import utils
from towerkit.config import config
from urllib.parse import urlparse
import requests
import towerkit.exceptions as exc
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
    utils.poll_until(lambda: requests.get(prometheus_url).status_code == 200)
    return prometheus_url


@pytest.mark.mp_group(group="PrometheusMetrics", strategy="isolated_serial")
@pytest.mark.api
@pytest.mark.destructive
@pytest.mark.usefixtures('authtoken', 'install_enterprise_license_unlimited')
class TestMetrics(APITest):

    def query_prometheus(self, prometheus_url, metric):
        query_endpoint = '{}/api/v1/query'.format(prometheus_url)
        params = {'query': metric}
        return int(requests.get(query_endpoint, params=params).json()['data']['result'][0]['value'][1])

    def test_metrics_unreadable_by_unprivileged_user(self, v2, unprivileged_user, user_password):
        with self.current_user(unprivileged_user.username, user_password):
            with pytest.raises(exc.Forbidden):
                v2.metrics.get()

    def test_metrics_unreadable_by_org_users(self, v2, organization_user, user_password):
        with self.current_user(organization_user.username, user_password):
            with pytest.raises(exc.Forbidden):
                v2.metrics.get()

    def test_metrics_readable_by_system_user(self, v2, system_user, user_password):
        with self.current_user(system_user.username, user_password):
            response = v2.metrics.get()
        assert 'awx_system_info' in response

    def test_metrics_counts_incremented_accurately(self, factories, v2, create_venv):
        prometheus_data_before = v2.metrics.get()
        org = factories.organization()
        factories.user(organization=org)
        factories.team(organization=org)
        inventory = factories.inventory(organization=org)
        project = factories.project(organization=org)
        factories.job_template(inventory=inventory, project=project)
        factories.v2_workflow_job_template(organization=org, inventory=inventory, project=project)
        factories.host(inventory=inventory)
        prometheus_data_after = v2.metrics.get()
        assert prometheus_data_after['awx_organizations_total']['value'] == prometheus_data_before['awx_organizations_total']['value'] + 1
        assert prometheus_data_after['awx_inventories_total']['value'] == prometheus_data_before['awx_inventories_total']['value'] + 1
        assert prometheus_data_after['awx_users_total']['value'] == prometheus_data_before['awx_users_total']['value'] + 1
        assert prometheus_data_after['awx_teams_total']['value'] == prometheus_data_before['awx_teams_total']['value'] + 1
        assert prometheus_data_after['awx_projects_total']['value'] == prometheus_data_before['awx_projects_total']['value'] + 1
        assert prometheus_data_after['awx_job_templates_total']['value'] == prometheus_data_before['awx_job_templates_total']['value'] + 1
        assert prometheus_data_after['awx_workflow_job_templates_total']['value'] == prometheus_data_before['awx_workflow_job_templates_total']['value'] + 1
        assert prometheus_data_after['awx_hosts_total']['value'] == prometheus_data_before['awx_hosts_total']['value'] + 1

    def test_metrics_are_readable_by_prometheus(self, factories, v2, k8s_prometheus, skip_if_openshift):
        prometheus_data_before = v2.metrics.get()
        org = factories.organization()
        factories.user(organization=org)
        factories.team(organization=org)
        inventory = factories.inventory(organization=org)
        project = factories.project(organization=org)
        factories.job_template(inventory=inventory, project=project)
        factories.v2_workflow_job_template(organization=org, inventory=inventory, project=project)
        factories.host(inventory=inventory)
        utils.poll_until(lambda: self.query_prometheus(k8s_prometheus, 'awx_hosts_total') > int(prometheus_data_before['awx_hosts_total']['value']), timeout=30)
        assert self.query_prometheus(k8s_prometheus, 'awx_organizations_total') == int(prometheus_data_before['awx_organizations_total']['value'] + 1)
        assert self.query_prometheus(k8s_prometheus, 'awx_inventories_total') == int(prometheus_data_before['awx_inventories_total']['value'] + 1)
        assert self.query_prometheus(k8s_prometheus, 'awx_users_total') == int(prometheus_data_before['awx_users_total']['value'] + 1)
        assert self.query_prometheus(k8s_prometheus, 'awx_teams_total') == int(prometheus_data_before['awx_teams_total']['value'] + 1)
        assert self.query_prometheus(k8s_prometheus, 'awx_projects_total') == int(prometheus_data_before['awx_projects_total']['value'] + 1)
        assert self.query_prometheus(k8s_prometheus, 'awx_job_templates_total') == int(prometheus_data_before['awx_job_templates_total']['value'] + 1)
        assert self.query_prometheus(k8s_prometheus, 'awx_workflow_job_templates_total') == int(prometheus_data_before['awx_workflow_job_templates_total']['value'] + 1)
        assert self.query_prometheus(k8s_prometheus, 'awx_hosts_total') == int(prometheus_data_before['awx_hosts_total']['value'] + 1)
