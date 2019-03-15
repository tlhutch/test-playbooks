import pytest
import googleapiclient.discovery
import kubernetes.client
import base64
from google.oauth2 import service_account


def create_gke_clients():
    def create_clients(credentials):
        sa_creds = service_account.Credentials.from_service_account_info(credentials['cloud']['gke']['serviceaccount']['key'])
        gke = googleapiclient.discovery.build('container', 'v1', credentials=sa_creds)
        name = credentials['cloud']['gke']['cluster']
        gke_clusters = gke.projects().locations().clusters()
        gke_cluster = gke_clusters.get(name=name).execute()
        kube_config = kubernetes.client.Configuration()
        kube_config.host = 'https://{}'.format(gke_cluster['endpoint'])
        kube_config.verify_ssl = True
        kube_config.api_key['authorization'] = credentials['cloud']['gke']['api_key']
        kube_config.api_key_prefix['authorization'] = 'Bearer'
        kube_config.ssl_ca_cert = '/tmp/ssl_ca_cert'
        with open(kube_config.ssl_ca_cert, 'wb') as f:
            f.write(base64.decodestring(gke_cluster['masterAuth']['clusterCaCertificate'].encode()))
        client = kubernetes.client.ApiClient(configuration=kube_config)
        return kubernetes.client.AppsV1Api(client), kubernetes.client.CoreV1Api(client)
    return create_clients


@pytest.fixture
def gke_client_fscope():
    return create_gke_clients()


@pytest.fixture(scope='class')
def gke_client_cscope():
    return create_gke_clients()
