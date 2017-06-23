import json
import os
import re

import pytest

from tests.api import Base_Api_Test
from towerkit import utils, exceptions


@pytest.mark.api
@pytest.mark.skip_selenium
class Test_Instance_Groups(Base_Api_Test):

    pytestmark = pytest.mark.usefixtures('authtoken', 'install_enterprise_license_unlimited')

    @pytest.mark.ha_tower
    def test_instance_group_creation(self, authtoken, v2, ansible_runner):
        inventory_path = os.environ.get('TQA_INVENTORY_FILE_PATH', '/tmp/setup/inventory')
        cmd = 'scripts/ansible_inventory_to_json.py --inventory {0} --group-filter tower,instance_group_'.format(inventory_path)
        contacted = ansible_runner.script(cmd)
        assert len(contacted.values()) == 1, "Failed to run script against Tower instance"

        group_mapping = json.loads(contacted.values().pop()['stdout'])
        for group in group_mapping.keys():
            match = re.search('instance_group_(.*)', group)
            if match:
                group_mapping[match.group(1)] = group_mapping.pop(group)

        instance_groups = [group.name for group in v2.instance_groups.get().results]
        assert len(instance_groups) == len(group_mapping.keys())
        assert set(instance_groups) == set(group_mapping.keys())

        for group in v2.instance_groups.get().results:
            instances = [instance.hostname for instance in group.get_related('instances').results]
            assert len(instances) == len(group_mapping[group.name])
            assert set(instances) == set(group_mapping[group.name])

    @pytest.mark.ha_tower
    @pytest.mark.parametrize('resource', ['job_template', 'inventory', 'organization'])
    def test_job_template_executes_on_assigned_instance_group(self, v2, factories, resource):
        def get_resource(jt, resource):
            if resource == 'job_template':
                return jt
            elif resource == 'inventory':
                return jt.ds.inventory
            elif resource == 'organization':
                return jt.ds.inventory.ds.organization
            else:
                raise ValueError("Unsupported resource: {0}".format(resource))

        instance_groups = v2.instance_groups.get().results
        project = factories.project()  # use the same project to save time
        job_template_to_instance_group_map = []
        for ig in instance_groups:
            jt = factories.job_template(project=project)
            with utils.suppress(exceptions.NoContent):
                get_resource(jt, resource).get_related('instance_groups').post(dict(id=ig.id))
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
