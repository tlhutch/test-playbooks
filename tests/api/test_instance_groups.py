import json
import os
import re

import pytest

from tests.api import Base_Api_Test
from towerkit import utils


@pytest.mark.api
@pytest.mark.skip_selenium
class Test_Instance_Groups(Base_Api_Test):

    pytestmark = pytest.mark.usefixtures('authtoken', 'install_enterprise_license_unlimited')

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
