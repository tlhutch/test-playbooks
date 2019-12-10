import logging

import pytest

from dateutil import rrule
from datetime import datetime
from dateutil.relativedelta import relativedelta

from tests.api import APITest

from tests.lib.rrule import RRule
from awxkit.utils import poll_until
from awxkit.exceptions import BadRequest, NotFound, Forbidden


log = logging.getLogger(__name__)


@pytest.mark.usefixtures('authtoken')
class TestJobTemplateSlicing(APITest):

    @pytest.fixture
    def sliced_jt_factory(self, factories):
        def r(ct, jt_kwargs=None, host_ct=None):
            if not jt_kwargs:
                jt_kwargs = {}
            if not host_ct:
                host_ct = ct
            jt = factories.job_template(job_slice_count=ct, **jt_kwargs)
            inventory = jt.ds.inventory
            hosts = []
            if 'inventory' not in jt_kwargs:
                for i in range(host_ct):
                    hosts.append(inventory.related.hosts.post(payload=dict(
                        name='foo{}'.format(i),
                        variables='ansible_connection: local'
                    )))
            return jt
        return r

    @pytest.mark.serial
    def test_job_template_slice_run(self, factories, v2, do_all_jobs_overlap, sliced_jt_factory):
        """Tests that a job template is split into multiple jobs
        and that those run against a 1/3rd subset of the inventory
        """
        jt = sliced_jt_factory(3)

        instance = v2.instances.get(
            rampart_groups__controller__isnull=True,
            capacity__gt=0
        ).results.pop()
        assert instance.capacity > 4, 'Cluster instances not large enough to run this test'
        ig = factories.instance_group()
        ig.add_instance(instance)
        jt.add_instance_group(ig)

        workflow_job = jt.launch()
        assert workflow_job.type == 'workflow_job'
        workflow_job.wait_until_completed()
        workflow_job.assert_successful()

        # The obvious test that slicing worked - that all hosts have only 1 job
        hosts = jt.ds.inventory.related.hosts.get().results
        assert [host.related.job_host_summaries.get().count for host in hosts] == [1 for i in range(3)]

        jobs = []
        for job in v2.unified_jobs.get(unified_job_node__workflow_job=workflow_job.id).results:
            assert job.get().host_status_counts['ok'] == 1
            jobs.append(job)

        assert do_all_jobs_overlap(jobs)

    @pytest.mark.serial
    @pytest.mark.parametrize('slices', (0, 1))
    def test_job_template_slice_zero_or_one_slice_does_not_run_as_workflow(self, factories, v2, do_all_jobs_overlap, sliced_jt_factory, slices):
        """Tests that a slice value of "0" or "1" does not create a workflow job
        """
        jt = sliced_jt_factory(slices)

        job = jt.launch()
        assert job.type != 'workflow_job'
        job.wait_until_completed()
        job.assert_successful()

    @pytest.mark.serial
    def test_job_template_many_slices_with_one_host_does_not_run_as_workflow(self, factories, v2):
        """Tests that a slice value of "2" does not create a workflow job when 1 host present
        """
        jt = factories.job_template(job_slice_count=2)
        inventory = jt.ds.inventory
        inventory.related.hosts.post(payload=dict(name='foo', variables='ansible_connection: local'))

        job = jt.launch()
        assert job.type != 'workflow_job'
        job.wait_until_completed()
        job.assert_successful()

        # Check that sparkline only reflects the job
        assert len(jt.get().summary_fields.recent_jobs) == 1

    @pytest.mark.serial
    @pytest.mark.parametrize('allow_sim', (True, False))
    def test_job_template_slice_allow_simultaneous(self, factories, v2, do_all_jobs_overlap,
                                                   sliced_jt_factory, allow_sim):
        jt = sliced_jt_factory(2, jt_kwargs=dict(allow_simultaneous=allow_sim))

        instance = v2.instances.get(
            rampart_groups__controller__isnull=True,
            capacity__gt=0
        ).results.pop()
        assert instance.capacity > 5, 'Cluster instances not large enough to run this test'
        ig = factories.instance_group()
        ig.add_instance(instance)
        jt.add_instance_group(ig)

        workflow_jobs = [jt.launch(), jt.launch()]
        for workflow_job in workflow_jobs:
            assert workflow_job.type == 'workflow_job'
            workflow_job.wait_until_completed()
            workflow_job.assert_successful()

        # The sliced workflow container has configurable allow_simultaneous
        assert do_all_jobs_overlap(workflow_jobs) == allow_sim

        for workflow_job in workflow_jobs:
            jobs = []
            for node in workflow_job.related.workflow_nodes.get().results:
                jobs.append(node.related.job.get())
            # The slices themselves should _always_ be simultaneous
            assert do_all_jobs_overlap(jobs)

    @pytest.mark.yolo
    def test_job_template_slice_workflow_job_relaunch(self, factories, v2, sliced_jt_factory):
        """Tests relaunch for jobs which are sliced, including:
        * relaunch of the workflow job container for sliced jobs
        """
        jt = sliced_jt_factory(2)

        workflow_job = jt.launch().get()  # .get() due to awxkit using list view

        # Relaunch overall job
        relaunched_wj = workflow_job.relaunch()
        assert relaunched_wj.type == 'workflow_job'
        assert relaunched_wj.get_related('workflow_nodes').count == 2
        orig_data = workflow_job.get().json.copy()
        relaunch_data = relaunched_wj.json
        non_static_fields = (
            'created', 'id', 'url', 'modified', 'related', 'launch_type',
            'started', 'status', 'elapsed'
        )
        for data in (orig_data, relaunch_data):
            for fd in non_static_fields:
                data.pop(fd)
        assert orig_data == relaunch_data

        node = workflow_job.get_related('workflow_nodes').results.pop()
        poll_until(lambda: node.get().job, interval=1, timeout=30)
        job = node.get_related('job')
        job.wait_until_completed()
        assert job.job_slice_count == 2
        assert job.event_processing_finished
        status_counts = job.get().host_status_counts
        assert 'ok' in status_counts  # ran on at least 1 host
        assert status_counts['ok'] == 1  # only ran on 1 host

    def test_job_template_slice_job_relaunch(self, factories, v2, sliced_jt_factory):
        """Tests relaunch for jobs which are sliced, including:
        * relaunch of job that ran on a particular slice
        """
        jt = sliced_jt_factory(2)

        workflow_job = jt.launch().get()  # .get() due to awxkit using list view

        node = workflow_job.get_related('workflow_nodes').results.pop()
        poll_until(lambda: node.get().job, interval=1, timeout=30)
        job = node.get_related('job')
        job.wait_until_completed()
        assert job.job_slice_count == 2
        assert job.event_processing_finished
        status_counts = job.get().host_status_counts
        assert 'ok' in status_counts  # ran on at least 1 host
        assert status_counts['ok'] == 1  # only ran on 1 host

        # Relaunch job slice
        relaunched_job = job.relaunch()
        assert relaunched_job.type == 'job'
        assert relaunched_job.job_slice_count == 2
        assert relaunched_job.job_slice_number == job.job_slice_number
        relaunched_job.wait_until_completed()
        assert 'ok' in status_counts  # ran on at least 1 host
        assert relaunched_job.get().host_status_counts['ok'] == 1  # only ran on 1 host

    def test_job_template_slice_relaunch_orphans(self, factories, v2, sliced_jt_factory):
        jt = sliced_jt_factory(2)

        workflow_job = jt.launch().get()  # .get() due to awxkit using list view
        workflow_job.wait_until_completed()
        node = workflow_job.get_related('workflow_nodes').results.pop()
        job = node.get_related('job')

        jt.delete()

        # Relaunch overall job
        with pytest.raises(BadRequest) as exc:
            workflow_job.relaunch()
        assert exc.value.msg == {'detail': 'Cannot relaunch slice workflow job orphaned from job template.'}
        # Relaunch joblet
        relaunched_job = job.relaunch()
        assert relaunched_job.job_slice_count == job.job_slice_count
        assert relaunched_job.job_slice_number == job.job_slice_number
        relaunched_job.wait_until_completed()
        assert job.host_status_counts == relaunched_job.host_status_counts

    def test_relaunch_after_conversion(self, factories, sliced_jt_factory):
        jt = sliced_jt_factory(2)
        workflow_job = jt.launch()

        jt.job_slice_count = 1
        with pytest.raises(BadRequest) as exc:
            workflow_job.relaunch()
        assert exc.value.msg == {'detail': 'Cannot relaunch sliced workflow job after slice count has changed.'}

    def test_job_template_slice_remainder_hosts(self, factories, sliced_jt_factory):
        """Test the logic for when the host count (= 5) does not match the
        slice count (= 3)
        """
        jt = sliced_jt_factory(3, host_ct=5)
        workflow_job = jt.launch()
        workflow_job.wait_until_completed()
        workflow_job.assert_successful()

        # The obvious test that slicing worked - that all hosts have only 1 job
        hosts = jt.ds.inventory.related.hosts.get().results
        assert [host.related.job_host_summaries.get().count for host in hosts] == [1 for i in range(5)]

        # It must be deterministic which jobs run which hosts
        job_okays = []
        for node in workflow_job.related.workflow_nodes.get(order_by='created').results:
            job = node.related.job.get()
            job_okays.append(job.get().host_status_counts['ok'])
        assert job_okays == [2, 2, 1]

    def test_job_template_slice_properties(self, factories, gce_credential, sliced_jt_factory):
        """Tests that JT properties are used in jobs that sliced
        workflow launches
        """
        jt = sliced_jt_factory(3, jt_kwargs=dict(verbosity=3, timeout=45))
        workflow_job = jt.launch()

        for node in workflow_job.related.workflow_nodes.get().results:
            assert node.verbosity is None

            poll_until(lambda: node.get().job, interval=1, timeout=30)
            job = node.related.job.get()
            assert job.related.create_schedule.get()['prompts'] == {}
            assert job.verbosity == 3
            assert job.timeout == 45

    def test_job_template_slice_prompts(self, gce_credential, sliced_jt_factory):
        """Tests that prompts applied on launch fan out to slices
        """
        jt = sliced_jt_factory(3, jt_kwargs=dict(
            ask_limit_on_launch=True,
            ask_credential_on_launch=True
        ))
        workflow_job = jt.launch(payload=dict(
            limit='foobar',
            credentials=[jt.ds.credential.id, gce_credential.id]
        ))

        for node in workflow_job.related.workflow_nodes.get().results:
            # design decision is to not save prompts on nodes
            assert node.limit is None
            assert node.related.credentials.get().count == 0

            poll_until(lambda: node.get().job, interval=1, timeout=30)
            job = node.related.job.get()
            prompts = job.related.create_schedule.get()['prompts']
            assert prompts['limit'] == 'foobar'
            assert [cred['id'] for cred in prompts['credentials']] == [gce_credential.id]
            assert set(cred.id for cred in job.related.credentials.get().results) == set([
                gce_credential.id, jt.ds.credential.id])

    def test_sliced_job_from_workflow(self, factories, sliced_jt_factory):
        wfjt = factories.workflow_job_template()
        jt = sliced_jt_factory(3)
        node = factories.workflow_job_template_node(
            workflow_job_template=wfjt,
            unified_job_template=jt
        )
        first_wj = wfjt.launch()
        first_wj_node = first_wj.related.workflow_nodes.get().results.pop()
        poll_until(lambda: first_wj_node.get().job, interval=1, timeout=30)
        sliced_job = first_wj_node.related.job.get()
        assert sliced_job.type == 'workflow_job'
        nodes = sliced_job.related.workflow_nodes.get()
        assert nodes.count == 3

        # better check that we didn't get recursion...
        for node in nodes.results:
            poll_until(lambda: node.get().job, interval=1, timeout=30)
            job = node.related.job.get()
            assert job.type == 'job'

    def test_job_template_slice_schedule(self, sliced_jt_factory):
        """Test that schedule runs will work with sliced jobs
        """
        jt = sliced_jt_factory(3)
        schedule = jt.add_schedule(
            rrule=RRule(rrule.MINUTELY, dtstart=datetime.utcnow() + relativedelta(minutes=-1, seconds=+30))
        )
        poll_until(lambda: schedule.related.unified_jobs.get().count == 1, interval=15, timeout=120)
        workflow_job = schedule.related.unified_jobs.get().results.pop()
        # teardown does not delete schedules created in v2
        schedule.delete()

        assert workflow_job.type == 'workflow_job'
        assert workflow_job.job_template == jt.id
        assert workflow_job.related.workflow_nodes.get().count == 3

    @pytest.mark.serial
    def test_job_template_slice_results_can_be_deleted(self, factories, v2, sliced_jt_factory):
        """Tests that job results for sliced jobs can be deleted,
           deleting the result for the workflow job does not
           delete the slice results, and that slice results can be deleted.
        """
        jt = sliced_jt_factory(3)

        workflow_job = jt.launch()
        assert workflow_job.type == 'workflow_job'
        workflow_job.wait_until_completed()
        slice_result = v2.unified_jobs.get(unified_job_node__workflow_job=workflow_job.id).results[0]
        workflow_job.delete()
        with pytest.raises(NotFound) as exc:
            workflow_job.get()
        assert exc.value.msg == {'detail': 'Not found.'}

        slice_result.delete()
        with pytest.raises(NotFound) as exc:
            slice_result.get()
        assert exc.value.msg == {'detail': 'Not found.'}

    @pytest.mark.serial
    def test_job_template_slice_results_readable_when_workflow_is_deleted(self, factories, v2, sliced_jt_factory):
        """Test that results for individual slices can still be obtained if the
           parent workflow job result is deleted.
        """
        jt = sliced_jt_factory(3)

        workflow_job = jt.launch()
        assert workflow_job.type == 'workflow_job'
        workflow_job.wait_until_completed()
        slice_results = v2.unified_jobs.get(unified_job_node__workflow_job=workflow_job.id).results
        workflow_job.delete()

        for job in slice_results:
            assert job.get().host_status_counts['ok'] == 1

    @pytest.mark.serial
    def test_job_template_slice_results_rbac(self, factories, v2, sliced_jt_factory):
        """Tests that users without permission cannot read results from sliced jobs,
           and that users with implicit permission can.
        """
        valid_user = factories.user()
        invalid_user = factories.user()
        jt = sliced_jt_factory(3)
        jt.set_object_roles(valid_user, 'read')

        workflow_job = jt.launch()
        assert workflow_job.type == 'workflow_job'
        workflow_job.wait_until_completed()
        slice_result = v2.unified_jobs.get(unified_job_node__workflow_job=workflow_job.id).results[0]

        with self.current_user(invalid_user):
            with pytest.raises(Forbidden) as exc:
                workflow_job.get()
            assert exc.value.msg == {'detail': 'You do not have permission to perform this action.'}

            with pytest.raises(Forbidden) as exc:
                slice_result.get()
            assert exc.value.msg == {'detail': 'You do not have permission to perform this action.'}

        with self.current_user(valid_user):
            assert workflow_job.get().id == workflow_job.id
            assert slice_result.get().id == slice_result.id

    @pytest.mark.serial
    def test_job_template_slice_job_can_be_canceled(self, factories, v2, sliced_jt_factory):
        """Test that cancelling a sliced job cancels all workflow nodes"""
        jt = sliced_jt_factory(3, jt_kwargs=dict(playbook='sleep.yml', extra_vars={'sleep_interval': 15}))
        workflow_job = jt.launch().wait_until_started()
        slice_results = v2.unified_jobs.get(unified_job_node__workflow_job=workflow_job.id).results
        [s.wait_for_job() for s in slice_results]
        workflow_job.cancel().wait_until_status('canceled')
        assert workflow_job.status == 'canceled'
        for r in slice_results:
            r.get().wait_until_status('canceled')
            assert r.status == 'canceled'

    @pytest.mark.serial
    def test_job_template_slice_slices_can_be_canceled(self, factories, v2, sliced_jt_factory):
        """Test that canceling an individual slice does not cancel the sliced job or other nodes"""
        jt = sliced_jt_factory(3, jt_kwargs=dict(playbook='sleep.yml', extra_vars={'sleep_interval': 10}))
        workflow_job = jt.launch()
        workflow_job.wait_until_status('running')
        job_slices = workflow_job.related.workflow_nodes.get().results
        assert workflow_job.status == 'running'
        canceled_slice = job_slices[0]
        canceled_slice.wait_for_job(timeout=60)
        canceled_slice_job = canceled_slice.related.job.get()
        canceled_slice_job.cancel().wait_until_status('canceled')
        assert canceled_slice_job.get().status == 'canceled'
        for s in job_slices[1:]:
            s.wait_for_job(timeout=60)
            j = s.related.job.get()
            j.wait_until_completed()
            j.assert_successful()
        assert workflow_job.get().status == 'failed'

    def test_job_template_slice_with_smart_inventory(self, factories, v2, sliced_jt_factory):
        inventory = factories.inventory()

        for n in range(9):
            factories.host(name="test_host_{0}".format(
                str(n)), inventory=inventory)
            factories.host(name="excluded_host_{0}".format(
                str(n)), inventory=inventory)
        smart_inventory = factories.inventory(organization=inventory.ds.organization, host_filter="search=test_host",
                                                 kind="smart")
        assert smart_inventory.total_hosts == 9
        jt = sliced_jt_factory(3, jt_kwargs=dict(inventory=smart_inventory))
        workflow_job = jt.launch()
        assert workflow_job.type == 'workflow_job'
        workflow_job.wait_until_completed()
        workflow_job.assert_successful()
        for job in v2.unified_jobs.get(unified_job_node__workflow_job=workflow_job.id).results:
            assert job.get().host_status_counts['ok'] == 3

    def test_job_template_admin_can_set_slices(self, factories, sliced_jt_factory):
        org = factories.organization()
        inv = factories.inventory(organization=org)
        jt = factories.job_template(inventory=inv)
        user = factories.user(organization=org)
        org.set_object_roles(user, 'Job Template Admin')
        with self.current_user(user):
            jt.job_slice_count = 2
        assert jt.get().job_slice_count == 2
