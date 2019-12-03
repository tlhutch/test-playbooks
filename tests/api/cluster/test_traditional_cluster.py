# -*- coding: utf-8 -*-

from contextlib import contextmanager
import logging
import random
import re
import subprocess
import sys
import time
import traceback

import pytest
from awxkit import utils
from awxkit.api import Connection
import awxkit.exceptions as exc
from awxkit.utils import random_title

from tests.api import APITest

log = logging.getLogger(__name__)

FAIL_STATUSES = ('error', 'failed')


class SafeStop(object):
    """A context manager that stops tower services on a single or multiple hosts
    and guarantees to restart the tower services on exit."""

    def __init__(self, stoppers, starters):
        if not isinstance(stoppers, list):
            stoppers = [stoppers]
        if not isinstance(starters, list):
            starters = [starters]
        self.stoppers = stoppers
        self.starters = starters
        self.stop_exceptions = []
        self.start_exceptions = []

    def __enter__(self):
        for stop in self.stoppers:
            self.safe_call(stop, self.stop_exceptions)
        if self.stop_exceptions:
            # Ensure we call starters if any stoppers failed
            self.__exit__()
        return self

    def __exit__(self, *exc_info):
        for start in self.starters:
            self.safe_call(start, self.start_exceptions)
        # Check if we have an exceptional exit
        self.raise_errors(exc_info)
        return False

    def safe_call(self, func, exceptions):
        try:
            func()
        except:
            exceptions.append(sys.exc_info())

    def raise_errors(self, final_error=()):
        have_exceptions = self.stop_exceptions or self.start_exceptions
        if not have_exceptions and not any(final_error):
            # No exceptions, normal exit
            return
        stop_message = self.build_error_message(self.stop_exceptions, during_stop=True)
        start_message = self.build_error_message(self.start_exceptions)
        final_error_message = ''

        if any(final_error):
            msg = 'Exception raised during test:\n\n{}\n\n'
            error_info = traceback.format_exc(final_error)
            final_error_message = msg.format(error_info)

        raise Exception(stop_message + start_message + final_error_message)

    def build_error_message(self, errors, during_stop=True):
        if not errors:
            return ''
        # We have an exceptional exit
        event = 'starting' if during_stop is False else 'stopping'
        error_info = '\n\n'.join([traceback.format_exc(info[2]) for info in errors])
        return 'Exceptions raised {} nodes:\n\n{}\n\n'.format(event, error_info)


def instances_using_ipv4(v2):
    """Return true if instances are specified by ipv4 addresses."""
    groups = v2.instance_groups.get().results
    for group in groups:
        instances = [instance.hostname for instance in group.get_related('instances').results]
        if instances:
            return re.search('\d*\.\d*\.\d*\.\d*', instances[0])
        else:
            continue
    return False


@pytest.mark.usefixtures('authtoken', 'skip_if_not_traditional_cluster')
class TestTraditionalCluster(APITest):

    def mutually_exclusive_instance_groups(self, instance_groups):
        instance_group_to_instances_map = [(instance_group, set([instance.id for instance in instance_group.get_related('instances').results]))
                                           for instance_group in instance_groups]
        for first in instance_group_to_instances_map:
            for second in instance_group_to_instances_map:
                if not (first[1] & second[1]):
                    return first[0], second[0]
        pytest.skip("Unable to find two mutually exclusive instance groups")

    def get_stop_and_start_funcs_for_node(self, admin_user, hostvars_for_host, hostname, v2):
        username = hostvars_for_host(hostname)['ansible_user']
        # "-t" (twice) gives us a tty which is needed for sudo
        ssh_template = "ssh -o StrictHostKeyChecking=no -t -t {} 'sudo ansible-tower-service {}' 1>&2"
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

        connection = Connection('https://' + hostname)
        connection.login(admin_user.username, admin_user.password)

        def stop_node():
            with self.current_instance(connection, v2):
                log.debug("Shutting down node {}".format(hostname))
                # Stop the tower node
                cmd = ssh_template.format(ssh_invocation, "stop")
                ret = subprocess.call(cmd, shell=True)
                assert ret == 0
                # Wait until it goes offline
                utils.poll_until(offline, interval=5, timeout=120)

        def start_node():
            with self.current_instance(connection, v2):
                # Start the tower node
                cmd = ssh_template.format(ssh_invocation, "start")
                ret = subprocess.call(cmd, shell=True)
                assert ret == 0
                # Wait until it comes online
                utils.poll_until(lambda: not offline(), interval=5, timeout=120)

        return stop_node, start_node

    def assert_job_stays_pending(self, job):
        pending_statuses = set(('pending', 'waiting'))
        start_time = time.time()
        timeout = 60
        interval = 5
        while True:
            job.get()
            assert job.status in pending_statuses

            elapsed = time.time() - start_time
            if elapsed > timeout:
                break
            time.sleep(interval)

    def test_instance_group_creation(self, authtoken, v2, ansible_adhoc, hosts_in_group):
        group_mapping = ansible_adhoc().options['inventory_manager'].get_groups_dict()
        inventory_file_instance_groups = {}
        inventory_file_instance_groups['tower'] = group_mapping.get('tower', 'Something is busted, no tower group found!')
        for group in group_mapping.keys():
            match = re.search('(instance_group_|isolated_group_)(.*)', group)
            if match:
                inventory_file_instance_groups[match.group(2)] = group_mapping[group]

        instance_groups = [group.name for group in v2.instance_groups.get().results]
        assert len(instance_groups) >= len(inventory_file_instance_groups.keys())
        assert set(inventory_file_instance_groups.keys()) <= set(instance_groups)

        # group_mapping maps instance groups to fqdns, but we need ip addresses
        # relate the two to eachother via the ansible_host var passed with each
        # host in the inventory file. If no ansible_host var is present, we will
        # just stick to hostname.
        hostname_map = hosts_in_group('all', return_map=True)
        for group in v2.instance_groups.get().results:
            if not group.is_containerized:
                instances = [instance.hostname for instance in group.get_related('instances').results]
                assert len(instances) == len(inventory_file_instance_groups[group.name])
                # Using default of host allows us to cope with situations when
                # there is no "ansible_host" defined
                if instances_using_ipv4(v2):
                    # instances are using ip addresses
                    assert set(instances) == set([hostname_map.get(host, host) for host in inventory_file_instance_groups[group.name]])
                else:
                    assert set(instances) == set(inventory_file_instance_groups[group.name])

    def test_instance_groups_do_not_include_isolated_instances(self, v2):
        igs = [ig for ig in v2.instance_groups.get().results if not ig.controller]
        isolated_instance_hostnames = [ig.hostname for ig in
                                       v2.instances.get(rampart_groups__controller__isnull=False).results]
        for ig in igs:
            ig_hostnames = [i.hostname for i in ig.related.instances.get().results]
            assert set(ig_hostnames).isdisjoint(set(isolated_instance_hostnames))

    @pytest.mark.serial
    def test_default_instance_attributes(self, v2):
        for instance in v2.instances.get().results:
            assert instance.enabled
            assert instance.cpu > 0
            assert instance.memory > 0
            assert instance.cpu_capacity > 0
            assert instance.mem_capacity > 0
            assert instance.capacity == max(instance.cpu_capacity, instance.mem_capacity)
            assert instance.capacity_adjustment == '1.00'

    def test_isolated_instance_control_node(self, v2, factories):
        ig = v2.instance_groups.get(name='protected').results[0]

        jt = factories.job_template()
        jt.add_instance_group(ig)

        job = jt.launch().wait_until_completed()

        assert job.get().status == 'successful'

        assert job.instance_group == ig.id, \
            "Job should run on the instance group assigned to the Job Template"

        assert job.controller_node in \
            [i.hostname for i in ig.related.controller.get().related.instances.get().results], \
            "Job control node chosen not found in controlling instances"

        assert job.execution_node in \
            [instance.hostname for instance in ig.related.instances.get().results], \
            "Job should execute on a node in the 'isolated' instance group"

    def test_isolated_artifacts(self, v2, factories, artifacts_from_stats_playbook):
        # Create JT that does set_stats
        host = factories.host()
        set_stats_jt = factories.job_template(
            playbook='test_set_stats.yml', inventory=host.ds.inventory
        )

        # Launch and finish isolated job
        ig = v2.instance_groups.get(name='protected').results[0]
        set_stats_jt.add_instance_group(ig)
        stats_job = set_stats_jt.launch().wait_until_completed()
        stats_job.assert_successful()

        assert stats_job.artifacts == artifacts_from_stats_playbook

    def test_full_instances_cannot_be_added_to_an_isolated_instance_group(self, v2):
        full_instances = v2.instances.get(rampart_groups__controller__isnull=True).results
        protected_ig = v2.instance_groups.get(name='protected').results.pop()

        for full_instance in full_instances:
            with pytest.raises(exc.BadRequest) as err:
                protected_ig.add_instance(full_instance)
            assert 'Isolated instance group membership may not be managed via the API.' == err.value.msg['error']

    def test_can_add_or_remove_instance_to_control_group(self, v2, factories, hosts_in_group, hostvars_for_host,
                                                         user_password):
        managed = hosts_in_group('managed_hosts')[0]
        username = hostvars_for_host(managed).get('ansible_user')
        cred = factories.credential(username=username, password=user_password)
        host = factories.host(name=managed, variables=dict(ansible_host=managed))

        jt = factories.job_template(allow_simultaneous=True, inventory=host.ds.inventory, credential=cred)
        protected_ig = v2.instance_groups.get(name='protected').results.pop()
        jt.add_instance_group(protected_ig)

        controller_group = v2.instance_groups.get(name='controller').results.pop()
        new_controller = v2.instance_groups.get(name='future_controller').results.pop().related.instances\
                           .get().results.pop()

        try:
            controller_group.add_instance(new_controller)
            controller_group_instances = controller_group.related.instances.get().results
            assert new_controller.id in [i.id for i in controller_group_instances]

            num_jobs = 3 * len(controller_group_instances)
            for _ in range(num_jobs):
                jt.launch()
            jobs = jt.related.jobs
            utils.poll_until(lambda: jobs.get(status='successful', order_by='id').count == num_jobs, interval=5, timeout=300)
            last_job = jt.related.jobs.get(order_by='id').results[-1].id

            job_controller_nodes = [job.controller_node for job in jt.related.jobs.get().results]
            assert set(job_controller_nodes) == set([instance.hostname for instance
                                                    in controller_group_instances])
        finally:
            controller_group.remove_instance(new_controller)

        controller_group_instances = controller_group.related.instances.get().results
        assert new_controller.id not in [i.id for i in controller_group_instances]

        num_jobs = 3 * len(controller_group_instances)
        for _ in range(num_jobs):
            jt.launch()
        jobs = jt.related.jobs
        utils.poll_until(lambda: jobs.get(id__gt=last_job, status='successful').count == num_jobs, interval=5, timeout=300)

        job_controller_nodes = [job.controller_node for job in jt.related.jobs.get(id__gt=last_job).results]
        assert set(job_controller_nodes) == set([instance.hostname for instance
                                                in controller_group_instances])

    def test_isolated_instance_cannot_be_added_to_instance_group(self, v2):
        iso_instances = v2.instances.get(rampart_groups__controller__isnull=False).results
        instance_groups = [ig for ig in v2.instance_groups.get().results]

        for ig in instance_groups:
            for instance in iso_instances:
                with pytest.raises(exc.BadRequest) as err:
                    ig.add_instance(instance)
                assert 'Isolated instances may not be added or removed from instances groups via the API.' == err.value.msg['error']

    def test_isolated_instance_cannot_be_removed_from_isolated_group(self, v2):
        iso_instance_groups = [ig for ig in v2.instance_groups.get().results if ig.controller]
        for ig in iso_instance_groups:
            for instance in ig.related.instances.get().results:
                with pytest.raises(exc.BadRequest):
                    ig.remove_instance(instance)

    def test_cannot_delete_controller_instance_group(self, v2):
        controller_ig_ids = [ig.controller for ig in v2.instance_groups.get().results if ig.controller]
        controller_igs = [v2.instance_groups.get(id=id).results.pop() for id in controller_ig_ids]

        for ig in controller_igs:
            with pytest.raises(exc.Forbidden):
                ig.delete()

    def test_cannot_delete_isolated_group(self, v2):
        isolated_groups = [ig for ig in v2.instance_groups.get().results if ig.controller]

        for ig in isolated_groups:
            with pytest.raises(exc.Forbidden):
                ig.delete()

    def test_job_with_unicode_successfully_runs_on_isolated_node(self, v2, factories):
        ig = v2.instance_groups.get(name='protected').results.pop()

        jt = factories.job_template(playbook='utf-8-䉪ቒ칸ⱷꯔ噂폄蔆㪗輥.yml')
        jt.add_instance_group(ig)
        factories.host(inventory=jt.ds.inventory)

        job = jt.launch().wait_until_completed()
        assert job.status == 'successful'

    @pytest.mark.serial
    @pytest.mark.parametrize('base_resource, parent_resource', [
        ('job_template', 'inventory'),
        ('job_template', 'organization'),
        ('inventory', 'organization')
    ])
    def test_instance_group_hierarchy(self, v2, factories, base_resource, parent_resource, get_resource_from_jt):
        assert not len(v2.jobs.get(status='running').results), "Test requires Tower to not have any running jobs"

        instance_groups = sorted(v2.instance_groups.get().results, key=lambda x: x.instances)
        if len(instance_groups) == 1:
            pytest.skip('Test requires multiple instance groups')

        base_instance_group, parent_instance_group = self.mutually_exclusive_instance_groups(instance_groups)
        host = factories.host()
        jt = factories.job_template(inventory=host.ds.inventory, playbook='sleep.yml', extra_vars=dict(sleep_interval=600), allow_simultaneous=True)
        factories.host(inventory=jt.ds.inventory)

        get_resource_from_jt(jt, base_resource).add_instance_group(base_instance_group)
        get_resource_from_jt(jt, parent_resource).add_instance_group(parent_instance_group)

        instance_group_to_hostnames_map = {instance_group.id: [instance.hostname for instance in instance_group.get_related('instances').results]
                                           for instance_group in instance_groups}
        while True:
            job = jt.launch()
            utils.poll_until(lambda: job.get().status not in ['pending', 'waiting'], interval=10, timeout=120)
            assert job.status == 'running', "Job failed with stdout:\n{}\njob_explanation:{}".format(
                job.result_stdout, job.job_explanation)
            if job.execution_node in instance_group_to_hostnames_map[base_instance_group.id]:
                assert base_instance_group.get().percent_capacity_remaining >= 0
            else:
                break
        assert job.execution_node in instance_group_to_hostnames_map[parent_instance_group.id]
        assert parent_instance_group.get().consumed_capacity > \
            base_instance_group.capacity - base_instance_group.consumed_capacity

    @pytest.mark.serial
    def test_job_run_against_isolated_node_ensure_viewable_from_all_nodes(self, hosts_in_group, factories,
                                                                          admin_user, user_password, v2,
                                                                          hostvars_for_host):
        hosts = hosts_in_group('instance_group_ordinary_instances')
        managed = hosts_in_group('managed_hosts')[0]
        protected = v2.instance_groups.get(name='protected').results[0]

        username = hostvars_for_host(managed).get('ansible_user')
        cred = factories.credential(username=username, password=user_password)
        host = factories.host(name=managed, variables=dict(ansible_host=managed))
        jt = factories.job_template(inventory=host.ds.inventory, credential=cred)
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

    @pytest.mark.serial
    @pytest.mark.parametrize('run_on_isolated_group', [True, False], ids=['isolated group', 'regular instance group'])
    def test_running_jobs_consume_capacity(self, factories, v2, run_on_isolated_group):
        ig_filter = dict(name='protected') if run_on_isolated_group else dict(not__name='protected')
        ig = random.choice(v2.instance_groups.get(**ig_filter).results)
        # Ensure no capacity consumed initially
        utils.poll_until(lambda: ig.get().consumed_capacity == 0, interval=10, timeout=60)

        host = factories.host()
        jt = factories.job_template(inventory=host.ds.inventory, playbook='sleep.yml', extra_vars=dict(sleep_interval=600), allow_simultaneous=True)
        jt.add_instance_group(ig)

        previous_ig_consumed_capacity = 0
        for _ in range(3):
            job = jt.launch().wait_until_status('running')
            utils.poll_until(lambda: getattr(job.get(), 'execution_node') != '', interval=10, timeout=45)

            # Capacity should increase after each job launch
            assert ig.get().consumed_capacity > previous_ig_consumed_capacity
            previous_ig_consumed_capacity = ig.consumed_capacity
            assert ig.percent_capacity_remaining == round(float(ig.capacity - ig.consumed_capacity) * 100 / ig.capacity, 2)
            instance = [i for i in ig.get_related('instances').results if i.hostname == job.execution_node][0]

            assert instance.get().consumed_capacity > 0
            assert instance.percent_capacity_remaining == round(float(instance.capacity - instance.consumed_capacity) * 100 / instance.capacity, 2)

    @pytest.mark.serial
    def test_controller_removal(self, admin_user, hosts_in_group, hostvars_for_host, factories, user_password, v2):
        """
        Test that shutting down tower services on both controller nodes prevents us from launching
        jobs against an isolated node. This also tests that a cluster can successfully recover after
        shutting down more than one node simultaneously."""
        hosts = hosts_in_group('instance_group_ordinary_instances')
        controllers = hosts_in_group('instance_group_controller')

        online_hostname = None
        stoppers, starters = [], []
        for host in hosts:
            if host not in controllers:
                online_hostname = host
                continue
            stop, start = self.get_stop_and_start_funcs_for_node(admin_user, hostvars_for_host, host, v2)
            starters.append(start)
            stoppers.append(stop)

        assert online_hostname is not None
        assert len(stoppers) == len(starters) == len(controllers)

        connection = Connection('https://' + online_hostname)
        connection.login(admin_user.username, admin_user.password)
        with self.current_instance(connection, v2):
            # Store original controller group capacity for later verification
            controller_group = v2.instance_groups.get(name="controller").results[0]
            original_capacity_controller_ig = controller_group.capacity

            # Start a long running job against the isolated node
            protected_group = v2.instance_groups.get(name="protected").results[0]
            original_capacity_protected_ig = protected_group.capacity

            host = factories.host()
            jt = factories.job_template(playbook='sleep.yml',
                                           extra_vars=dict(sleep_interval=600),
                                           inventory=host.ds.inventory)
            jt.add_instance_group(protected_group)
            long_job = jt.launch().wait_until_started()

            # Stop controller nodes
            with SafeStop(stoppers, starters):
                # Wait until controller group capacity is set to zero
                utils.poll_until(lambda: controller_group.get().capacity == 0,
                                 interval=5, timeout=120)
                # It has been determined that the protected_group capacity is
                # not set to zero by any logic when the controller nodes are
                # down, because there is no access to the nodes by which to get
                # this information. See https://github.com/ansible/awx/issues/2874

                # Check the long running job fails
                long_job.wait_until_status(FAIL_STATUSES, interval=5, timeout=180, since_job_created=False)

                # Should fail with explanation:
                explanation = "Task was marked as running in Tower but was not present in the job queue, so it has been marked as failed."
                assert long_job.job_explanation == explanation

                # Start a new job and check it remains pending
                jt = factories.job_template(inventory=host.ds.inventory)
                jt.add_instance_group(protected_group)
                job = jt.launch()

                # Check it stays in pending
                self.assert_job_stays_pending(job)

            # Check group capacity is restored
            utils.poll_until(lambda: controller_group.get().capacity == original_capacity_controller_ig, interval=5, timeout=120)
            utils.poll_until(lambda: protected_group.get().capacity == original_capacity_protected_ig, interval=5, timeout=120)

            # Check the pending job is picked up
            job.wait_until_completed(since_job_created=False)
            # Check we can successfully launch a new job against the isolated node
            job = jt.launch().wait_until_completed()
            job.assert_successful()

    @pytest.mark.serial  # noqa: C901
    def test_instance_removal(self, connection, admin_user, user_password, inventory_hostname_map, ansible_adhoc,
                              hosts_in_group, hostvars_for_host, factories, v2):
        """
        This test checks a full node's ability to recover when its tower services are stopped and restarted

        * A long running job is started assigned to run on the node
        * The node is taken offline
        * We check the job fails
        * We check that the group and instance capacity are set to zero (where the group capacity should be zero b/c the group only contains one instance)
        * We check that the heartbeat for the offline instance does not advance
        * We check a new job launched against the node remains pending
        * We restart the node
        * We check that the pending job starts running and completes
        * We check that group and instance capacity for the now-online node are restored
        * We check a new job against the now-back-online node starts and completes
        """
        def get_rabbit_master():
            inventory_file = ansible_adhoc().options['inventory']
            hosts = hosts_in_group('instance_group_ordinary_instances', return_hostnames=True)
            for host in hosts:
                cmd = "ANSIBLE_BECOME=true ansible {} -i {} -m shell -a 'rabbitmqctl list_queues -p tower --local'".format(host, inventory_file)
                proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
                stdout, stderr = proc.communicate()
                stdout = stdout.decode()
                stderr = stderr.decode()
                if 'awx_private_queue' in stdout:
                    return host
            else:
                raise Exception('Failed to find rabbit master')

        if instances_using_ipv4(v2):
            hosts = hosts_in_group('instance_group_ordinary_instances')
            host = inventory_hostname_map(get_rabbit_master())
        else:
            hosts = hosts_in_group('instance_group_ordinary_instances', return_hostnames=True)
            host = get_rabbit_master()
        instance = v2.instances.get(hostname=host).results.pop()

        active_host = hosts[1] if hosts[0] == host else hosts[0]
        active_instance = v2.instances.get(hostname=active_host).results.pop()
        active_ig = factories.instance_group()
        active_ig.add_instance(active_instance)

        # Create an instance group with only the target instance
        ig = factories.instance_group()
        ig.add_instance(instance)
        ig = ig.get()  # needed for accurate capacity value

        # create a long running job template
        jt = factories.job_template(playbook='sleep.yml',
                                       extra_vars=dict(sleep_interval=600))
        jt.ds.inventory.add_host()
        jt.add_instance_group(ig)

        # MIGHT NEED TO WAIT TO HAVE ACCURATE INSTANCE CAPACITY
        # Store the capacity of the group and instance for later verification
        group_capacity = ig.capacity
        instance_capacity = instance.capacity

        # Start a long running job from the node we're going to take offline
        long_job = jt.launch().wait_until_status('running')
        assert long_job.execution_node == host

        def get_capacities(v):
            """
            Return a dictionary of the capacity of all ordinary nodes that are online
            and the capacity of the node we take offline.
            """
            instances = v.ping.get().instances
            capacities = {}
            offline_capacity = None
            for i in instances:
                this_host = i['node']
                this_capacity = i['capacity']
                if this_host not in hosts and this_host != host:
                    # ignore nodes not in the ordinary_instances group
                    continue
                if this_host == host:
                    # this is the node we took offline
                    offline_capacity = this_capacity
                else:
                    capacities[this_host] = this_capacity
            return capacities, offline_capacity

        original_capacities, original_capacity_of_offline_node = get_capacities(v2)

        def get_stable_connection():
            """
            Returns a context manager that can be used to ensure that test is connected
            to an instance that is not going to be brought down as part of the test.

            Will either return a
            - no-op context manager if connected to an instance that won't be brought down, or
            - context manager that will switch connections if connected to an instance that will
              be brought down
            """
            current_host = v2.ping.get().active_node
            if host != current_host:
                return contextmanager(lambda: (yield))  # no-op context mgr

            for h in hosts:
                if h != current_host:
                    other_host = h
                    break
            else:
                raise Exception('Test requires at least two full instances in cluster')

            @contextmanager
            def _stable_connection():
                connection = Connection('https://' + other_host)
                connection.login(admin_user.username, admin_user.password)
                with self.current_instance(connection, v2, pages=[instance, ig, jt, long_job, active_ig]):
                    yield
            return _stable_connection

        # Stop the tower node.
        stable_connection = get_stable_connection()
        with stable_connection():
            stop, start = self.get_stop_and_start_funcs_for_node(admin_user, hostvars_for_host, host, v2)
            with SafeStop(stop, start):
                # Confirm new rabbit master elected
                def new_rabbit_master_elected():
                    try:
                        master = inventory_hostname_map(get_rabbit_master())
                        return master != host
                    except:
                        # Failed to find master
                        return False
                utils.poll_until(new_rabbit_master_elected, interval=10, timeout=60)

                # We probably cannot trust that the node is offline yet
                # poll until capacity is 0 on offline node to know everything is dead
                def check_group_capacity_zeroed():
                    ig.get()
                    return ig.capacity == 0
                utils.poll_until(check_group_capacity_zeroed, interval=5, timeout=190)

                def get_heartbeats():
                    """
                    return a dictionary of heartbeats of all ordinary nodes that are online
                    and the heartbeat of the offline node"""
                    instances = v2.ping.get().instances
                    heartbeats = {}
                    offline_heartbeat = None
                    for i in instances:
                        this_host = i['node']
                        this_heartbeat = i['heartbeat']
                        if this_host not in hosts and this_host != host:
                            # ignore nodes not in the ordinary_instances group
                            continue
                        if this_host == host:
                            # this is the node we took offline
                            offline_heartbeat = this_heartbeat
                        else:
                            heartbeats[this_host] = this_heartbeat
                    return heartbeats, offline_heartbeat

                other_heartbeats, offline_heartbeat = get_heartbeats()
                # assert the offline heartbeat is unchanged
                # then wait another two min and get heartbeat again and assert not changed
                time.sleep(190)

                # Check capacity only changed on offline node
                current_other_capacities, current_offline_capacity = get_capacities(v2)
                for key in current_other_capacities.keys():
                    assert current_other_capacities[key] == original_capacities[key], \
                        'Capacity for online node {} changed! Only the offline node should have its capacity changed!'.format(key)
                # Check that instance capacity is set to zero
                assert current_offline_capacity == 0, 'Capacity for offline instance is not set to 0!'

                current_other_heartbeats, current_offline_heartbeat = get_heartbeats()
                assert current_offline_heartbeat == offline_heartbeat
                for key in other_heartbeats.keys():
                    assert current_other_heartbeats[key] != other_heartbeats[key], \
                        'Heartbeat for online node {} did not advance! Only the offline node should have its heartbeat stop!'.format(key)

                # Check that ig capacity is still set to zero
                assert instance.get().capacity == 0, 'Instance group capacity changed while node was still offline'

                # Check the job we started is marked as failed
                utils.poll_until(lambda: long_job.get().status in FAIL_STATUSES, interval=5, timeout=130)
                long_job = long_job.get()
                # Should fail with explanation
                explanation = "Task was marked as running in Tower but was not present in the job queue, so it has been marked as failed."
                assert long_job.job_explanation == explanation

                # Start a new job against the offline node
                jt.patch(extra_vars='', playbook='ping.yml')  # no longer need long-running job
                job = jt.launch()

                # Check it stays in pending
                self.assert_job_stays_pending(job)

                # Confirm that job run on node that was not shut down runs successfully
                jt_on_active_node = factories.job_template()
                jt_on_active_node.ds.inventory.add_host()
                jt_on_active_node.add_instance_group(active_ig)
                jt_on_active_node.launch().wait_until_completed().assert_successful()

        # Capacity of the instance and the group should be restored
        def check_group_capacity_restored():
            return ig.get().capacity == group_capacity
        utils.poll_until(check_group_capacity_restored, interval=5, timeout=120)
        assert instance.get().capacity == instance_capacity

        current_other_capacities, current_capacity_of_restored_node = get_capacities(v2)
        assert current_capacity_of_restored_node == original_capacity_of_offline_node, \
            'Capacity for instance that has been restored did not return to original value!'
        for key in current_other_capacities.keys():
            assert current_other_capacities[key] == original_capacities[key], \
                'Capacity for online node {} changed! They should not have been effected by other node capacity change!'.format(key)

        # Check that the waiting job is picked up and completes
        job.wait_until_completed(since_job_created=False)

        # Check that we can run a new job against the node
        job = jt.launch().wait_until_completed()
        job.assert_successful()

    @pytest.mark.github('https://github.com/ansible/tower/issues/4007', ids=['svn-isolated group', 'svn-regular instance group'], skip=True)
    @pytest.mark.serial
    @pytest.mark.parametrize('run_on_isolated_group', [True, False], ids=['isolated group', 'regular instance group'])
    @pytest.mark.parametrize('scm_type', ['git', 'svn', 'hg'])
    def test_project_copied_to_separate_instance_on_job_run(self, v2, factories, run_on_isolated_group, scm_type):
        if run_on_isolated_group:
            ig1 = v2.instance_groups.get(name='ordinary_instances').results.pop()
            ig2 = v2.instance_groups.get(name='protected').results.pop()
        else:
            ig1, ig2 = self.mutually_exclusive_instance_groups(v2.instance_groups.get().results)

        # Create project on first instance
        org = factories.organization()
        org.add_instance_group(ig1)
        proj = factories.project(organization=org, scm_type=scm_type)
        playbook = 'sleep.yml'
        if scm_type == 'svn':
            playbook = 'trunk/{}'.format(playbook)
        org.remove_instance_group(ig1)

        # Run job template on second instance
        host = factories.host()
        jt = factories.job_template(project=proj, inventory=host.ds.inventory, playbook=playbook)
        jt.add_instance_group(ig2)

        job = jt.launch().wait_until_completed()
        ig2_hostnames = [i.hostname for i in ig2.get_related('instances').results]
        assert job.execution_node in ig2_hostnames
        job.assert_successful()

    @pytest.mark.parametrize('setting_endpoint', ['all', 'jobs'])
    def test_ensure_awx_isolated_key_fields_are_read_only(self, factories, admin_user, user_password, v2, setting_endpoint):
        settings = v2.settings.get().get_endpoint(setting_endpoint)
        assert settings.AWX_ISOLATED_PUBLIC_KEY != '$encrypted$' and len(settings.AWX_ISOLATED_PUBLIC_KEY)
        assert settings.AWX_ISOLATED_PRIVATE_KEY == '$encrypted$'

        initial_value_public_key = settings.AWX_ISOLATED_PUBLIC_KEY
        initial_value_private_key = settings.AWX_ISOLATED_PRIVATE_KEY

        def check_settings():
            settings.get()
            assert settings.AWX_ISOLATED_PUBLIC_KEY == initial_value_public_key
            assert settings.AWX_ISOLATED_PRIVATE_KEY == initial_value_private_key

        settings.delete()
        check_settings()

        settings.patch(AWX_ISOLATED_PUBLIC_KEY='changed', AWX_ISOLATED_PRIVATE_KEY='changed')
        check_settings()

        payload = settings.get().json
        payload.AWX_ISOLATED_PUBLIC_KEY = 'changed'
        payload.AWX_ISOLATED_PRIVATE_KEY = 'changed'
        settings.put(payload)
        check_settings()

    def test_inventory_script_serialization_preserves_escaped_characters(self, factories, v2):
        """Inventory scripts are printed to a file and sent to isolated nodes.
        Test ensures that escaped characters are preserved in the process.
        """
        host = factories.host(variables=dict(ansible_host='127.0.0.1', ansible_connection='local', should_be_preserved='\f"'))
        jt = factories.job_template(playbook='debug_hostvars.yml', inventory=host.ds.inventory)
        ig_protected = v2.instance_groups.get(name='protected').results.pop()
        jt.add_instance_group(ig_protected)
        job = jt.launch().wait_until_completed()
        job_events = job.get_related('job_events').results
        for job_event in job_events:
            if job_event.event == 'runner_on_ok':
                assert list(job_event.event_data.res.hostvars.values())[0].should_be_preserved == '\x0c"'  # \x0c is equivalent to \f
                break
        else:
            pytest.fail('Failed to find job event with hostvar information')

    def test_venv_on_regular_instance(self, v2, factories, create_venv, venv_path):
        folder_name = random_title(non_ascii=False)
        with create_venv(folder_name, cluster=True):
            assert venv_path(folder_name) in v2.config.get().custom_virtualenvs
            jt = factories.job_template()
            jt.ds.inventory.add_host()
            jt.custom_virtualenv = venv_path(folder_name)

            # To facilitate testing, each instance in the traditional Tower cluster
            # is assigned to its own instance group. The instance groups are named
            # 1, 2, .. n, where n is the total number of regular instances in the cluster
            ig_ordinary_instances = v2.instance_groups.get(name='ordinary_instances').results.pop()
            i = random.randint(1, ig_ordinary_instances.related.instances.get().count)
            ig = v2.instance_groups.get(name=str(i)).results.pop()
            jt.add_instance_group(ig)

            job = jt.launch().wait_until_completed()
            job.assert_successful()
            assert job.job_env['VIRTUAL_ENV'] == venv_path(folder_name)

    @pytest.mark.run(order=1)
    @pytest.mark.serial
    def test_disabled_isolated_nodes_remain_disabled_after_heartbeat(self, v2, factories):
        # Disable all iso nodes in iso IG
        ig_protected = v2.instance_groups.get(name='protected').results.pop()
        instances = ig_protected.related.instances.get().results
        for instance in instances:
            instance.enabled = False
        for instance in instances:
            assert instance.get().capacity == 0

        # Ensure that job assigned to IG remains in pending state
        jt = factories.job_template()
        jt.ds.inventory.add_host()
        jt.add_instance_group(ig_protected)
        job = jt.launch()

        time.sleep(70)
        for instance in instances:
            assert instance.get().capacity == 0
            assert instance.enabled == False # noqa
        assert job.get().status == 'pending'

        # Re-enable iso nodes, ensure capacity is restored and job completes successfully
        for instance in instances:
            instance.enabled = True
        for instance in instances:
            assert instance.get().capacity > 0
        job.wait_until_completed(since_job_created=False)
        job.assert_successful()

    @pytest.mark.run(order=2)
    def test_isolated_instance_heartbeat_after_setting_iso_verbosity(self, request, v2, api_settings_all_pg):
        """
        This test and the previous one are ordered (see `run` markers) so that we can confirm that isolated
        node heartbeats continue to function after isolated nodes are disabled. Opted to do this (instead of
        creating a third test focused on this specifically), since these tests already consume a fair
        amount of time waiting for the next heartbeat to occur.

        The default heartbeat interval for isolated nodes is 10 minutes (see `AWX_ISOLATED_PERIODIC_CHECK`).
        The deploy-tower-cluster.yml playbook sets this to 1 minute at the end of the tower installation,
        though. This allows this pair of tests to poll for a much shorter period of time.
        """
        original_setting = api_settings_all_pg.get().AWX_ISOLATED_VERBOSITY
        api_settings_all_pg.AWX_ISOLATED_VERBOSITY = 5

        def reset_setting():
            api_settings_all_pg.AWX_ISOLATED_VERBOSITY = original_setting
        request.addfinalizer(reset_setting)

        isolated_instance_hostnames = [i.hostname for i in
                                       v2.instances.get(rampart_groups__controller__isnull=False).results]
        initial_heartbeats = {i.node: i.heartbeat for i in
                              v2.ping.get().instances if i.node in isolated_instance_hostnames}

        def isolated_heartbeats_advanced():
            heartbeats = {i.node: i.heartbeat for i in
                          v2.ping.get().instances if i.node in isolated_instance_hostnames}
            for i in isolated_instance_hostnames:
                if i not in heartbeats:
                    return False
                if heartbeats[i] == initial_heartbeats[i]:
                    return False
            return True
        utils.poll_until(isolated_heartbeats_advanced, interval=10, timeout=100)
