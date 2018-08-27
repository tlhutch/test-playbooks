import logging

import pytest

from tests.api import Base_Api_Test


log = logging.getLogger(__name__)


@pytest.mark.api
@pytest.mark.destructive
@pytest.mark.usefixtures('authtoken', 'install_enterprise_license_unlimited')
class TestJobTemplateSharding(Base_Api_Test):

    def test_job_template_shard_run(self, factories, v2):
        """Tests that a job template is split into multiple jobs
        and that those run against a 1/3rd subset of the inventory
        """
        ct = 3
        jt = factories.v2_job_template(job_shard_count=ct, allow_simultaneous=True)
        inventory = jt.ds.inventory
        hosts = []
        for i in range(ct):
            hosts.append(inventory.related.hosts.post(payload=dict(
                name='foo{}'.format(i),
                variables='ansible_connection: local'
            )))
        workflow_job = jt.launch()
        workflow_job.wait_until_completed()
        assert workflow_job.is_successful

        # The obvious test that sharding worked - that all hosts have only 1 job
        assert [host.related.job_host_summaries.get().count for host in hosts] == [1 for i in range(ct)]

        for job in v2.unified_jobs.get(unified_job_node__workflow_job=workflow_job.id).results:
            job.get().host_status_counts['ok'] == 1

    # TODO: tests still to write
    # test_job_template_shard_remainder_hosts
    # test_job_template_shard_prompts
    # (some kind of test for actual clusters, probably in job execution node assignment)
