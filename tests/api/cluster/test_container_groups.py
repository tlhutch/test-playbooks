import json

import pytest
import fauxfactory

import awxkit.exceptions as exc
from awxkit.config import config
from tests.api import APITest


class TestContainerGroups(APITest):

    @pytest.fixture(scope='class')
    def container_group_and_client(self, request, gke_client_cscope, class_factories, v2_class):
        client = gke_client_cscope(config.credentials)
        namespace = fauxfactory.gen_alphanumeric().lower()
        client.setup_container_group_namespace(namespace=namespace)
        request.addfinalizer(client.destroy_container_group_namespace)
        cred_type = v2_class.credential_types.get(namespace='kubernetes_bearer_token').results.pop()
        cred = class_factories.credential(credential_type=cred_type, inputs={'host': client.client.configuration.host, 'verify_ssl': True, 'ssl_ca_cert': client.cacrt, 'bearer_token': client.serviceaccount_token})
        ig = class_factories.instance_group(name=f'ContainerGroup - {namespace}')
        ig.credential = cred.id
        pod_spec = {
            "apiVersion": "v1",
            "kind": "Pod",
            "metadata": {
             "namespace": namespace
            },
            "spec": {
             "containers": [
              {
               "args": [
                "sleep",
                "infinity"
               ],
               "image": "gcr.io/ansible-tower-engineering/awx-runner",
               "imagePullPolicy": "Always",
               "stdin": True,
               "tty": True
              }
             ]
            }
        }
        ig.pod_spec_override = json.dumps(pod_spec)

        return ig, client

    def test_launch_job(self, container_group_and_client, factories):
        container_group, client = container_group_and_client
        jt = factories.job_template()
        with pytest.raises(exc.NoContent):
            jt.related.instance_groups.post(dict(id=container_group.id, associate=True))
        # TODO use sleep playbook and confirm a pod spins up on gke using client
        job = jt.launch().wait_until_completed()
        job.assert_successful()
