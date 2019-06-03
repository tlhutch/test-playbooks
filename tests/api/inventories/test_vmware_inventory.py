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