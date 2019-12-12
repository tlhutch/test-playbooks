import json

import pytest
import googleapiclient.discovery
import kubernetes.client
import base64
from google.oauth2 import service_account
import fauxfactory

from awxkit.config import config
from awxkit import utils
from awxkit import exceptions as exc


class K8sClient(object):
    def __init__(self, client):
        self.client = client
        self.K8sClient = kubernetes.client
        self.apps = kubernetes.client.AppsV1Api(self.client)
        self.core = kubernetes.client.CoreV1Api(self.client)
        self.rbac = kubernetes.client.RbacAuthorizationV1Api(self.client)
        self.storage = kubernetes.client.StorageV1Api(self.client)
        self.deploymentobject = kubernetes.client.V1Deployment()
        self.serviceobject = kubernetes.client.V1Service()
        self.secretobject = kubernetes.client.V1Secret()
        self.configmapobject = kubernetes.client.V1ConfigMap
        self.objectmeta = kubernetes.client.V1ObjectMeta

    def generate_deployment(self, deploymentname, containerspec):
        deployment = self.deploymentobject
        deployment.api_version = 'apps/v1'
        deployment.metadata = {'name': deploymentname,
                               'labels': {'integration': 'True'}}
        deployment.spec = {}
        deployment.spec['selector'] = {'matchLabels': {'run': deploymentname}}
        deployment.spec['template'] = {}
        deployment.spec['template']['metadata'] = {'labels': {'run': deploymentname}}
        deployment.spec['template']['spec'] = {'containers': containerspec}

        return deployment

    def random_deployment_name(self, prefix):
        return '{}-{}'.format(prefix, fauxfactory.gen_string('alphanumeric', 5)).lower()

    def generate_service(self, deploymentname, portspec):
        service = self.serviceobject
        service.api_version = 'v1'
        service.metadata = {'name': deploymentname,
                            'labels': {'run': deploymentname,
                                       'integration': 'True'}}
        service.spec = {}
        service.spec['ports'] = portspec
        service.spec['selector'] = {'run': deploymentname}
        service.spec['type'] = 'NodePort'

        return service

    def destroy(self, deploymentname):
        self.core.delete_namespaced_service(deploymentname, 'default', body=kubernetes.client.V1DeleteOptions())
        self.apps.delete_namespaced_deployment(deploymentname, 'default', body=kubernetes.client.V1DeleteOptions())

    def setup_container_group_namespace(self, namespace, corrupt_role=False):
        """Set up necessary namespace, service account, and role for use in a ContainerGroup.

        :params:
            namespace: <str> name of namespace
            corrupt_role: <bool> if true, intentionally provide inadequate role to service account
        """
        # Prepare objects
        self.serviceaccount = f'serviceaccount-{namespace}'
        self.role = f'serviceaccount-role-{namespace}'
        self.nsmeta = kubernetes.client.V1ObjectMeta(labels=dict(integration='True'),
                                    name=namespace)
        self.namespaceobject = kubernetes.client.V1Namespace(metadata=self.nsmeta)
        self.sameta = kubernetes.client.V1ObjectMeta(labels=dict(integration='True'),
                                    name=self.serviceaccount)
        self.serviceaccountobject = kubernetes.client.V1ServiceAccount(metadata=self.sameta)
        pod_verbs = ["get", "list", "watch", "create", "update", "patch", "delete"]
        pod_exec_verbs = ["create"]
        pod_rules = kubernetes.client.V1PolicyRule(api_groups=[""], resources=["pods"], verbs=pod_verbs)
        pod_exec_rules = kubernetes.client.V1PolicyRule(api_groups=[''], resources=['pods/exec'], verbs=pod_exec_verbs)
        self.rometa = kubernetes.client.V1ObjectMeta(labels=dict(integration='True'),
                                    name=self.role)
        self.roleobject = kubernetes.client.V1Role(rules=[pod_rules, pod_exec_rules], metadata=self.rometa)
        role_subject = kubernetes.client.V1Subject(name=self.serviceaccount, kind='ServiceAccount')
        role_ref = kubernetes.client.V1RoleRef(name=self.role, kind='Role', api_group='rbac.authorization.k8s.io')
        self.robmeta = kubernetes.client.V1ObjectMeta(labels=dict(integration='True'),
                                    name=f'{namespace}-{self.role}-rolebind')
        self.rolebindobject = kubernetes.client.V1RoleBinding(metadata=self.robmeta, subjects=[role_subject], role_ref=role_ref)
        self.limitrangeobject = kubernetes.client.V1LimitRange(spec=dict({"limits":[{"defaultRequest": {"cpu": "100m"}, "type": "Container"}]}))

        # Actually create these items
        self.core.create_namespace(self.namespaceobject)
        self.core.create_namespaced_limit_range(namespace, self.limitrangeobject)
        self.core.create_namespaced_service_account(namespace, self.serviceaccountobject)
        if not corrupt_role:
            self.rbac.create_namespaced_role(namespace, self.roleobject)
            self.rbac.create_namespaced_role_binding(namespace, self.rolebindobject)
        secrets = self.core.list_namespaced_secret(namespace)
        tokens = [token.data['token'] for token in secrets.items if token.metadata.namespace == namespace and token.metadata.annotations.get('kubernetes.io/service-account.name') == self.serviceaccount]
        assert len(tokens) == 1
        token = base64.decodebytes(tokens.pop().encode()).decode(encoding='utf-8')
        self.serviceaccount_token = token

    def assert_job_pod_cleaned_up(self, job_id, namespace=None, timeout=30):
        try:
            utils.poll_until(lambda: len(self.get_job_pod(job_id, namespace=namespace)) == 0, timeout=timeout)
        except exc.WaitUntilTimeout:
            raise AssertionError(f'Job {job_id} left job pod in namespace')

    def get_pods(self, namespace=None):
        namespace = namespace if namespace else self.namespaceobject.metadata.name
        return self.core.list_namespaced_pod(namespace)

    def get_job_pod(self, job_id, namespace=None, timeout=30):
        def _get_job_pod():
            pods = self.get_pods(namespace)
            return [pod for pod in pods.items if pod.metadata.name == f'awx-job-{job_id}']
        try:
            utils.poll_until(lambda: len(_get_job_pod()) == 1, timeout=timeout)
        except exc.WaitUntilTimeout:
            pass
        return _get_job_pod()

    def wait_until_num_pods_in_namespace(self, namespace=None, num_pods=0, timeout=120):
        try:
            utils.poll_until(lambda: len(self.get_pods(namespace).items) == num_pods, timeout=timeout)
        except exc.WaitUntilTimeout:
            pass
        pods = self.get_pods(namespace)
        running_pods = [{'pod-name': pod.metadata.name, 'pod-namespace': pod.metadata.namespace} for pod in pods.items]
        return running_pods

    def assert_num_pods_in_namespace(self, namespace=None, num_pods=0, timeout=120):
        pods = self.wait_until_num_pods_in_namespace(namespace=namespace, num_pods=num_pods, timeout=timeout)
        assert len(pods) == num_pods, pods

    def destroy_container_group_namespace(self, assert_no_hanging_pods=False, namespace=None):
        """Delete created items for container groups setup.

        By default, before destroying namespace assert there are no remaining pods.

        All jobs should be completed/canceled by the time this runs. If there are any hanging pods it is because
        we did not clean up.

        Optionally, delete different namespace and all dependent objects. (useful in development)
        """
        namespace = namespace if namespace else self.namespaceobject.metadata.name
        if assert_no_hanging_pods:
            try:
                self.assert_num_pods_in_namespace(namespace=namespace)
            finally:
                pass
        self.core.delete_namespace(namespace, body=kubernetes.client.V1DeleteOptions(), propagation_policy='Background')


def create_gke_client():
    def create_client(credentials):
        sa_creds = service_account.Credentials.from_service_account_info(credentials['cloud']['gke']['serviceaccount']['key'])
        gke = googleapiclient.discovery.build('container', 'v1', credentials=sa_creds, cache_discovery=False)
        name = credentials['cloud']['gke']['cluster']
        gke_clusters = gke.projects().locations().clusters()
        gke_cluster = gke_clusters.get(name=name).execute()
        kube_config = kubernetes.client.Configuration()
        kube_config.host = 'https://{}'.format(gke_cluster['endpoint'])
        kube_config.verify_ssl = True
        kube_config.api_key['authorization'] = credentials['cloud']['gke']['api_key']
        kube_config.api_key_prefix['authorization'] = 'Bearer'
        kube_config.ssl_ca_cert = '/tmp/ssl_ca_cert'
        cacrt = base64.decodebytes(gke_cluster['masterAuth']['clusterCaCertificate'].encode())
        with open(kube_config.ssl_ca_cert, 'wb') as f:
            f.write(cacrt)
        client = kubernetes.client.ApiClient(configuration=kube_config)
        k8sclient = K8sClient(client)
        k8sclient.cacrt = cacrt.decode(encoding='utf-8')
        return k8sclient
    return create_client


@pytest.fixture
def gke_client_fscope():
    return create_gke_client()


@pytest.fixture(scope='class')
def gke_client_cscope():
    return create_gke_client()


@pytest.fixture(scope='session')
def gke_client_session_scope():
    return create_gke_client()


@pytest.fixture(scope='session')
def session_container_group(session_subrequest, gke_client_session_scope, session_factories, v2_session):
    client = gke_client_session_scope(config.credentials)
    namespace = f'session-container-group-{fauxfactory.gen_alphanumeric().lower()}'
    client.setup_container_group_namespace(namespace=namespace)
    session_subrequest.addfinalizer(client.destroy_container_group_namespace)
    cred_type = v2_session.credential_types.get(namespace='kubernetes_bearer_token').results.pop()
    cred = session_factories.credential(
        credential_type=cred_type,
        inputs={
            'host': client.client.configuration.host,
            'verify_ssl': True,
            'ssl_ca_cert': client.cacrt,
            'bearer_token': client.serviceaccount_token
            }
        )
    ig = session_factories.instance_group(name=f'ContainerGroup - {namespace}')
    ig.credential = cred.id
    ig_options = v2_session.instance_groups.options()
    pod_spec = dict(ig_options.actions['POST']['pod_spec_override']['default'])
    pod_spec['metadata']['namespace'] = namespace
    ig.pod_spec_override = json.dumps(pod_spec)

    return ig
