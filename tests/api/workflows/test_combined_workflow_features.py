import json

import pytest
from awxkit.exceptions import NoContent

from tests.api import APITest
from tests.api.workflows.utils import get_job_node
from tests.lib.helpers.workflow_utils import (WorkflowTree, WorkflowTreeMapper)


@pytest.mark.usefixtures('authtoken')
class TestCombinedWorkflowFeatures(APITest):
    """This class of tests focuses on interoperability of various workflow features.

    The features of interest are:
        * Workflows in Workflows
        * Convergence nodes
        * Do Not Run logic introduced by Convergence node feature
        * Sliced Job Templates (that spawn workflow jobs)
        * Workflow level inventory
        * Workflow level extra_vars
    """

    @pytest.fixture(autouse=True)
    def setup_common_resources(self, class_factories):
        factories = class_factories
        self.host = factories.host()
        self.outer_inventory = factories.inventory()
        self.inner_inventory = factories.inventory()
        self.OUTER_HOSTS = 3
        self.INNER_HOSTS = 2
        # This is intentionally larger than both OUTER_HOSTS and INNER_HOSTS
        # so that as many slices will be launched as there are hosts
        self.NUM_SLICES = 5
        for i in range(self.OUTER_HOSTS):
            self.outer_inventory.add_host()
        for i in range(self.INNER_HOSTS):
            self.inner_inventory.add_host()
        self.jt_regular = factories.job_template(
            inventory=self.host.ds.inventory,
            allow_simultaneous=True
        )
        self.jt_ask_on_launch = factories.job_template(
            inventory=self.inner_inventory,
            allow_simultaneous=True,
            ask_inventory_on_launch=True,
            ask_variables_on_launch=True
        )
        self.jt_failure = factories.job_template(
            inventory=self.host.ds.inventory,
            allow_simultaneous=True,
            playbook='fail_unless.yml'
        )
        self.wfjt_inner = factories.workflow_job_template(
            inventory=self.inner_inventory
        )
        self.wfjt_inner_ask_on_launch = factories.workflow_job_template(
            ask_inventory_on_launch=True,
            inventory=self.inner_inventory,
            ask_variables_on_launch=True
        )
        self.sliced_jt = factories.job_template(
            job_slice_count=self.NUM_SLICES,
            allow_simultaneous=True
        )
        self.sliced_jt_inventory = self.sliced_jt.ds.inventory
        for i in range(self.INNER_HOSTS):
            self.sliced_jt_inventory.add_host()
        self.sliced_jt_ask_inventory_on_launch = factories.job_template(
            job_slice_count=self.NUM_SLICES,
            allow_simultaneous=True,
            ask_inventory_on_launch=True,
            ask_variables_on_launch=True,
            inventory=self.inner_inventory
        )

    def validate_sjt_inside_wf_inside_wf(self, inner_wf_job, additional_assertions=[]):
        """Pass additional assertions as a list of callables that take the sliced joblet extra_vars as an argument.

        The extra vars of the individual "joblet" from the sliced job workflow job will be a dictionary.

        These callables should raise sensible error messages that provide sufficient information
        to understand a test failure.
        """
        sjt_workflow_job_node = inner_wf_job.related.workflow_nodes.get().results.pop()
        wf_spawned_from_sjt = sjt_workflow_job_node.related.job.get()
        sliced_nodes = wf_spawned_from_sjt.related.workflow_nodes.get()
        # should match OUTER_HOSTS becaused used outer workflow inventory
        assert sliced_nodes.count == self.OUTER_HOSTS, 'Unexpected number of nodes were spawned in sliced job!'
        for node in sliced_nodes.results:
            assert node.summary_fields.job.status == 'successful', 'Node in wf spawned from sliced jt failed!'
            node.related.job.get().assert_successful()
            sjt_job_vars = json.loads(node.related.job.get().extra_vars)
            assert sjt_job_vars.get('outer_var') == 'outer_var'
            for assertion in additional_assertions:
                assertion(sjt_job_vars)

    def test_set_stats_propagate_correctly_through_workflow(self, instance_group, factories):
        """Assert that artifacts from set_stats playbooks are passed from node to node.

        This test is parametrized to have job templates run on both regular instances and isolated instances
        (when in a cluster, other wise the isolated case skips).
        """
        wfjt = factories.workflow_job_template(
            extra_vars={'outer_var': 'outer_var'},
            inventory=self.outer_inventory
        )

        set_stats_vars = {
            'set_stats_data': {
                    'acow': 'jumped over the moon',
                    'apig': {
                        'flew': 2
                        }
                    }
            }
        set_stats_jt = factories.job_template(playbook='test_set_stats.yml', extra_vars=set_stats_vars)
        set_stats_jt.add_instance_group(instance_group)
        set_stats_root_node = factories.workflow_job_template_node(
            workflow_job_template=wfjt,
            unified_job_template=set_stats_jt
        )
        # Make sure set stats flow through project update
        abuelo = set_stats_root_node.add_success_node(
            unified_job_template=factories.inventory_source()
        )
        # Make sure set stats flow through project update.
        parent = abuelo.add_success_node(
            unified_job_template=factories.project()
        )
        # Make sure set stats flow through approval node.
        approval_node = factories.workflow_job_template_node(
            workflow_job_template=wfjt,
            unified_job_template=None
            ).make_approval_node()
        with pytest.raises(NoContent):
            parent.related.always_nodes.post(dict(id=approval_node.id))

        approval_jt = approval_node.related.unified_job_template.get()
        run_and_succeed = approval_node.add_always_node(unified_job_template=self.jt_regular)
        run_and_fail = run_and_succeed.add_success_node(unified_job_template=self.jt_failure)
        convergenece_node = parent.add_always_node(unified_job_template=self.jt_regular)
        with pytest.raises(NoContent):
            run_and_fail.related.always_nodes.post(dict(id=convergenece_node.id))
        wf_use_outer_inv = convergenece_node.add_success_node(
            unified_job_template=self.wfjt_inner_ask_on_launch
        )
        jt_use_outer_inv = convergenece_node.add_success_node(
            unified_job_template=self.jt_ask_on_launch
        )

        # put a SJT node that asks for inventory inside WFJ that asks for
        # inventory inside the outer WF
        factories.workflow_job_template_node(
            workflow_job_template=self.wfjt_inner_ask_on_launch,
            unified_job_template=self.sliced_jt_ask_inventory_on_launch,
        )

        wfj = wfjt.launch().wait_until_status('running')
        set_stats_root_node_job_node = wfj.related.workflow_nodes.get(unified_job_template=set_stats_jt.id).results.pop()
        set_stats_job = set_stats_root_node_job_node.wait_for_job(timeout=120).related.job.get()
        set_stats_job.wait_until_completed()
        parent_job_node = wfj.related.workflow_nodes.get(unified_job_template=parent.summary_fields.unified_job_template.id).results.pop()
        parent_job = parent_job_node.wait_for_job(timeout=120).related.job.get()
        parent_job.wait_until_completed()
        approval_job_node = wfj.related.workflow_nodes.get(unified_job_template=approval_jt.id).results.pop()
        wf_approval = approval_job_node.wait_for_job(timeout=120).related.job.get()
        wf_approval.wait_until_status('pending')

        # Approve so the workflow will proceed
        wf_approval.approve()

        # Unhandled failed nodes will cause WF to be marked failed
        wfj = wfj.wait_until_completed()
        assert wfj.status == 'successful'
        tree = WorkflowTree(wfjt)
        job_tree = WorkflowTree(wfj)
        mapping = WorkflowTreeMapper(tree, job_tree).map()

        # Assert all nodes we expected jobs to run and fail failed
        for node in [run_and_fail, ]:
            assert get_job_node(wfj, node.id, mapping).summary_fields.job.status == 'failed'

        # Assert all nodes we expected jobs to run and succeed did so
        for node in [run_and_succeed, parent, convergenece_node]:
            assert get_job_node(wfj, node.id, mapping).summary_fields.job.status == 'successful'

        for node in [wf_use_outer_inv, jt_use_outer_inv]:
            job = get_job_node(wfj, node.id, mapping).related.job.get()
            assert job.status == 'successful'
            assert job.inventory == self.outer_inventory.id
            assert json.loads(job.extra_vars).get('outer_var', 'MISSING VAR!') == 'outer_var', 'Inner unified job template did not inherit extra var!'

        # Assert the SJT inside the WF that prompted for inventory used the outer
        # inventory
        inner_wf_job_node = wfj.related.workflow_nodes.get(unified_job_template=self.wfjt_inner_ask_on_launch.id).results.pop()
        inner_wf_job = inner_wf_job_node.related.job.get()
        # Assert the job node has the correct wfjt in it
        assert inner_wf_job.related.unified_job_template.get().id == self.wfjt_inner_ask_on_launch.id, 'Unexpected job template found on node'

        def _found_set_stats_data_on_sjt_job(job_vars):
            assert job_vars.get('acow') == 'jumped over the moon', 'Missing var on sliced job template joblet that should have been inherited via set_stats!'
            assert job_vars.get('apig', {}).get('flew') == 2, 'Missing var on sliced job template joblet that should have been inherited via set_stats!'

        self.validate_sjt_inside_wf_inside_wf(inner_wf_job, additional_assertions=[_found_set_stats_data_on_sjt_job])

    def test_workflow_with_dead_branches_marked_dnr(self, factories):
        # Create detached section of workflow where some branches should be
        # marked DNR
        wfjt = factories.workflow_job_template(
            extra_vars={'outer_var': 'outer_var'},
            inventory=self.outer_inventory
        )
        ancestor = factories.workflow_job_template_node(
            workflow_job_template=wfjt,
            unified_job_template=self.jt_regular
        )
        run_and_succeed = ancestor.add_always_node(unified_job_template=self.jt_regular)
        run_and_fail = run_and_succeed.add_success_node(unified_job_template=self.jt_failure)
        dnr1 = run_and_fail.add_success_node(unified_job_template=self.jt_failure)
        dnr2 = dnr1.add_success_node(unified_job_template=self.jt_failure)
        dnr3 = run_and_succeed.add_failure_node(unified_job_template=self.jt_regular)
        dnr4 = dnr3.add_failure_node(unified_job_template=self.jt_regular)
        dnr5 = dnr2.add_always_node(unified_job_template=self.jt_regular)
        convergenece_node = ancestor.add_always_node(unified_job_template=self.jt_regular)
        wf_use_outer_inv = convergenece_node.add_success_node(
            unified_job_template=self.wfjt_inner_ask_on_launch
        )
        jt_use_outer_inv = convergenece_node.add_success_node(
            unified_job_template=self.jt_ask_on_launch
        )

        # put a SJT node that asks for inventory inside WFJ that asks for
        # inventory inside the outer WF
        factories.workflow_job_template_node(
            workflow_job_template=self.wfjt_inner_ask_on_launch,
            unified_job_template=self.sliced_jt_ask_inventory_on_launch,
        )

        with pytest.raises(NoContent):
            dnr1.related.success_nodes.post(dict(id=convergenece_node.id))
        with pytest.raises(NoContent):
            dnr2.related.failure_nodes.post(dict(id=convergenece_node.id))
        with pytest.raises(NoContent):
            dnr3.related.always_nodes.post(dict(id=convergenece_node.id))

        wfj = wfjt.launch().wait_until_completed()
        # Unhandled failed nodes will cause WF to be marked failed
        assert wfj.status == 'failed'
        tree = WorkflowTree(wfjt)
        job_tree = WorkflowTree(wfj)
        mapping = WorkflowTreeMapper(tree, job_tree).map()

        # Assert the SJT inside the WF that prompted for inventory used the outer
        # inventory
        inner_wf_job_node = wfj.related.workflow_nodes.get(unified_job_template=self.wfjt_inner_ask_on_launch.id).results.pop()
        inner_wf_job = inner_wf_job_node.related.job.get()
        # Assert the job node has the correct wfjt in it
        assert inner_wf_job.related.unified_job_template.get().id == self.wfjt_inner_ask_on_launch.id, 'Unexpected job template found on node'
        self.validate_sjt_inside_wf_inside_wf(inner_wf_job)

        # Assert all DNR nodes got marked Do Not Run
        for node in [dnr1, dnr2, dnr3, dnr4, dnr5]:
            assert get_job_node(wfj, node.id, mapping).do_not_run

        # Assert all nodes we expected jobs to run and fail failed
        for node in [run_and_fail, ]:
            assert get_job_node(wfj, node.id, mapping).summary_fields.job.status == 'failed'

        # Assert all nodes we expected jobs to run and succeed did so
        for node in [run_and_succeed, ancestor, convergenece_node]:
            assert get_job_node(wfj, node.id, mapping).summary_fields.job.status == 'successful'

        for node in [wf_use_outer_inv, jt_use_outer_inv]:
            job = get_job_node(wfj, node.id, mapping).related.job.get()
            assert job.status == 'successful'
            assert job.inventory == self.outer_inventory.id
            assert json.loads(job.extra_vars).get('outer_var', 'MISSING VAR!') == 'outer_var', 'Inner unified job template did not inherit extra var!'

    @pytest.mark.yolo
    def test_dense_workflow(self, factories): # noqa C901
        wfjt = factories.workflow_job_template(
            extra_vars={'outer_var': 'outer_var'},
            inventory=self.outer_inventory
        )
        # put a SJT node that asks for inventory inside WFJ that asks for
        # inventory inside the outer WF
        factories.workflow_job_template_node(
            workflow_job_template=self.wfjt_inner_ask_on_launch,
            unified_job_template=self.sliced_jt_ask_inventory_on_launch,
        )
        dense_graph_nodes = []
        # Create section dense section of workflow where the graph is as
        # connected as it possibly can be
        # Use 6 since we have 6 different type JTs to choose from
        NUM_DENSE_NODES = 6
        for i in range(NUM_DENSE_NODES):
            if i % 6 == 0:
                jt = self.jt_regular
            if i % 6 == 1:
                jt = self.wfjt_inner
            if i % 6 == 2:
                jt = self.sliced_jt
            if i % 6 == 3:
                jt = self.jt_failure
            if i % 6 == 4:
                jt = self.jt_ask_on_launch
            if i % 6 == 5:
                jt = self.wfjt_inner_ask_on_launch
            # HACK, provide some jt to prevent one being made. Then replaced
            # with the desired jt
            node = factories.workflow_job_template_node(
                workflow_job_template=wfjt,
                unified_job_template=self.jt_regular
            )
            node.unified_job_template = jt.id
            dense_graph_nodes.append(node)
        for i, parent in enumerate(dense_graph_nodes):
            for k, child in enumerate(dense_graph_nodes[i + 1:]):
                with pytest.raises(NoContent):
                    if k % 3 == 0:
                        parent.related.always_nodes.post(dict(id=child.id))
                    if k % 3 == 1:
                        parent.related.success_nodes.post(dict(id=child.id))
                    if k % 3 == 2:
                        parent.related.failure_nodes.post(dict(id=child.id))

        wfj = wfjt.launch().wait_until_completed()
        assert wfj.status == 'successful'
        tree = WorkflowTree(wfjt)
        job_tree = WorkflowTree(wfj)
        mapping = WorkflowTreeMapper(tree, job_tree).map()

        for node in dense_graph_nodes:
            job_node = get_job_node(wfj, node.id, mapping)
            # make sure we have working links
            this_jt = job_node.related.unified_job_template.get()
            this_job = job_node.related.job.get()

            # Does job reach expected state?
            if this_jt.id == self.jt_failure.id:
                assert this_job.status == 'failed'
            else:
                assert this_job.status == 'successful'
                this_job.assert_successful()

            if this_jt.id == self.sliced_jt.id:
                # assert correct number of slices
                sliced_nodes = this_job.related.workflow_nodes.get()
                assert sliced_nodes.count == self.INNER_HOSTS, 'Unexpected number of nodes were spawned in sliced job!'
                for node in sliced_nodes.results:
                    assert node.summary_fields.job.status == 'successful', 'Node in wf spawned from sliced jt failed!'
                    node.related.job.get().assert_successful()

            # Did SJT inside inner WF with 'ask_inventory_on_launch' propagate the outer inventory correctly?
            if this_jt.id == self.wfjt_inner_ask_on_launch:
                # Assert the SJT inside the WF that prompted for inventory used the
                # outer inventory
                self.validate_sjt_inside_wf_inside_wf(this_job)

            # Is WF level inventory applied correctly?
            if this_jt.id in [
                self.wfjt_inner_ask_on_launch.id,
                self.jt_ask_on_launch.id
            ]:
                assert this_job.inventory == self.outer_inventory.id
            else:
                assert this_job.inventory != self.outer_inventory.id

            # Are WF extra_vars inventory applied correctly?
            if this_jt.id in [
                self.wfjt_inner_ask_on_launch.id,
                self.jt_ask_on_launch.id,
                self.jt_regular.id,
                self.jt_failure.id,
                self.sliced_jt.id
            ]:
                # UNFORTUNATELY _all_ regular job templates inherit workflow level vars regarless of ask_on_launch value
                assert json.loads(this_job.extra_vars).get('outer_var', 'MISSING VAR!') == 'outer_var', 'Inner unified job template did not inherit extra var!'
            else:
                assert json.loads(this_job.extra_vars).get('outer_var') is None, 'Inner unified job template should not inherit extra var!'
