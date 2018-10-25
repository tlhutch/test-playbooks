import random

import pytest

from tests.api import APITest


@pytest.mark.api
@pytest.mark.requires_cluster
@pytest.mark.usefixtures('authtoken', 'install_enterprise_license_unlimited')
class TestClusterCommon(APITest):

    def test_jobs_should_be_able_to_run_on_all_full_instances(self, v2, factories):
        instances = v2.instances.get(rampart_groups__controller__isnull=True).results
        igs = []
        for instance in instances:
            ig = factories.instance_group()
            ig.add_instance(instance)
            igs.append(ig)

        jt = factories.v2_job_template()
        jt.ds.inventory.add_host()

        for ig in igs:
            # reuse the same JT
            jt.remove_all_instance_groups()

            jt.add_instance_group(ig)
            job = jt.launch().wait_until_completed()
            assert job.is_successful
            assert job.execution_node == ig.related.instances.get().results.pop().hostname

    def test_fact_cache_across_different_tower_instances(self, tower_instance_group, factories):
        ig1, ig2 = [factories.instance_group() for _ in range(2)]
        instances = random.sample(tower_instance_group.related.instances.get().results, 2)
        ig1.add_instance(instances[0])
        ig2.add_instance(instances[1])

        host = factories.v2_host()
        gather_facts_jt = factories.v2_job_template(inventory=host.ds.inventory, playbook='gather_facts.yml', use_fact_cache=True)
        use_facts_jt = factories.v2_job_template(inventory=host.ds.inventory, playbook='use_facts.yml', job_tags='ansible_facts',
                                                 use_fact_cache=True)
        gather_facts_jt.add_instance_group(ig1)
        use_facts_jt.add_instance_group(ig2)

        gather_facts_job, use_facts_job = [jt.launch().wait_until_completed() for jt in (gather_facts_jt, use_facts_jt)]
        assert gather_facts_job.is_successful
        assert use_facts_job.is_successful

        ansible_facts = host.related.ansible_facts.get()
        assert use_facts_job.result_stdout.count(ansible_facts.ansible_distribution) == 1
        assert use_facts_job.result_stdout.count(ansible_facts.ansible_machine) == 1
        assert use_facts_job.result_stdout.count(ansible_facts.ansible_system) == 1

    @pytest.mark.mp_group('JobTemplateSharding', 'isolated_serial')
    def test_sliced_job_ordinary_instances(self, v2, factories):
        # obtain all ordinary (non-isolated) instances, put in instance group
        instances = v2.instances.get(rampart_groups__controller__isnull=True, page_size=200, capacity__gt=0).results
        ct = len(instances)
        cap_dict = {}
        ig = factories.instance_group()
        for inst in instances:
            inst.percent_capacity_remaining == 100.0
            cap_dict[inst.hostname] = inst.capacity
            ig.add_instance(inst)
        available_hostnames = set(inst.hostname for inst in instances)

        # duplicated with sliced_jt_factory fixture
        jt = factories.v2_job_template(job_slice_count=ct, playbook='sleep.yml', extra_vars='{"sleep_interval": 120}')
        jt.add_instance_group(ig)
        inventory = jt.ds.inventory
        for i in range(ct):
            inventory.related.hosts.post(payload=dict(
                name='foo{}'.format(i),
                variables='ansible_connection: local'
            ))

        # put the sharded job and joblets into stable running state
        workflow_job = jt.launch()
        assert workflow_job.type == 'workflow_job'
        nodes = workflow_job.get_related('workflow_nodes').results

        # verify expectations for this cluster state
        working_hostnames = set([])
        for node in nodes:
            job = node.wait_for_job().get_related('job')
            job.wait_until_status(['running'])
            assert job.instance_group == ig.id
            working_hostnames.add(job.execution_node)
        assert working_hostnames == available_hostnames  # jobs distribute evenly
        instances = ig.get_related('instances', page_size=200).results  # refresh capacity
        assert [inst.consumed_capacity for inst in instances] == [2 for i in range(ct)], (
            'Expected all instances used by sliced job to consume 2 units of capacity. '
            'List of all instances:\n{}'.format(instances)
        )
