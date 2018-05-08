import random

import pytest

from tests.api import Base_Api_Test


@pytest.mark.api
@pytest.mark.requires_ha
@pytest.mark.usefixtures('authtoken', 'install_enterprise_license_unlimited')
class TestClusterCommon(Base_Api_Test):

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
