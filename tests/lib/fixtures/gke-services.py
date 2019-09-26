import pytest
import googleapiclient.discovery
import kubernetes.client
import base64
from google.oauth2 import service_account
import fauxfactory


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
        self.namespace = namespace
        self.namespaceobject = kubernetes.client.V1Namespace(metadata={'name': self.namespace})
        self.serviceaccountobject = kubernetes.client.V1ServiceAccount(metadata={'name': self.serviceaccount})
        pod_verbs = ["get", "list", "watch", "create", "update", "patch", "delete"]
        pod_exec_verbs = ["create"]
        pod_rules = kubernetes.client.V1PolicyRule(api_groups=[""], resources=["pods"], verbs=pod_verbs)
        pod_exec_rules = kubernetes.client.V1PolicyRule(api_groups=[''], resources=['pods/exec'], verbs=pod_exec_verbs)
        self.roleobject = kubernetes.client.V1Role(rules=[pod_rules, pod_exec_rules], metadata={'name': self.role})
        role_subject = kubernetes.client.V1Subject(name=self.serviceaccount, kind='ServiceAccount')
        role_ref = kubernetes.client.V1RoleRef(name=self.role, kind='Role', api_group='rbac.authorization.k8s.io')
        self.rolebindobject = kubernetes.client.V1RoleBinding(metadata={'name': f'{namespace}-{self.role}-rolebind'}, subjects=[role_subject], role_ref=role_ref)

        # Actually create these items
        self.core.create_namespace(self.namespaceobject)
        self.core.create_namespaced_service_account(namespace, self.serviceaccountobject)
        if not corrupt_role:
            self.rbac.create_namespaced_role(namespace, self.roleobject)
            self.rbac.create_namespaced_role_binding(namespace, self.rolebindobject)
        secrets = self.core.list_namespaced_secret(namespace)
        tokens = [token.data['token'] for token in secrets.items if token.metadata.namespace == namespace and token.metadata.annotations.get('kubernetes.io/service-account.name') == self.serviceaccount]
        assert len(tokens) == 1
        token = base64.decodebytes(tokens.pop().encode()).decode(encoding='utf-8')
        self.serviceaccount_token = token

    def destroy_container_group_namespace(self, namespace=None):
        """Delete created items for container groups setup.

        Optionally, delete different namespace and all dependent objects. (useful in development)
        """
        if namespace:
            self.core.delete_namespace(namespace, body=kubernetes.client.V1DeleteOptions(), propagation_policy='Background')
            return
        if hasattr(self, 'namespaceobject'):
            self.core.delete_namespace(self.namespaceobject.metadata['name'], body=kubernetes.client.V1DeleteOptions(), propagation_policy='Background')


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
