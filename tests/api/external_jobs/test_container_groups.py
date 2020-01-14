import json

import pytest
import fauxfactory

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
        cred = class_factories.credential(
            credential_type=cred_type,
            inputs={
                'host': client.client.configuration.host,
                'verify_ssl': True,
                'ssl_ca_cert': client.cacrt,
                'bearer_token': client.serviceaccount_token
                }
            )
        ig = class_factories.instance_group(name=f'ContainerGroup - {namespace}')
        ig.credential = cred.id
        ig_options = v2_class.instance_groups.options()
        pod_spec = dict(ig_options.actions['POST']['pod_spec_override']['default'])
        pod_spec['metadata']['namespace'] = namespace
        ig.pod_spec_override = json.dumps(pod_spec)

        return ig, client

    @pytest.fixture(scope='function', params=[
                                            'cacrt',
                                            'token',
                                            'host',
                                            'image',
                                            'role',
                                            'entry_point'
                                            ]
                                        )
    def bad_container_group_and_client(self, request, gke_client_fscope, factories, v2):
        problem = request.param
        client = gke_client_fscope(config.credentials)
        namespace = f'bad-{fauxfactory.gen_alphanumeric().lower()}'
        if problem == 'role':
            client.setup_container_group_namespace(namespace=namespace, corrupt_role=True)
        else:
            client.setup_container_group_namespace(namespace=namespace)
        request.addfinalizer(client.destroy_container_group_namespace)
        cred_type = v2.credential_types.get(namespace='kubernetes_bearer_token').results.pop()
        cacrt = 'blah' if problem == 'cacrt' else client.cacrt
        host = 'broken.example.com' if problem == 'host' else client.client.configuration.host
        token = '230420934823broken928340983240' if problem == 'token' else client.serviceaccount_token
        cred = factories.credential(credential_type=cred_type, inputs={
            'host': host, 'verify_ssl': True, 'ssl_ca_cert': cacrt, 'bearer_token': token}
            )
        ig = factories.instance_group(name=f'ContainerGroup - {namespace}')
        ig.credential = cred.id
        ig_options = v2.instance_groups.options()
        pod_spec = dict(ig_options.actions['POST']['pod_spec_override']['default'])
        pod_spec['metadata']['namespace'] = namespace
        if problem == 'image':
            pod_spec['spec']['containers'][0]['image'] = 'nginx'
        if problem == 'entry_point':
            pod_spec['spec']['containers'][0]['args'] = ['sleep', '10']
        ig.pod_spec_override = json.dumps(pod_spec)

        return ig, client, problem

    @pytest.fixture
    def fscope_container_group_and_client(self, request, gke_client_fscope, factories, v2):
        client = gke_client_fscope(config.credentials)
        namespace = f'fscope-{fauxfactory.gen_alphanumeric().lower()}'
        client.setup_container_group_namespace(namespace=namespace)
        request.addfinalizer(client.destroy_container_group_namespace)
        cred_type = v2.credential_types.get(namespace='kubernetes_bearer_token').results.pop()
        cacrt = client.cacrt
        host = client.client.configuration.host
        token = client.serviceaccount_token
        cred = factories.credential(credential_type=cred_type, inputs={
            'host': host, 'verify_ssl': True, 'ssl_ca_cert': cacrt, 'bearer_token': token}
            )
        ig = factories.instance_group(name=f'ContainerGroup - {namespace}')
        ig.credential = cred.id
        ig_options = v2.instance_groups.options()
        pod_spec = dict(ig_options.actions['POST']['pod_spec_override']['default'])
        pod_spec['metadata']['namespace'] = namespace
        ig.pod_spec_override = json.dumps(pod_spec)

        return ig, client

    def create_pod_resourcequota(self, request, client, namespace, pod_quota):
        resource_quota = client.K8sClient.V1ResourceQuota(spec=client.K8sClient.V1ResourceQuotaSpec(hard={"pods": str(pod_quota)}))
        resource_quota.metadata = client.K8sClient.V1ObjectMeta(namespace=namespace,
        name="pod-quota")
        client.core.create_namespaced_resource_quota(namespace, resource_quota)
        request.addfinalizer(lambda: client.core.delete_namespaced_resource_quota("pod-quota", namespace, body=resource_quota))

    @pytest.mark.github('https://github.com/ansible/awx/issues/4909', ids=['entry_point', 'image'], skip=True)
    def test_container_group_failed_job(self, bad_container_group_and_client, factories):
        container_group, client, problem = bad_container_group_and_client
        jt = factories.job_template(playbook='sleep.yml', extra_vars='{"sleep_interval": 45}')
        jt.add_instance_group(container_group)
        job = jt.launch().wait_until_completed()
        if problem == 'cacrt':
            assert 'SSLError' in job.result_traceback
        elif problem == 'token':
            assert 'Unauthorized' in job.result_traceback
        elif problem == 'host':
            assert 'Name or service not known' in job.result_traceback
        elif problem == 'role':
            assert 'cannot create resource' in job.result_traceback
            assert 'forbidden' in job.result_traceback.lower()
        elif problem == 'image':
            assert 'rsync error' in job.result_traceback
        job.assert_status('error')
        assert job.result_traceback != ''
        assert job.instance_group == container_group.id, "Container group is not indicated that the job tried to run on"

    @pytest.mark.github('https://github.com/ansible/awx/issues/4907', skip=True)
    def test_container_group_launch_project_update(self, container_group_and_client, factories):
        container_group, client = container_group_and_client
        org = factories.organization()
        org.add_instance_group(container_group)
        proj = factories.project(organization=org)
        update = proj.update().wait_until_completed()
        update.assert_successful()
        assert update.execution_node != ""

    @pytest.mark.github('https://github.com/ansible/awx/issues/4907', skip=True)
    def test_container_group_launch_cloud_inventory_update(self, container_group_and_client, aws_inventory_source):
        container_group, client = container_group_and_client
        organization = aws_inventory_source.related.inventory.get().related.organization.get()
        organization.add_instance_group(container_group)
        update = aws_inventory_source.update().wait_until_completed()
        update.assert_successful()
        assert update.execution_node != ""

    def test_container_group_launch_job(self, container_group_and_client, factories):
        container_group, client = container_group_and_client
        inventory = factories.inventory()
        host = inventory.add_host()
        jt = factories.job_template(inventory=inventory)
        jt.add_instance_group(container_group)
        job = jt.launch().wait_until_completed()
        job.assert_successful()
        assert job.instance_group == container_group.id
        assert host.name in job.result_stdout

    def test_container_group_cancel_job(self, container_group_and_client, factories):
        container_group, client = container_group_and_client
        inventory = factories.inventory()
        jt = factories.job_template(inventory=inventory, playbook='sleep.yml', extra_vars='{"sleep_interval": 120}')
        jt.add_instance_group(container_group)
        job = jt.launch().wait_until_status('running')
        job_pod = client.get_job_pod(job.id)
        assert len(job_pod) == 1, f'Did not find expected job pod. Only found {[pod.metadata.name for pod in client.get_pods()]}'
        assert job.instance_group == container_group.id
        job.cancel().wait_until_status('canceled')
        client.assert_job_pod_cleaned_up(job.id)

    @pytest.mark.github('https://github.com/ansible/awx/issues/4908', skip=True)
    def test_container_group_cancel_adhoc(self, container_group_and_client, factories):
        container_group, client = container_group_and_client
        organization = factories.organization()
        organization.add_instance_group(container_group)
        inv = factories.inventory(organization=organization)
        inv.add_host()
        adhoc = factories.ad_hoc_command(inventory=inv, module='command', module_args='sleep 120')
        adhoc.wait_until_status('running')
        job_pod = client.get_job_pod(adhoc.id)
        assert len(job_pod) == 1, f'Did not find expected job pod. Only found {[pod.metadata.name for pod in client.get_pods()]}'
        adhoc.summary_fields.instance_group.id == container_group.id
        adhoc.cancel().wait_until_status('canceled')
        client.assert_job_pod_cleaned_up(adhoc.id)

    def test_container_group_workflow_job(self, container_group_and_client, factories):
        container_group, client = container_group_and_client
        org = factories.organization()
        org.add_instance_group(container_group)
        inventory = factories.inventory(organization=org)
        host = inventory.add_host()
        jt = factories.job_template(inventory=inventory)
        wfjt = factories.workflow_job_template(organization=org)
        factories.workflow_job_template_node(workflow_job_template=wfjt, unified_job_template=jt)
        wf_job = wfjt.launch().wait_until_completed()
        wf_job.assert_successful()
        n1_job_node = wf_job.related.workflow_nodes.get(unified_job_template=jt.id).results.pop()
        n1_job = n1_job_node.wait_for_job().related.job.get()
        assert n1_job.instance_group == container_group.id
        assert host.name in n1_job.result_stdout

    @pytest.mark.github('https://github.com/ansible/awx/issues/4908', skip=True)
    def test_container_group_launch_adhoc(self, container_group_and_client, factories):
        container_group, client = container_group_and_client
        organization = factories.organization()
        organization.add_instance_group(container_group)
        inv = factories.inventory(organization=organization)
        host = inv.add_host()
        adhoc = factories.ad_hoc_command(inventory=inv)
        adhoc.wait_until_completed(timeout=90)
        adhoc.assert_successful()
        adhoc.summary_fields.instance_group.id == container_group.id
        assert host.name in adhoc.result_stdout

    @pytest.mark.github('https://github.com/ansible/awx/issues/4910', skip=True)
    def test_container_group_launch_exceeding_resource_quota(self, request, fscope_container_group_and_client, factories):
        container_group, client = fscope_container_group_and_client
        namespace = json.loads(container_group['pod_spec_override'])['metadata']['namespace']
        self.create_pod_resourcequota(request, client, namespace, 1)
        inventory = factories.inventory()
        inventory.add_host()
        jt = factories.job_template(inventory=inventory, playbook='sleep.yml', extra_vars='{"sleep_interval": 20}', allow_simultaneous=True)
        jt.add_instance_group(container_group)
        job0 = jt.launch().wait_until_started()
        job1 = jt.launch().wait_until_status('pending', timeout=25)
        job0.wait_until_completed()
        job1.wait_until_completed()
        job0.assert_successful()
        job1.assert_successful()

    def test_container_group_sliced_jobs_launch_on_container_groups(self, container_group_and_client, factories):
        ct = 4
        container_group, client = container_group_and_client
        jt = factories.job_template(job_slice_count=ct)
        jt.add_instance_group(container_group)
        inventory = jt.ds.inventory
        for i in range(ct):
            inventory.related.hosts.post(payload=dict(
                name='foo{}'.format(i),
                variables='ansible_connection: local'
            ))
        workflow_job = jt.launch()
        assert workflow_job.type == 'workflow_job'
        nodes = workflow_job.get_related('workflow_nodes').results
        jobs = []
        for node in nodes:
            job = node.wait_for_job().get_related('job')
            job.wait_until_status(['running'])
            jobs.append(job)
            assert job.instance_group == container_group.id
        for job in jobs:
            job.wait_until_completed()
            job.assert_successful()

    def test_container_group_sliced_jobs_run_in_containers(self, container_group_and_client, factories):
        ct = 4
        container_group, client = container_group_and_client
        jt = factories.job_template(job_slice_count=ct, playbook='sleep.yml', extra_vars='{"sleep_interval": 60}')
        jt.add_instance_group(container_group)
        inventory = jt.ds.inventory
        for i in range(ct):
            inventory.related.hosts.post(payload=dict(
                name='foo{}'.format(i),
                variables='ansible_connection: local'
            ))
        workflow_job = jt.launch()
        assert workflow_job.type == 'workflow_job'
        nodes = workflow_job.get_related('workflow_nodes').results
        jobs = []
        for node in nodes:
            job = node.wait_for_job().get_related('job')
            job.wait_until_status(['running'])
            jobs.append(job)
        try:
            for job in jobs:
                job_pod = client.get_job_pod(job.id)
                assert len(job_pod) == 1, f'Did not find expected job pod. Only found {[pod.metadata.name for pod in client.get_pods()]}'
        finally:
            workflow_job.cancel()
            workflow_job.wait_until_completed()

    @pytest.mark.github('https://github.com/ansible/awx/issues/4910', skip=True)
    def test_container_group_sliced_jobs_exceeding_resource_quota(self, request, fscope_container_group_and_client, factories):
        ct = 4
        container_group, client = fscope_container_group_and_client
        namespace = json.loads(container_group['pod_spec_override'])['metadata']['namespace']
        self.create_pod_resourcequota(request, client, namespace, ct // 2)
        jt = factories.job_template(job_slice_count=ct, playbook='sleep.yml', extra_vars='{"sleep_interval": 15}')
        jt.add_instance_group(container_group)
        inventory = jt.ds.inventory
        for i in range(ct):
            inventory.related.hosts.post(payload=dict(
                name='foo{}'.format(i),
                variables='ansible_connection: local'
            ))
        workflow_job = jt.launch()
        assert workflow_job.type == 'workflow_job'
        nodes = workflow_job.get_related('workflow_nodes').results
        jobs = []
        for node in nodes:
            job = node.wait_for_job().get_related('job')
            jobs.append(job)
        queued_jobs = []
        for job in jobs:
            job.assert_status(['running', 'pending', 'waiting'])
            if job.get().status in ['pending', 'waiting']:
                queued_jobs.append(job)
        try:
            for job in queued_jobs:
                job.wait_until_completed()
                job.assert_successful()
        finally:
            workflow_job.cancel()
            workflow_job.wait_until_completed()
