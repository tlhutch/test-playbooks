import pytest
import logging

from tests.api import Base_Api_Test
from towerkit.exceptions import BadRequest

log = logging.getLogger(__name__)

# Variations in structure
# [ ] Single node
# [x] Multiple root nodes
# [x] Node Depth > 1
# [x] (-) Circular graph
# [ ] Can add node by (a) citing WFJT during node creation, (b) patching node w/ WFJT, (c) posting new node on /workflow_job_templates/\d+/workflow_nodes/

# Copy
# [ ]

# Labels
# [ ]

# Notifications
# [ ] On workflow job template
# [ ] On regular jobs

# Tags / Limits
# [ ]

# Extra vars
# [ ]

# Deleting
# [ ] Delete workflow with single node
# [ ] Delete intermediate node (with node(s) before/after)
# [ ] Delete leaf node
# [ ] Deleting root node when depth > 1
# [ ]


@pytest.mark.api
@pytest.mark.skip_selenium
@pytest.mark.destructive
class Test_Workflow_Job_Templates(Base_Api_Test):

    pytestmark = pytest.mark.usefixtures('authtoken', 'install_enterprise_license_unlimited')

    # Graph Topology Validation
    # Graphs should not (1) converge (2) contain cycles or
    # (3) trigger the same node in both always_nodes and {success,failure}_nodes

    def test_converging_nodes(self, factories):
        '''Confirms that two nodes cannot trigger the same node'''
        wfjt = factories.workflow_job_template()
        # Create two top-level nodes
        n1 = factories.workflow_job_template_node(workflow_job_template=wfjt)
        jt = n1.related.unified_job_template.get()  # Reuse job template from first node
        n2 = factories.workflow_job_template_node(workflow_job_template=wfjt, unified_job_template=jt)

        # Create third node. Have each root node trigger third node.
        n3 = n1.related.always_nodes.post(dict(unified_job_template=jt.id))
        for condition in ('always', 'success', 'failure'):
            with pytest.raises(BadRequest) as exception:
                n2.get_related(condition + '_nodes').post(dict(id=n3.id))
            assert 'Multiple parent relationship not allowed.' in str(exception.value)

            # Confirm nodes were not linked
            triggered_nodes = n2.get_related(condition + '_nodes').results
            assert not len(triggered_nodes), \
                'Found nodes listed, expected none. (Creates converging path in workflow):\n{0}'.format(triggered_nodes)

    def test_single_node_references_itself(self, factories):
        '''Confirms that a node cannot trigger itself'''
        wfjt = factories.workflow_job_template()
        n = factories.workflow_job_template_node(workflow_job_template=wfjt)
        for condition in ('always', 'success', 'failure'):
            with pytest.raises(BadRequest) as exception:
                n.get_related(condition + '_nodes').post(dict(id=n.id))
            assert 'Cycle detected.' in str(exception.value)

            # Confirm node not linked to itself
            triggered_nodes = n.get_related(condition + '_nodes').results
            assert not len(triggered_nodes), \
                'Found nodes listed, expected none. (Creates cycle in workflow):\n{0}'.format(triggered_nodes)

    def test_cyclic_graph(self, factories):
        '''Confirms that a graph cannot contain a cycle'''
        # Create two nodes. First node triggers second node.
        wfjt = factories.workflow_job_template()
        n1 = factories.workflow_job_template_node(workflow_job_template=wfjt)
        jt = n1.related.unified_job_template.get()  # Reuse job template from first node
        n2 = n1.related.always_nodes.post(dict(unified_job_template=jt.id))

        # Second node triggers the first (creates cycle)
        for condition in ('always', 'success', 'failure'):
            with pytest.raises(BadRequest) as exception:
                n2.get_related(condition + '_nodes').post(dict(id=n1.id))
            assert 'Cycle detected.' in str(exception.value)

            # Confirm nodes were not linked
            triggered_nodes = n2.get_related(condition + '_nodes').results
            assert not len(triggered_nodes), \
                'Found nodes listed, expected none. (Creates cycle in workflow):\n{0}'.format(triggered_nodes)

    # TODO: Add more advaced test for cyclic graphs (e.g. testing graph with depth, braches, usage
    #      of different types of edges)

    def test_node_triggers_should_be_mutually_exclusive(self, factories):
        '''Confirms that if a node is listed under `always_nodes`, it cannot also be
           listed under `{success, failure}_nodes`.'''
        # Create two nodes. First node set to _always_ trigger second node.
        wfjt = factories.workflow_job_template()
        n1 = factories.workflow_job_template_node(workflow_job_template=wfjt)
        jt = n1.related.unified_job_template.get()  # Reuse job template from first node
        n2 = n1.related.always_nodes.post(dict(unified_job_template=jt.id))

        # First node set to trigger second node using success / failure
        for condition in ('success', 'failure'):
            with pytest.raises(BadRequest) as exception:
                n1.get_related(condition + '_nodes').post(dict(id=n2.id))
            error_msg = 'Cannot associate {}_nodes when always_nodes have been associated.'.format(condition)
            assert error_msg in str(exception.value)

            # Confirm nodes were not linked
            triggered_nodes = n1.get_related(condition + '_nodes').results
            assert not len(triggered_nodes), \
                'Found nodes listed, expected none. (Creates triggers that should be mutually exclusive):\n{0}'.format(triggered_nodes)
