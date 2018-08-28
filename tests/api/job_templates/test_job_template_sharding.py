import logging

import pytest

from dateutil import rrule
from datetime import datetime
from dateutil.relativedelta import relativedelta

from tests.api import Base_Api_Test

from towerkit.rrule import RRule
from towerkit.utils import poll_until


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
            assert job.get().host_status_counts['ok'] == 1

    def test_job_template_shard_remainder_hosts(self, factories, v2):
        """Test the logic for when the host count (= 4) does not match the
        shard count (= 3)
        """
        jt = factories.v2_job_template(job_shard_count=3, allow_simultaneous=True)
        inventory = jt.ds.inventory
        hosts = []
        for i in range(5):
            hosts.append(inventory.related.hosts.post(payload=dict(
                name='foo{}'.format(i),
                variables='ansible_connection: local'
            )))
        workflow_job = jt.launch()
        workflow_job.wait_until_completed()
        assert workflow_job.is_successful

        # The obvious test that sharding worked - that all hosts have only 1 job
        assert [host.related.job_host_summaries.get().count for host in hosts] == [1 for i in range(5)]

        # It must be deterministic which jobs run which hosts
        for i, node in enumerate(workflow_job.related.workflow_nodes.get(order_by='created').results):
            job = node.related.job.get()
            if i in (0, 1):
                assert job.get().host_status_counts['ok'] == 2
            else:
                assert job.get().host_status_counts['ok'] == 1

    def test_job_template_shard_prompts(self, factories, v2, gce_credential):
        """Tests that prompts applied on launch fan out to shards
        """
        ct = 3
        jt = factories.v2_job_template(
            job_shard_count=ct, allow_simultaneous=True,
            ask_limit_on_launch=True,
            ask_credential_on_launch=True
        )
        inventory = jt.ds.inventory
        hosts = []
        for i in range(ct):
            hosts.append(inventory.related.hosts.post(payload=dict(
                name='foo{}'.format(i),
                variables='ansible_connection: local'
            )))
        workflow_job = jt.launch(payload=dict(
            limit='foobar',
            credentials=[jt.ds.credential.id, gce_credential.id]
        ))
        workflow_job.wait_until_completed()
        for node in workflow_job.related.workflow_nodes.get().results:
            assert node.limit == 'foobar'
            assert (
                set(cred.id for cred in node.related.credentials.get().results) ==
                set([gce_credential.id, jt.ds.credential.id])
            )
            job = node.related.job.get()
            prompts = job.related.create_schedule.get()['prompts']
            assert prompts['limit'] == 'foobar'
            assert prompts['credentials'] == [gce_credential.id]


    def test_job_template_shard_schedule(self, factories, v2, gce_credential):
        """Test that schedule runs will work with sharded jobs
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
        schedule = jt.add_schedule(
            rrule=RRule(rrule.MINUTELY, dtstart=datetime.utcnow() + relativedelta(minutes=-1, seconds=+30))
        )
        poll_until(lambda: schedule.related.unified_jobs.get().count == 1, interval=15, timeout=60)
        workflow_job = schedule.related.unified_jobs.get().results.pop()

        assert workflow_job.type == 'workflow_job'
        assert workflow_job.job_template == jt.id
        assert workflow_job.related.workflow_nodes.get().count == 3

    # TODO: (some kind of test for actual clusters, probably in job execution node assignment)
