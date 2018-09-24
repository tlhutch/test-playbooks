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
