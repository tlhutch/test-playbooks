import json
import logging
import os
import random
import re
import subprocess
import time

import pytest

from tests.api import Base_Api_Test
from towerkit import utils
from towerkit.api import Connection

log = logging.getLogger(__name__)


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

    def mutually_exclusive_instance_groups(self, instance_groups):
        instance_group_to_instances_map = [(instance_group, set([instance.id for instance in instance_group.get_related('instances').results]))
                                           for instance_group in instance_groups]
        for first in instance_group_to_instances_map:
            for second in instance_group_to_instances_map:
                if not (first[1] & second[1]):
                    return first[0], second[0]
        pytest.skip("Unable to find two mutually exclusive instance groups")

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
        job_template_to_instance_group_map = []
        for ig in instance_groups:
            jt = factories.v2_job_template()
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

        base_instance_group, parent_instance_group = self.mutually_exclusive_instance_groups(instance_groups)
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
    def test_job_run_against_isolated_node_ensure_viewable_from_all_nodes(self, ansible_module_cls, factories,
                                                                          admin_user, user_password, v2):
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
            connection = Connection('https://' + host)
            connection.login(admin_user.username, admin_user.password)
            with self.current_instance(connection, v2):
                job = v2.get().jobs.get(id=job_id).results[0]
                assert not job.failed

                job.related.stdout.get(format='txt_download')
                stdout = [line for line in job.get().result_stdout.splitlines() if line]
                assert stdout == canonical_stdout

    @pytest.mark.requires_isolation
    def test_capacity_when_no_jobs_running(self, v2):
        for ig in v2.instance_groups.get().results:
            utils.poll_until(lambda: ig.get().jobs_running == 0, interval=10, timeout=120)
            assert ig.consumed_capacity == 0
            assert ig.capacity > 0
            assert ig.percent_capacity_remaining == 100

            for instance in ig.get_related('instances').results:
                utils.poll_until(lambda: instance.get().jobs_running == 0, interval=10, timeout=60)
                assert instance.consumed_capacity == 0
                assert instance.capacity > 0
                assert instance.percent_capacity_remaining == 100

    @pytest.mark.requires_ha
    @pytest.mark.requires_isolation
    @pytest.mark.parametrize('run_on_isolated_group', [True, False], ids=['isolated group', 'regular instance group'])
    def test_running_jobs_consume_capacity(self, factories, v2, run_on_isolated_group):
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

    @pytest.mark.requires_ha
    @pytest.mark.requires_isolation
    def test_instance_removal(self, admin_user, ansible_module_cls, factories, user_password, v2):
        """
        This test checks the behaviour of a cluster as nodes are removed and restored.

        For each node in the 'tower' instance group:

        * A long running job is started assigned to run on the node
        * The node is taken offline
        * We check the job fails
        * We check that the group and instance capacity are set to zero (where the group capacity should be zero b/c the group only contains one instance)
        * We check that the heartbeat for the offline instance does not advance
        * We check a new job launched against the node remains pending
        * We restart the node
        * We check that the pending job starts running and completes
        * We check that group and instance capacity for the now-online node are restored
        """
        manager = ansible_module_cls.inventory_manager
        hosts = manager.get_group_dict()['tower']

        # fetch the instance groups containing the tower nodes
        # we name the instance groups 1...n where n is the number of tower nodes
        hostname_to_instance_group = {}
        for i in range(1, len(hosts) + 1):
            group = v2.instance_groups.get(name=str(i)).results[0]
            hostname = group.related.instances.get().results[0].hostname
            hostname_to_instance_group[hostname] = group

        # create a long running job template for each host
        job_templates = {}
        for hostname in hosts:
            host = factories.v2_host()
            jt = factories.v2_job_template(playbook='sleep.yml',
                                           extra_vars=dict(sleep_interval=600),
                                           inventory=host.ds.inventory)
            jt.add_instance_group(hostname_to_instance_group[hostname])
            job_templates[hostname] = jt

        def fetch_node_not_matching_name(name):
            online_hosts = [hostname for hostname in hosts if hostname != name]
            return random.choice(online_hosts)

        ssh_template = "ssh -o StrictHostKeyChecking=no -t -t {} sudo ansible-tower-service {}"
        for hostname in hosts:
            # Store the capacity of the group and instance for later verification
            ig = hostname_to_instance_group[hostname]
            group_capacity = ig.capacity
            instance_capacity = ig.related.instances.get().results.pop().capacity

            online_hostname = fetch_node_not_matching_name(hostname)
            username = manager.get_host(hostname).get_vars()['ansible_user']
            connection = Connection('https://' + hostname)
            connection.login(admin_user.username, admin_user.password)
            with self.current_instance(connection, v2):
                ssh_invocation = "{}@{}".format(username, hostname)

                def offline():
                    try:
                        v2.get()
                    except:
                        # Possible errors here include ConnectionError, UnknownTowerState and
                        # exc.Unknown, so we assume any exception means the tower node is
                        # offline.
                        return True
                    return False

                def get_heartbeats():
                    """
                    return a dictionary of heartbeats of all online nodes in the tower group
                    and the heartbeat of the offline node"""
                    instances = v2.ping.get().instances
                    heartbeats = {}
                    offline_heartbeat = None
                    for instance in instances:
                        this_host = instance['node']
                        this_heartbeat = instance['heartbeat']
                        if this_host not in hosts:
                            # ignore nodes not in the tower group
                            continue
                        if this_host == hostname:
                            # this is the node we took offline
                            offline_heartbeat = this_heartbeat
                        else:
                            heartbeats[this_host] = this_heartbeat
                    return heartbeats, offline_heartbeat

                # Start a long running job from the node we're going to take offline
                long_job = job_templates[hostname].launch().wait_until_status('running')
                try:
                    log.debug("Shutting down node {}".format(hostname))
                    log.debug("Using online node {}".format(online_hostname))
                    # Stop the tower node, "-t" (twice) gives us a tty which is needed for sudo
                    cmd = ssh_template.format(ssh_invocation, "stop")
                    ret = subprocess.call(cmd, shell=True)
                    assert ret == 0
                    # Wait until it goes offline
                    utils.poll_until(offline, interval=5, timeout=120)

                    connection = Connection('https://' + online_hostname)
                    connection.login(admin_user.username, admin_user.password)
                    with self.current_instance(connection, v2):
                        # Check that the heartbeat of all nodes except the stopped one advance
                        heartbeats, offline_heartbeat = get_heartbeats()
                        assert offline_heartbeat is not None

                        def heartbeats_changed():
                            new_heartbeats, _ = get_heartbeats()
                            for host, beat in new_heartbeats.items():
                                if heartbeats[host] == new_heartbeats[host]:
                                    return False
                            return True

                        utils.poll_until(heartbeats_changed, interval=10, timeout=120)
                        _, current_offline_heartbeat = get_heartbeats()
                        # assert the offline heartbeat is unchanged
                        assert current_offline_heartbeat == offline_heartbeat

                        ig = hostname_to_instance_group[hostname]
                        # we have to fetch the group from an online instance
                        group = v2.instance_groups.get(id=ig.id).results.pop()

                        def check_group_capacity_zeroed():
                            group.get()
                            return group.capacity == 0
                        utils.poll_until(check_group_capacity_zeroed, interval=5, timeout=120)
                        instance = group.related.instances.get().results.pop()
                        assert instance.capacity == 0

                        # Check the job we started is marked as failed
                        long_job = v2.jobs.get(id=long_job.id).results[0]
                        long_job.wait_until_status('failed', interval=5, timeout=120)

                        # Should fail with explanation:
                        explanation = "Task was marked as running in Tower but was not present in Celery, so it has been marked as failed."
                        assert long_job.job_explanation == explanation

                        # Start a new job against the offline node
                        host = factories.v2_host()
                        jt = factories.v2_job_template(inventory=host.ds.inventory)
                        jt.add_instance_group(hostname_to_instance_group[hostname])
                        job = jt.launch()

                        # Check it stays in pending
                        start_time = time.time()
                        timeout = 60
                        interval = 5
                        while True:
                            job.get()
                            assert job.status == 'pending'

                            elapsed = time.time() - start_time
                            if elapsed > timeout:
                                break
                            time.sleep(interval)

                finally:
                    # Start the node again
                    cmd = ssh_template.format(ssh_invocation, "start")
                    ret = subprocess.call(cmd, shell=True)
                    assert ret == 0
                    utils.poll_until(lambda: not offline(), interval=5, timeout=120)

                # Capacity of the instance and the group should be restored
                group = v2.instance_groups.get(id=ig.id).results.pop()

                def check_group_capacity_restored():
                    group.get()
                    return group.capacity == group_capacity
                utils.poll_until(check_group_capacity_restored, interval=5, timeout=120)
                instance = group.related.instances.get().results.pop()
                assert instance.capacity == instance_capacity

                # Check that the waiting job is picked up and completes
                job.wait_until_completed()

                # Check that we can run a new job against the node
                job = jt.launch().wait_until_completed()
                assert job.is_successful

    @pytest.mark.requires_ha
    @pytest.mark.requires_isolation
    @pytest.mark.parametrize('run_on_isolated_group', [True, False], ids=['isolated group', 'regular instance group'])
    def test_project_copied_to_separate_instance_on_job_run(self, v2, factories, run_on_isolated_group):
        if run_on_isolated_group:
            ig1 = v2.instance_groups.get(name='tower').results.pop()
            ig2 = v2.instance_groups.get(name='protected').results.pop()
        else:
            ig1, ig2 = self.mutually_exclusive_instance_groups(v2.instance_groups.get().results)

        # Create project on first instance
        org = factories.v2_organization()
        org.add_instance_group(ig1)
        proj = factories.v2_project(organization=org)

        # Create and run job template on second instance
        host = factories.v2_host()
        jt = factories.v2_job_template(project=proj, inventory=host.ds.inventory)
        jt.add_instance_group(ig2)

        job = jt.launch().wait_until_completed()
        ig2_hostnames = [i.hostname for i in ig2.get_related('instances').results]
        assert job.execution_node in ig2_hostnames
        assert job.is_successful
