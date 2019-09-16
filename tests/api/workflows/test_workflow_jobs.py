import logging
import re

import pytest
import awxkit
from awxkit.config import config
from awxkit.exceptions import NoContent
from awxkit.utils import poll_until

from tests.api import APITest
from tests.api.workflows.utils import get_job_node
from tests.lib.helpers.workflow_utils import (WorkflowTree, WorkflowTreeMapper)

# Job results
# [x] Single node success
# [x] Single failing node, workflow failed
# [x] Node fails, triggers failure node, workflow successful
# [x] Node fails, triggers failure node, 1 failure node fails, workflow failed
# [ ] Two branches, one node succeeds, other fails
# [ ] Individual job encounters error
# [ ] Workflow job encounters error
# [ ] Workflow job interrupted (e.g. by restarting tower)

# Job runs
# [x] Node triggers success/failure/always nodes when appropriate
# [x] Workflow includes multiple nodes that point to same unified job template
# [ ] Running concurrent workflows
# [ ] Changing job node while workflow is running
# [ ] Changing job template while workflow is running (change playbook, add survey, delete extra var..)
# [ ] Kicking off workflow when a job included in workflow has already been kicked off (as single job)
# [ ] Confirm including job template in workflow doesn't impair to run job template outside workflows
# [ ] Two workflows contain same node. Run both workflows at same time. Any collisions? (e.g. w/ artifacts)
# [ ] Using any misc settings (e.g. forks)

# Cancel
# [x] Cancelling individual job in workflow
# [x] Cancelling workflow

# Notifications
# [ ] For workflow's various states

# Timeouts
# [ ] On node
# [ ] On workflow

# Schedules
# [ ]

# Negative testing
# [ ] (-) No nodes
# [x] (-) Delete unified job template used by node, run job
# [ ] (-) Delete unified job template used by node, while workflow in progress
# [ ] (-) Should not be able to re-run a job that was a part of a larger workflow job
# [ ] Delete a job that was part of a larger workflow job?
# [ ] (-) Delete workflow job while in progress
# [ ] Add new nodes to workflow while workflow is in progress

# Extra vars / Surveys / Prompting
# [ ] Workflow survey with non-default variable
# [ ] Job template prompts for credential, inventory, project, ..
# [ ] Create workflow, update node job template to require additional variable (using prompting, surveys)
# [ ] Variable precedence testing

# Artifacts (break out into separate test module?)
# [ ] Artifacts cumulative?
# [ ] Sensitive artifacts not exposed

# Workflows and HA
# [ ] Project update during workflow job, does project get copied over to other nodes (race condition?).
# [ ] (Similiar to above) Inventory updates lead to race condition?
# [ ] (-) Workflow running, node brought down

# Workflow job nodes
#

# Activity Stream
#

# Deleting
# [ ] Deleting workflow job (possible?)
# [ ] Delete workflow job template, confirm workflow job (and regular jobs triggered as well) deleted
# [ ] Orphaned workflow jobs

log = logging.getLogger(__name__)


@pytest.mark.usefixtures('authtoken')
class Test_Workflow_Jobs(APITest):

    def test_inventory_source_correctly_referenced_in_related_job_endpoint(self, factories):
        """Confirms that inventory sources are treated as unified job templates in addition to confirming
        related workflow job nodes of inventory update types have correct url
        """
        inv_script = factories.inventory_script()
        inv_source = factories.inventory_source(source_script=inv_script)
        assert inv_source.source_script == inv_script.id
        wfjt = factories.workflow_job_template()
        factories.workflow_job_template_node(workflow_job_template=wfjt, unified_job_template=inv_source)
        wfj = wfjt.launch().wait_until_completed()
        wfjn = wfj.related.workflow_nodes.get().results.pop()
        assert('inventory_updates' in wfjn.related.job)  # confirm that it's not linked as a job
        assert(inv_source.related.inventory_updates.get().results.pop().endpoint == wfjn.related.job.get().endpoint)

    # Basic tests of workflow jobs

    @pytest.mark.ansible_integration
    def test_workflow_job_single_node_success(self, factories):
        """Workflow with single node with successful job template.
        Expect workflow job to be 'successful', job to be 'successful'
        """
        wfjt = factories.workflow_job_template()
        host = factories.host()
        jt = factories.job_template(inventory=host.ds.inventory)
        factories.workflow_job_template_node(workflow_job_template=wfjt, unified_job_template=jt)
        wf_job = wfjt.launch().wait_until_completed()
        wf_job.assert_successful()

        # Get job in node
        wfjns = wf_job.related.workflow_nodes.get().results
        assert len(wfjns) == 1, "Expected one workflow job node, found {}".format(len(wfjns))
        wfjn = wfjns.pop()
        job = wfjn.get_related('job')
        job.assert_successful()

        # Confirm WFJ correctly references job
        assert re.match(awxkit.resources.job, wfjn.related.job)
        assert wfjn.get_related('job').endpoint == jt.get().get_related('last_job').endpoint

    @pytest.mark.ansible_integration
    def test_workflow_job_single_node_failure(self, factories):
        """Workflow with single node with failing job template.
        Expect workflow job to fail, job to be 'failure'
        """
        wfjt = factories.workflow_job_template()
        host = factories.host()
        jt = factories.job_template(inventory=host.ds.inventory, playbook='fail_unless.yml')
        factories.workflow_job_template_node(workflow_job_template=wfjt, unified_job_template=jt)
        wf_job = wfjt.launch().wait_until_completed()
        assert wf_job.status == 'failed', "Workflow job {} should have failed".format(wfjt.id)

        # Get job in node
        wfjns = wf_job.related.workflow_nodes.get().results
        assert len(wfjns) == 1, "Expected one workflow job node, found {}".format(len(wfjns))
        job = wfjns.pop().get_related('job')
        assert job.status == 'failed', "Job {} successful".format(job.id)

    def test_workflow_job_successful_on_failed_when_failure_handler(self, factories):
        """Workflow: (sucessful)
         n1 (failed)       <--- failure
          - (failure) n2
         n2 (successful)
        """

        host = factories.host()
        jt = factories.job_template(inventory=host.ds.inventory, allow_simultaneous=True)
        failing_jt = factories.job_template(inventory=host.ds.inventory, playbook='fail_unless.yml', allow_simultaneous=True)

        wfjt = factories.workflow_job_template()
        n1 = factories.workflow_job_template_node(workflow_job_template=wfjt, unified_job_template=failing_jt)
        n1.related.failure_nodes.post(dict(unified_job_template=jt.id))

        wfj = wfjt.launch().wait_until_completed()
        wfj.assert_successful()

    def test_workflow_job_failed_on_failed_when_failed_failure_handler(self, factories):
        """Workflow: (sucessful)
         n1 (failed)       <--- failure
          - (failure) n2
          - (failure) n3
          - (failure) n4
          - (failure) n5
         n2 (successful)
         n3 (successful)
         n4 (failed)
         n5 (successful)
        """

        host = factories.host()
        jt = factories.job_template(inventory=host.ds.inventory, allow_simultaneous=True)
        failing_jt = factories.job_template(inventory=host.ds.inventory, playbook='fail_unless.yml', allow_simultaneous=True)

        wfjt = factories.workflow_job_template()
        n1 = factories.workflow_job_template_node(workflow_job_template=wfjt, unified_job_template=failing_jt)
        n1.related.failure_nodes.post(dict(unified_job_template=jt.id))
        n1.related.failure_nodes.post(dict(unified_job_template=jt.id))
        n1.related.failure_nodes.post(dict(unified_job_template=failing_jt.id))
        n1.related.failure_nodes.post(dict(unified_job_template=jt.id))

        wfj = wfjt.launch().wait_until_completed()
        assert 'failed' == wfj.status, "Workflow job {} expected to be failed {}".format(wfjt.id, wfjt.status)

    @pytest.mark.ansible_integration
    def test_workflow_job_trigger_conditions(self, factories, api_workflow_job_nodes_pg):
        """Confirm that workflow with all possible triggering scenarios executes jobs appropriately.

        Workflow:                        Should run?
         - n1+                           Yes
          - (always) n2                    Yes
          - (failure) nf                   No
          - (success) ns                   Yes
         - n3-                           Yes
          - (always) n4                    Yes
          - (always) n5*                   Yes
         - n6+                           Yes
          - (success) n7                   Yes
          - (failure) n8                   No
          - (failure) n9*                  No
         - n10-                          Yes
          - (success) n11                  No
          - (failure) n12                  Yes

        + -> node with passing job
        - -> node with failing job

        * -> Node not essential to test, added so that there could be a unique mapping (i.e. homomorphism) between
             the WFJT's nodes and the WFJ's nodes.
        """
        host = factories.host()
        jt = factories.job_template(inventory=host.ds.inventory, allow_simultaneous=True)
        failing_jt = factories.job_template(inventory=host.ds.inventory, playbook='fail_unless.yml', allow_simultaneous=True)

        wfjt = factories.workflow_job_template()
        node_payload = dict(unified_job_template=jt.id)
        n1 = factories.workflow_job_template_node(workflow_job_template=wfjt, unified_job_template=jt)
        # Confirms that always nodes can be run in conjunction with success and failure nodes
        # see https://github.com/ansible/awx/issues/2255
        n2 = n1.related.always_nodes.post(node_payload)
        nf = n1.related.failure_nodes.post(node_payload)
        ns = n1.related.success_nodes.post(node_payload)

        n3 = factories.workflow_job_template_node(workflow_job_template=wfjt, unified_job_template=failing_jt)
        n4 = n3.related.always_nodes.post(node_payload)
        n5 = n3.related.always_nodes.post(node_payload)

        n6 = factories.workflow_job_template_node(workflow_job_template=wfjt, unified_job_template=jt)
        n7 = n6.related.success_nodes.post(node_payload)
        n8 = n6.related.failure_nodes.post(node_payload)
        n9 = n6.related.failure_nodes.post(node_payload)

        n10 = factories.workflow_job_template_node(workflow_job_template=wfjt, unified_job_template=failing_jt)
        n11 = n10.related.success_nodes.post(node_payload)
        n12 = n10.related.failure_nodes.post(node_payload)

        wfj = wfjt.launch().wait_until_completed()
        wfj.assert_successful()

        # Map nodes to job nodes
        tree = WorkflowTree(wfjt)
        job_tree = WorkflowTree(wfj)
        mapping = WorkflowTreeMapper(tree, job_tree).map()
        assert mapping, "Failed to map WFJT to WFJ.\n\nWFJT:\n{0}\n\nWFJ:\n{1}".format(tree, job_tree)

        # Confirm only expected jobs ran
        should_run_ids = [str(mapping[node.id]) for node in [n1, n2, ns, n3, n4, n5, n6, n7, n10, n12]]
        should_run_nodes = api_workflow_job_nodes_pg.get(id__in=','.join(should_run_ids)).results
        assert all([node.job for node in should_run_nodes]), \
            "Found node(s) missing job: {0}".format(node for node in should_run_nodes if not node.job)
        should_not_run_ids = [str(mapping[node.id]) for node in [nf, n8, n9, n11]]
        should_not_run_nodes = api_workflow_job_nodes_pg.get(id__in=','.join(should_not_run_ids)).results
        assert not any([node.job for node in should_not_run_nodes]), \
            "Found node(s) with job: {0}".format(node for node in should_not_run_nodes if node.job)

    def test_workflow_job_with_project_update(self, factories):
        """Confirms that workflow job can include project updates."""
        project = factories.project()
        wfjt = factories.workflow_job_template()
        factories.workflow_job_template_node(workflow_job_template=wfjt, unified_job_template=project)
        wfj = wfjt.launch().wait_until_completed()
        wfjn = wfj.related.workflow_nodes.get().results.pop()
        assert re.match(awxkit.resources.project_update, wfjn.related.job)
        assert wfjn.get_related('job').endpoint == project.get().get_related('last_job').endpoint

    # Canceling jobs

    def test_cancel_workflow_job_pre_spawn(self, factories):
        host = factories.host()
        jt_sleep = factories.job_template(inventory=host.ds.inventory, playbook='sleep.yml')  # Longer-running job
        jt_sleep.extra_vars = '{"sleep_interval": 120}'
        wfjt = factories.workflow_job_template()
        factories.workflow_job_template_node(workflow_job_template=wfjt, unified_job_template=jt_sleep)

        wfj = wfjt.launch()
        wfj.cancel()
        wfj.wait_until_status('canceled')

        # workflow job is canceled, it should:
        #  - not spawn any jobs after its finished / canceled time
        #  - not have any running jobs after it is marked canceled
        job_node = wfj.get_related('workflow_nodes').results.pop()
        if job_node.job is None:
            return  # cancel happened before nodes spawned, this is fine
        job = job_node.get_related('job')
        assert job.get().status == 'canceled'
        assert job.created < wfj.finished

    def test_cancel_workflow_job(self, factories):
        """Confirm that cancelling a workflow job cancels spawned jobs."""
        # Build workflow
        host = factories.host()
        jt_sleep = factories.job_template(inventory=host.ds.inventory, playbook='sleep.yml')  # Longer-running job
        jt_sleep.extra_vars = '{"sleep_interval": 20}'
        wfjt = factories.workflow_job_template()
        factories.workflow_job_template_node(workflow_job_template=wfjt, unified_job_template=jt_sleep)

        # Run workflow
        wfj = wfjt.launch()

        # Wait for workflow job to spawn job
        job_nodes = wfj.get_related('workflow_nodes')
        assert len(job_nodes.results) == 1, "Only expecting one job node, found:\n\n{0}".format(job_nodes)
        job_node = job_nodes.results.pop()
        job_node.wait_for_job(timeout=60)  # Job does not exist until kicked off by workflow
        job = job_node.get_related('job')

        # Wait for spawned job to enter running state
        job.wait_until_status('running')

        # ..then cancel workflow job
        wfj.cancel()
        poll_until(lambda: getattr(wfj.get(), 'status') == 'canceled', timeout=3 * 60)

        # Confirm job spawned by workflow job was canceled
        assert job.get().status == 'canceled'

    def test_cancel_job_spawned_by_workflow_job(self, factories):
        """Cancel job spawned by workflow job. Confirm workflow job finishes and is marked successful.

        Workflow:
         n1     <--- cancelled
        """
        host = factories.host()
        jt_sleep = factories.job_template(inventory=host.ds.inventory, playbook='sleep.yml', extra_vars='{"sleep_interval": 20}',
                                          allow_simultaneous=True)  # Longer-running job

        # Build workflow
        wfjt = factories.workflow_job_template()
        factories.workflow_job_template_node(workflow_job_template=wfjt, unified_job_template=jt_sleep)

        # Run workflow
        wfj = wfjt.launch()

        # Get job node
        job_nodes = wfj.related.workflow_nodes.get().results
        assert len(job_nodes) == 1, 'Expected workflow job to have single node, found:\n\n{0}'.format(job_nodes)
        job_node = job_nodes[0]

        # Wait for node's job to be created
        job_node.wait_for_job(timeout=60)
        assert getattr(job_node, 'job', None), 'Failed to find job listed on node {}'.format(job_node)

        # Cancel job
        job = job_node.related.job.get()
        job.cancel()

        # Confirm job cancelled
        poll_until(lambda: getattr(job.get(), 'status') == 'canceled', timeout=60)

        # Confirm WF job failed
        wfj.wait_until_status('failed', since_job_created=False)

    def test_cancel_job_in_workflow_with_downstream_jobs(self, factories, api_jobs_pg):
        """Cancel job spawned by workflow job. Confirm jobs downstream from canceled job
        are not triggered, but rest of workflow continues to execute.

        Workflow:
         n1                 <--- canceled
          - (success) dnr_n2  <--- should be marked Do Not Run
          - (failure) failure_path_for_canceled_node_n3 <--- should run because canceled jobs are treated as failed
          - (always) always_path_for_canceled_nA <--- should run because canceled jobs are treated as failed
         n4
          - (always) n5

        Expect:
         - Nodes downstream from n1 (includes n2, n3) should not run.
         - Rest of workflow (includes n4, n5) should run to completion.
         - WFJ should succeed because failure path node for canceled job should succeed
        """
        # Create jobs for workflow
        # Note: Both root jobs sleep so that (1) there's time to cancel n1 and (2) n4 does not finish before n1 is
        # canceled. We need n4 to still be running when n1 is cancelled so that we can verify that downstream jobs (n5)
        # are triggered *after* n1 is canceled.

        host = factories.host()
        jt = factories.job_template(inventory=host.ds.inventory)                            # Default job template for all nodes
        jt_sleep = factories.job_template(inventory=host.ds.inventory, playbook='sleep.yml', extra_vars='{"sleep_interval": 20}',
                                          allow_simultaneous=True)  # Longer-running job

        # Build workflow
        wfjt = factories.workflow_job_template()
        node_payload = dict(unified_job_template=jt.id)
        n1 = factories.workflow_job_template_node(workflow_job_template=wfjt, unified_job_template=jt_sleep)
        dnr_n2 = n1.related.success_nodes.post(node_payload)
        always_path_for_canceled_nA = n1.related.always_nodes.post(node_payload)
        failure_path_for_canceled_node_n3 = n1.related.failure_nodes.post(node_payload)
        n4 = factories.workflow_job_template_node(workflow_job_template=wfjt, unified_job_template=jt_sleep)
        n5 = n4.related.always_nodes.post(node_payload)

        # Run workflow
        wfj = wfjt.launch()

        # Get mapping
        # Note: When a workflow job is launched, it immediately creates one WFJ node for every WFJT node
        # in the WFJT (even if that WFJ node's job is never launched). This allows us to create a mapping,
        # even when only the jobs for the root nodes are running. (Otherwise, there would be two possible
        # mappings and it wouldn't be clear which job we should cancel).
        mapping = WorkflowTreeMapper(WorkflowTree(wfjt), WorkflowTree(wfj)).map()
        error = ('Expected Workflow Job to have same tree structure as Workflow Job Template.\n\n'
                 'Workflow Job Template:\n\n{0}\n\nWorkflow Job:\n\n{1}').format(WorkflowTree(wfjt), WorkflowTree(wfj))
        assert mapping, error

        n1_job_node = wfj.related.workflow_nodes.get(id=mapping[n1.id]).results.pop()
        dnr_n2_job_node = wfj.related.workflow_nodes.get(id=mapping[dnr_n2.id]).results.pop()
        failure_path_n3_job_node = wfj.related.workflow_nodes.get(id=mapping[failure_path_for_canceled_node_n3.id]).results.pop()
        always_path_nA_job_node = wfj.related.workflow_nodes.get(id=mapping[always_path_for_canceled_nA.id]).results.pop()
        n4_job_node = wfj.related.workflow_nodes.get(id=mapping[n4.id]).results.pop()
        n5_job_node = wfj.related.workflow_nodes.get(id=mapping[n5.id]).results.pop()

        # Cancel job spawned by job node n1
        n1_job_node.wait_for_job(timeout=60)  # Job does not exist until kicked off by workflow
        assert getattr(n1_job_node, 'job', None), 'Failed to find job for node {}'.format(n1_job_node)
        n1_job = n1_job_node.related.job.get()
        n1_job.cancel()

        poll_until(lambda: getattr(n1_job.get(), 'status') == 'canceled', timeout=60)

        # Confirm workflow job fails
        wfj.wait_until_completed()
        wfj.assert_successful()
        # Confirm remaining jobs in workflow completed successfully
        for job_node in (n4_job_node, n5_job_node, failure_path_n3_job_node, always_path_nA_job_node):
            job_node.get()
            assert getattr(job_node, 'job', None), 'Failed to find job listed on node {}'.format(job_node)
            assert job_node.get_related('job').status == 'successful'

        # Confirm job downstream from cancelled job never triggered
        dnr_n2_job_node = dnr_n2_job_node.get()
        assert not getattr(dnr_n2_job_node, 'job', None), \
            'Found job listed on node {} that should have been marked DNR because was success child of canceled node'.format(job_node)
        assert dnr_n2_job_node.do_not_run, "Node was not marked Do Not Run even though was success child of canceled node."

    @pytest.mark.parametrize('dependency', ['inventory', 'project'])
    def test_downstream_jt_jobs_fail_appropriately_when_missing_deleted_dependencies(self, factories, dependency):
        wfjt = factories.workflow_job_template()
        jt = factories.job_template()
        factories.workflow_job_template_node(workflow_job_template=wfjt, unified_job_template=jt)

        getattr(jt.ds, dependency).delete()

        wfj = wfjt.launch().wait_until_completed()
        assert wfj.status == 'failed'
        assert wfj.failed
        job = jt.get().related.last_job.get()
        assert job.status == 'failed'
        assert job.failed
        assert job.job_explanation == 'Job spawned from workflow could not start because it was missing a related resource ' \
                                      'such as project or inventory'

    def test_workflow_job_fails_when_encounter_node_with_deleted_job_template(self, factories):
        """When JTs get deleted out from under a WFJT node, the WF should abort when it encounters it.

        WFJT looks like this:

        ancestor:
          - n0 (always) wfjt that succeeds
          - n1 (always) wfjt that succeeds
        n0:
          - n2 (always) jt that gets deleted
          - n3 (failure) jt that gets deleted
          - n5 (success) jt that gets deleted
        n1:
          - n2 (always) jt that gets deleted
          - n3 (failure) jt that gets deleted
          - n4 (success) jt that gets deleted
          - n5 (success) jt that gets deleted
        n2:
          - n2_child (success) wfjt that would succeed (but should not run)
        n3:
          - n3_child (always) wfjt that would succeed (but should not run because n3 should not run because is failure node for both parents that succceed)
        n4:
          - n4_child (failure) wfjt that should run and succeed as error handler of parent
        n5:
          - n5_child (always) wfjt that should run and succeed as error handler of parent

        Expect:
          - WFJ runs and completes
          - WFJ is marked failed
          - ancestor runs and succeeds
          - n0 runs and succeeds
          - n1 runs and succeeds
          - n4_child runs and succeeds
          - n5_child runs and succeeds
          - workflow job nodes spawned from n2, n3, n4, n5 have no jobs associated
          - workflow job nodes spawned from n2, n3, n4, n5 should be marked DNR
          - workflow job nodes spawned from n2, n3, n4, n5 have no unified job templates associated
          - workflow job nodes spawned from n2_child, n3_child have no jobs associated
          - workflow job nodes spawned from n2_child, n3_child should be marked DNR
          - The fact that n2's job node had no JT associated and no error path should be the reason the WF is marked failed
        """
        wfjt = factories.workflow_job_template()
        wfjt_inner = factories.workflow_job_template()
        jt_to_delete = factories.job_template()
        ancestor = factories.workflow_job_template_node(workflow_job_template=wfjt, unified_job_template=jt_to_delete)
        n0 = factories.workflow_job_template_node(workflow_job_template=wfjt, unified_job_template=jt_to_delete)
        n1 = factories.workflow_job_template_node(workflow_job_template=wfjt, unified_job_template=jt_to_delete)
        ancestor.unified_job_template = wfjt_inner.id
        n0.unified_job_template = wfjt_inner.id
        n1.unified_job_template = wfjt_inner.id
        with pytest.raises(NoContent):
            ancestor.related.always_nodes.post(dict(id=n0.id))
        with pytest.raises(NoContent):
            ancestor.related.always_nodes.post(dict(id=n1.id))
        n2 = n1.add_always_node(unified_job_template=jt_to_delete)
        n3 = n1.add_failure_node(unified_job_template=jt_to_delete)
        n4 = n1.add_success_node(unified_job_template=jt_to_delete)
        n5 = n1.add_success_node(unified_job_template=jt_to_delete)
        with pytest.raises(NoContent):
            n0.related.always_nodes.post(dict(id=n2.id))
        with pytest.raises(NoContent):
            n0.related.failure_nodes.post(dict(id=n3.id))
        with pytest.raises(NoContent):
            n0.related.success_nodes.post(dict(id=n4.id))
        with pytest.raises(NoContent):
            n0.related.success_nodes.post(dict(id=n5.id))
        n2_child = n2.add_success_node(unified_job_template=jt_to_delete)
        n2_child.unified_job_template = wfjt_inner.id
        n3_child = n3.add_always_node(unified_job_template=jt_to_delete)
        n3_child.unified_job_template = wfjt_inner.id
        n4_child = n4.add_failure_node(unified_job_template=jt_to_delete)
        n4_child.unified_job_template = wfjt_inner.id
        n5_child = n5.add_always_node(unified_job_template=jt_to_delete)
        n5_child.unified_job_template = wfjt_inner.id

        # delete the jt
        jt_to_delete.delete()

        wfj = wfjt.launch().wait_until_completed()
        assert wfj.status == 'failed'
        assert wfj.failed
        tree = WorkflowTree(wfjt)
        job_tree = WorkflowTree(wfj)
        mapping = WorkflowTreeMapper(tree, job_tree).map()

        # Confirm only expected jobs ran
        # This includes the "always" and "failure" nodes for the nodes with deleted JTs
        for node, message in [(ancestor, 'root node of whole workflow'),
                              (n0, 'first parent of nodes with JTs deleted'),
                              (n1, 'second parent of nodes with JTs deleted'),
                              (n4_child, 'failure child of node with JT deleted'),
                              (n5_child, 'always child of node with JT deleted')]:
            job_node = get_job_node(wfj, node.id, mapping)
            assert job_node.unified_job_template == wfjt_inner.id, 'JT was unexpectedly changed for {}'.format(message)
            assert job_node.related.job.get(), 'No job found for {}'.format(message)
            assert job_node.related.job.get().status == 'successful', '{} in wf where later nodes are missing JTs did not succeed!'.format(message)

        # Confirm that the nodes with the deleted JT did not run and do not have a JT
        for node in [n2, n3, n4, n5]:
            job_node = get_job_node(wfj, node.id, mapping)
            assert job_node.unified_job_template is None, 'The node that should be missing a JT has a JT for some reason!'
            assert job_node.job is None, 'Node missing a JT somehow had a job spawned!'

        # Confirm that the success child of a node with a deleted JT did not run
        n2_child_job_node = get_job_node(wfj, n2_child.id, mapping)
        assert n2_child_job_node.unified_job_template == wfjt_inner.id, 'The JT got changed on a node that should not have been modified!'
        assert n2_child_job_node.job is None, 'A success child of a node with a JT deleted was run!'
        assert n2_child_job_node.do_not_run is True

        # Confirm that the child of a node with a deleted JT that also did not have any triggering parent did not run
        n3_child_job_node = get_job_node(wfj, n3_child.id, mapping)
        assert n3_child_job_node.unified_job_template == wfjt_inner.id, 'The JT got changed on a node that should not have been modified!'
        assert n3_child_job_node.job is None, 'The always child of a node that should not have run anyway (no triggering parent) and who had its JT deleted ran when it should not have.'
        assert n3_child_job_node.do_not_run is True

        # assert error message include relavent info
        assert 'No error handling paths found, marking workflow as failed' in wfj.job_explanation

    @pytest.mark.serial
    def test_awx_metavars_for_workflow_jobs(self, v2, factories, update_setting_pg):
        update_setting_pg(
            v2.settings.get().get_endpoint('jobs'),
            dict(ALLOW_JINJA_IN_EXTRA_VARS='always')
        )
        wfjt = factories.workflow_job_template()
        jt = factories.job_template(playbook='debug_extra_vars.yml',
                                       extra_vars='var1: "{{ awx_workflow_job_id }}"\nvar2: "{{ awx_user_name }}"')
        factories.host(inventory=jt.ds.inventory)
        factories.workflow_job_template_node(workflow_job_template=wfjt, unified_job_template=jt)
        wf_job = wfjt.launch().wait_until_completed()
        wf_job.assert_successful()

        # Get job in node
        wfjns = wf_job.related.workflow_nodes.get().results
        wfjn = wfjns.pop()
        job = wfjn.get_related('job')
        job.assert_successful()
        assert '"var1": "{}"'.format(wf_job.id) in job.result_stdout
        assert '"var2": "{}"'.format(config.credentials.users.admin.username) in job.result_stdout
