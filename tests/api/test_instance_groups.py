import json
import os
import random
import re

import pytest

from tests.api import Base_Api_Test
from towerkit import utils
from towerkit.api import Connection, ApiV2


def v2_from_domain(domain, secure=True):
    protocol = 'https' if secure else 'http'
    conn = Connection('{}://{}'.format(protocol, domain))
    api = ApiV2(conn)
    api.load_default_authtoken()
    return api


@pytest.mark.api
@pytest.mark.skip_selenium
@pytest.mark.usefixtures('authtoken', 'install_enterprise_license_unlimited')
class TestInstanceGroups(Base_Api_Test):

    @staticmethod
    def get_resource(jt, resource):
        if resource == 'job_template':
            return jt
        elif resource == 'inventory':
            return jt.ds.inventory
        elif resource == 'organization':
            return jt.ds.inventory.ds.organization
        else:
            raise ValueError("Unsupported resource: {0}".format(resource))

    def test_instance_group_creation(self, authtoken, v2, ansible_runner):
        inventory_path = os.environ.get('TQA_INVENTORY_FILE_PATH', '/tmp/setup/inventory')
        cmd = 'scripts/ansible_inventory_to_json.py --inventory {0} --group-filter tower,instance_group_,isolated_group_'.format(inventory_path)
        contacted = ansible_runner.script(cmd)
        assert len(contacted.values()) == 1, "Failed to run script against Tower instance"

        group_mapping = json.loads(contacted.values().pop()['stdout'])
        for group in group_mapping.keys():
            match = re.search('(instance_group_|isolated_group_)(.*)', group)
            if match:
                group_mapping[match.group(2)] = group_mapping.pop(group)

        instance_groups = [group.name for group in v2.instance_groups.get().results]
        assert len(instance_groups) == len(group_mapping.keys())
        assert set(instance_groups) == set(group_mapping.keys())

        for group in v2.instance_groups.get().results:
            instances = [instance.hostname for instance in group.get_related('instances').results]
            assert len(instances) == len(group_mapping[group.name])
            assert set(instances) == set(group_mapping[group.name])

    @pytest.mark.requires_ha
    @pytest.mark.parametrize('resource', ['job_template', 'inventory', 'organization'])
    def test_job_template_executes_on_assigned_instance_group(self, v2, factories, resource):
        instance_groups = v2.instance_groups.get().results
        project = factories.v2_project()  # use the same project to save time
        job_template_to_instance_group_map = []
        for ig in instance_groups:
            jt = factories.v2_job_template(project=project)
            self.get_resource(jt, resource).add_instance_group(ig)
            job_template_to_instance_group_map.append((jt, ig))

        for jt, _ in job_template_to_instance_group_map:
            jt.launch()
        for jt, _ in job_template_to_instance_group_map:
            jt.wait_until_completed()

        for jt, ig in job_template_to_instance_group_map:
            job = jt.get_related('last_job')
            assert job.instance_group == ig.id, "Job instance group differs from job template instance group"

            execution_host = job.execution_node
            instances = ig.get_related('instances').results
            assert any(execution_host in instance.hostname for instance in instances), \
                "Job not run on instance in assigned instance group"

    @pytest.mark.requires_ha
    @pytest.mark.requires_isolation
    @pytest.mark.parametrize('base_resource, parent_resource', [('job_template', 'inventory'), ('job_template', 'organization'), ('inventory', 'organization')])
    def test_instance_group_hierarchy(self, v2, factories, base_resource, parent_resource):
        assert not len(v2.jobs.get(status='running').results), "Test requires Tower to not have any running jobs"

        instance_groups = sorted(v2.instance_groups.get().results, key=lambda x: x.instances)
        if len(instance_groups) == 1:
            pytest.skip('Test requires multiple instance groups')

        def mutually_exclusive_instance_groups():
            instance_group_to_instances_map = [(instance_group, set([instance.id for instance in instance_group.get_related('instances').results]))
                                               for instance_group in instance_groups]
            for first in instance_group_to_instances_map:
                for second in instance_group_to_instances_map:
                    if not (first[1] & second[1]):
                        return first[0], second[0]
            pytest.skip("Unable to find two mutually exclusive instance groups")

        base_instance_group, parent_instance_group = mutually_exclusive_instance_groups()
        jt = factories.v2_job_template(playbook='sleep.yml', extra_vars=dict(sleep_interval=600), allow_simultaneous=True)
        factories.v2_host(inventory=jt.ds.inventory)

        self.get_resource(jt, base_resource).add_instance_group(base_instance_group)
        self.get_resource(jt, parent_resource).add_instance_group(parent_instance_group)

        instance_group_to_hostnames_map = {instance_group.id: [instance.hostname for instance in instance_group.get_related('instances').results]
                                           for instance_group in instance_groups}
        while True:
            job = jt.launch()
            utils.poll_until(lambda: getattr(job.get(), 'execution_node') != '', interval=10, timeout=120)
            if job.execution_node in instance_group_to_hostnames_map[base_instance_group.id]:
                assert base_instance_group.get().percent_capacity_remaining >= 0
            else:
                break
        assert job.execution_node in instance_group_to_hostnames_map[parent_instance_group.id]
        assert parent_instance_group.get().consumed_capacity > \
            base_instance_group.capacity - base_instance_group.consumed_capacity

    @pytest.mark.requires_ha
    @pytest.mark.requires_isolation
    def test_job_run_against_isolated_node_ensure_viewable_from_all_nodes(self, ansible_module_cls, factories, user_password, v2):
        manager = ansible_module_cls.inventory_manager
        hosts = manager.get_group_dict().get('tower')
        managed = manager.get_group_dict().get('managed_hosts')[0]
        protected = v2.instance_groups.get(name='protected').results[0]

        username = manager.get_host(managed).get_vars().get('ansible_user')
        cred = factories.v2_credential(username=username, password=user_password)
        host = factories.host(name=managed, variables=dict(ansible_host=managed))
        jt = factories.v2_job_template(inventory=host.ds.inventory, credential=cred)
        jt.add_instance_group(protected)
        jt.launch().wait_until_completed()

        # update the job template and fetch the id of the job that just ran
        job = jt.get().get_related('last_job')
        job_id = job.id
        assert not job.failed

        # as the job ran on another node, fetch the standard out
        job.related.stdout.get(format='txt_download')
        stdout = job.get().result_stdout

        # assert the managed host appears in the output, ensuring the job ran
        # on the machine we specified
        assert managed in stdout
        # strip line endings and empty lines because output format varies
        canonical_stdout = [line for line in stdout.splitlines() if line]

        for host in hosts:
            api = v2_from_domain(host)
            job = api.get().jobs.get(id=job_id).results[0]
            assert not job.failed

            job.related.stdout.get(format='txt_download')
            stdout = [line for line in job.get().result_stdout.splitlines() if line]
            assert stdout == canonical_stdout

    @pytest.mark.requires_isolation
    @pytest.mark.parametrize('run_on_isolated_group', [True, False], ids=['isolated group', 'regular instance group'])
    def test_capacity(self, factories, v2, run_on_isolated_group):
        ig_filter = dict(name='protected') if run_on_isolated_group else dict(not__name='protected')
        ig = random.choice(v2.instance_groups.get(**ig_filter).results)
        # Ensure no capacity consumed initially
        utils.poll_until(lambda: ig.get().consumed_capacity == 0, interval=10, timeout=60)

        host = factories.v2_host()
        jt = factories.v2_job_template(inventory=host.ds.inventory, playbook='sleep.yml', extra_vars=dict(sleep_interval=600), allow_simultaneous=True)
        jt.add_instance_group(ig)

        previous_ig_consumed_capacity = 0
        for _ in range(3):
            job = jt.launch().wait_until_status('running')
            utils.poll_until(lambda: getattr(job.get(), 'execution_node') != '', interval=10, timeout=45)

            # Capacity should increase after each job launch
            assert ig.get().consumed_capacity > previous_ig_consumed_capacity
            previous_ig_consumed_capacity = ig.consumed_capacity
            assert ig.percent_capacity_remaining == round(float(ig.capacity - ig.consumed_capacity) * 100 / ig.capacity, 1)
            instance = [i for i in ig.get_related('instances').results if i.hostname == job.execution_node][0]

            assert instance.get().consumed_capacity > 0
            assert instance.percent_capacity_remaining == round(float(instance.capacity - instance.consumed_capacity) * 100 / instance.capacity, 1)
