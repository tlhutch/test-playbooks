import pytest

from tests.lib.helpers.workflow_utils import WorkflowTree, WorkflowTreeMapper


class MockNode:

    def __init__(self, id, always_nodes=[], failure_nodes=[], success_nodes=[]):
        self.id = id
        self.always_nodes = set(always_nodes)
        self.failure_nodes = set(failure_nodes)
        self.success_nodes = set(success_nodes)


class MockNodes:
    """Wraps `MockNode` objects to provide `results` attribute."""

    def __init__(self, nodes=[]):
        self.results = nodes


class MockWorkflowJobTemplate:
    """Mocks WorkflowJobTemplate page object"""

    def __init__(self, nodes=[]):
        """Optionally takes list of `MockNode` objects"""
        self.nodes = MockNodes(nodes)

    def get(self):
        return self

    def get_related(self, item):
        """ignore `item`. WorkflowTree only uses `get_related`
        for getting 'workflow_nodes'.
        """
        return self.nodes

######################
# WorkflowTree tests #
######################


@pytest.mark.parametrize('node', [0, -1, 5])
def test_get_node_from_empty_tree(node):
    """Confirms getting node that does not exist returns None"""
    t = WorkflowTree()
    assert not len(t._graph), 'Tree should be empty when first created'
    assert t.get_node(node) is None, 'Tree empty, but found node ({})'.format(id)


def test_add_nodes_without_edges():
    """Create single node. Shouldn't find any edges on node."""
    t = WorkflowTree()
    t.add_nodes(1)
    n1 = t.get_node(1)

    # Assert dictionary representing node is empty (i.e. has no edges)
    assert not len(n1), 'Found edges (non expected): {}'.format(n1)


def test_add_node():
    """Confirm can successfully add single node using `add_nodes`"""
    t = WorkflowTree()
    t.add_nodes(1)
    assert len(t._graph) == 1, 'WorkflowTree should have single node'
    assert 1 in t._graph, 'Expected node 1 to be in WorkflowTree'
    assert not len(t._graph[1]), 'Node 1 should not have any edges:\n{}'.format(t._graph[1])


def test_add_nodes():
    """Confirm can successfully add multiple single node using `add_nodes`"""
    t = WorkflowTree()
    nodes = [1, 2, 3, 4]
    t.add_nodes(*nodes)
    assert len(t._graph) == len(nodes),\
        'WorkflowTree should have {0} nodes, found {1}'.format(len(nodes), len(t._graph))
    for node in nodes:
        assert node in t._graph, 'Expected node {} to be in WorkflowTree'.format(node)


def test_add_node_with_edge_to_node_that_does_not_exist():
    """Confirm that attempting to create a node with an edge
    to a node that does not exist, `Exception` is raised.
    """
    t = WorkflowTree()
    error = 'Should not be able to create node with edge to node that does not exist.'
    with pytest.raises(Exception):
        t.add_node(1, always_nodes=[2])
        pytest.fail(error)

    with pytest.raises(Exception):
        t.add_node(1, always_nodes=[2, 3])
        pytest.fail(error)

    t.add_nodes(2)
    with pytest.raises(Exception):
        t.add_node(1, always_nodes=[2, 3])  # Still missing node 3
        pytest.fail(error)

    with pytest.raises(Exception):
        t.add_node(1, always_nodes=[2], success_nodes=[3])
        pytest.fail(error)

    t.add_nodes(3)
    with pytest.raises(Exception):
        t.add_node(1, always_nodes=[2], success_nodes=[3, 4])  # Missing node 4
        pytest.fail(error)


def test_add_node_with_edges():
    """Confirm that adding a node with edges is successful."""
    t = WorkflowTree()
    t.add_nodes(2)
    t.add_nodes(3)
    t.add_nodes(4)
    t.add_node(1, success_nodes=[2], failure_nodes=[3, 4])
    n1 = t.get_node(1)

    # Assert node has expected edges
    assert n1['success'] == set([2]), \
        "Expected 'success' edge to node 2, found edge(s) to: {}".format(n1['success'])
    assert n1['failure'] == set([3, 4]), \
        "Expected 'failure' edges to nodes 3 and 4, found edge(s) to: {}".format(n1['failure'])
    assert 'always' not in n1, "Did not expect 'always' edges"


@pytest.mark.parametrize('node', [-1, 0, 5])
def test_remove_node_that_does_not_exist(node):
    """Confirm that removing node that does not exist raises `Exception`"""
    t = WorkflowTree()
    with pytest.raises(Exception):
        t.remove_nodes(node)
        pytest.fail('Expect `Exception` when deleting node that does not exist')


def test_remove_node():
    """Confirm can successfully remove node."""
    t = WorkflowTree()
    t.add_nodes(1)
    assert len(t._graph) == 1, 'Expected single node in graph'
    assert 1 in t._graph, 'Expected node 1 in graph'

    t.remove_nodes(1)
    assert not len(t._graph), 'Expected graph to be empty after removing node.'


def test_remove_node_with_edges():
    """Confirm can successfully remove nodes."""
    t = WorkflowTree()
    t.add_nodes(4, 5)
    t.add_node(1, always_nodes=[4])
    t.add_node(2, success_nodes=[4])
    t.add_node(3, failure_nodes=[4, 5])

    t.remove_nodes(4)
    assert 'always' not in t._graph[1]
    assert 'success' not in t._graph[2]
    assert 'failure' in t._graph[3]
    assert 5 in t._graph[3]['failure']


def test_add_edge_when_nodes_missing():
    """Confirms cannot add edge when either node is missing"""
    t = WorkflowTree()

    with pytest.raises(Exception):
        t.add_edge(1, 2, 'always')
        pytest.fail('Should not be able to add edge when second node missing.')

    t.add_nodes(2)
    with pytest.raises(Exception):
        t.add_edge(1, 2, 'always')
        pytest.fail('Should not be able to add edge when second node missing.')

    t.remove_nodes(2)
    t.add_nodes(1)
    with pytest.raises(Exception):
        t.add_edge(1, 2, 'always')
        pytest.fail('Should not be able to add edge when second node missing.')


def test_add_edge():
    """Confirms can successfully add edge"""
    t = WorkflowTree()
    t.add_nodes(1, 2)
    t.add_edge(1, 2, 'always')

    # Confirm edge created
    assert 1 in t._graph
    assert 'always' in t._graph[1]
    assert 'success' not in t._graph[1]
    assert 'failure' not in t._graph[1]
    assert t._graph[1]['always'] == set([2])


def test_remove_edge_that_does_not_exist():
    """Confirm that removing edge that does not exist raises `Exception`"""
    t = WorkflowTree()

    # Remove edge when nodes do not exist
    with pytest.raises(Exception):
        t.remove_edge(1, 2, 'always')
        pytest.fail('Removing edge that does not exist should raise `Exception`')

    t.add_nodes(1)
    # Remove edge when second node do not exist
    with pytest.raises(Exception):
        pytest.fail('Removing edge that does not exist should raise `Exception`')

    t.add_nodes(2)
    # Remove edge when edge does not exist
    with pytest.raises(Exception):
        t.remove_edge(1, 2, 'always')
        pytest.fail('Removing edge that does not exist should raise `Exception`')


def test_remove_edges():
    """Confirm removing edge that exists is successful"""
    t = WorkflowTree()
    t.add_nodes(2, 3)
    t.add_node(1, success_nodes=[2, 3])
    n1 = t.get_node(1)
    assert n1['success'] == set([2, 3]), \
        'Created node with 2 edges, but cannot find edges. Edge(s) found: {}'.format(n1['success'])

    t.remove_edge(1, 3, 'success')
    assert n1['success'] == set([2]), \
        'Removed edge (to node 3), expected to find one remaining edge (to node 2). Found: {}'\
        .format(n1['success'])

    t.remove_edge(1, 2, 'success')
    assert 'success' not in n1, \
        "Removed last 'success' edge, but still found edges. Found: {}"\
        .format(n1['success'])


def fixture_for_equality_tests():
    """Builds:
    - `WorkflowTree` constructed based on (mock) `WorkflowJobTemplate` object, and
    - Manually constructed `WorkflowTree`

     Workflow:
      n1:
       - always: n2
      n3:
       - success: n4
       - failure: n5
      n6:
       - always: n7
         - always: n8
           - always: n9
      n10
    """
    # Build WorkflowTree from (mock) WorkflowJobTemplate
    n1 = MockNode(1, always_nodes=[2])
    n2 = MockNode(2)
    n3 = MockNode(3, success_nodes=[4], failure_nodes=[5])
    n4 = MockNode(4)
    n5 = MockNode(5)
    n6 = MockNode(6, always_nodes=[7])
    n7 = MockNode(7, always_nodes=[8])
    n8 = MockNode(8, always_nodes=[9])
    n9 = MockNode(9)
    n10 = MockNode(10)

    nodes = [n1, n2, n3, n4, n5, n6, n7, n8, n9, n10]
    wfjt = MockWorkflowJobTemplate(nodes)
    wfjt_tree = WorkflowTree(wfjt)

    # Build WorkflowTree 'manually'
    tree = WorkflowTree()
    tree.add_nodes(1, 2, 3, 4, 5, 6, 7, 8, 9, 10)
    tree.add_edge(1, 2, 'always')
    tree.add_edge(3, 4, 'success')
    tree.add_edge(3, 5, 'failure')
    tree.add_edge(6, 7, 'always')
    tree.add_edge(7, 8, 'always')
    tree.add_edge(8, 9, 'always')

    return wfjt_tree, tree


def test_equality_when_trees_are_equal():
    """Test equality when trees have same structure."""
    wfjt_tree, tree = fixture_for_equality_tests()

    # Test (in)equality when trees are same
    assert wfjt_tree == tree,\
        ('Expected trees to be equal.' +
         '\n\nWFJT Tree:\n\n{0}\n\n(Manually-built) Tree:\n\n{1}').format(wfjt_tree, tree)
    assert not wfjt_tree != tree,\
        ('Expected inequality to be false (i.e. trees to be same).' +
         '\n\nWFJT Tree:\n\n{0}\n\n(Manually-built) Tree:\n\n{1}').format(wfjt_tree, tree)


def test_equality_when_one_edge_missing():
    """Test equality when one tree is missing an edge."""
    wfjt_tree, tree = fixture_for_equality_tests()

    # Trees should be different if edge is missing
    tree.remove_edge(1, 2, 'always')
    assert not wfjt_tree == tree,\
        ('Expected trees to *not* be equal (missing edge).' +
         '\n\nWFJT Tree:\n\n{0}\n\n(Manually-built) Tree:\n\n{1}').format(wfjt_tree, tree)
    assert wfjt_tree != tree,\
        ('Expected inequality to be true (i.e. trees to be different) due to missing edge.' +
         '\n\nWFJT Tree:\n\n{0}\n\n(Manually-built) Tree:\n\n{1}').format(wfjt_tree, tree)


def test_equality_when_extra_edge_present():
    """Test equality when one tree has an extra edge."""
    wfjt_tree, tree = fixture_for_equality_tests()

    # Trees should be different if extra edge is present
    tree.add_edge(9, 10, 'success')
    assert not wfjt_tree == tree,\
        ('Expected trees to *not* be equal (extra edge).' +
         '\n\nWFJT Tree:\n\n{0}\n\n(Manually-built) Tree:\n\n{1}').format(wfjt_tree, tree)
    assert wfjt_tree != tree,\
        ('Expected inequality to be true (i.e. trees to be different) due to extra edge.' +
         '\n\nWFJT Tree:\n\n{0}\n\n(Manually-built) Tree:\n\n{1}').format(wfjt_tree, tree)


def test_equality_when_node_missing():
    """Test equality when one tree is missing a node."""
    wfjt_tree, tree = fixture_for_equality_tests()

    # Trees should be different if node is missing
    tree.remove_nodes(10)
    assert not wfjt_tree == tree,\
        ('Expected trees to *not* be equal (missing node).' +
         '\n\nWFJT Tree:\n\n{0}\n\n(Manually-built) Tree:\n\n{1}').format(wfjt_tree, tree)
    assert wfjt_tree != tree,\
        ('Expected inequality to be true (i.e. trees to be different) due to missing node.' +
         '\n\nWFJT Tree:\n\n{0}\n\n(Manually-built) Tree:\n\n{1}').format(wfjt_tree, tree)


def test_equality_when_extra_node_present():
    """Test equality when one tree has an extra node."""
    wfjt_tree, tree = fixture_for_equality_tests()

    # Trees should be different if extra node is present
    tree.add_nodes(11)
    assert not wfjt_tree == tree,\
        ('Expected trees to *not* be equal (extra node).' +
         '\n\nWFJT Tree:\n\n{0}\n\n(Manually-built) Tree:\n\n{1}').format(wfjt_tree, tree)
    assert wfjt_tree != tree,\
        ('Expected inequality to be true (i.e. trees to be different) due to extra.' +
         '\n\nWFJT Tree:\n\n{0}\n\n(Manually-built) Tree:\n\n{1}').format(wfjt_tree, tree)


############################
# WorkflowTreeMapper tests #
############################

def fixture_for_simple_mapping_tests():
    """Builds two trees of form:

    Workflow:
     n1:
      - (always) n2
     n3
    """
    tree1 = WorkflowTree()
    tree1.add_nodes(1, 2, 3)
    tree1.add_edge(1, 2, 'success')

    tree2 = WorkflowTree()
    tree2.add_nodes(11, 12, 13)
    tree2.add_edge(11, 12, 'success')

    return tree1, tree2


def test_map_simple_trees():
    """Forms mapping between two simple trees
    (that are identical in structure, but
    have different node ids).
    """
    tree1, tree2 = fixture_for_simple_mapping_tests()
    mapping = WorkflowTreeMapper(tree1, tree2).map()

    assert mapping == {1: 11, 2: 12, 3: 13}


def test_map_simple_trees_differing_by_single_node():
    """Tests mapping trees that differ by single node."""
    tree1, tree2 = fixture_for_simple_mapping_tests()
    tree1.add_nodes(4)

    mapping = WorkflowTreeMapper(tree1, tree2).map()
    assert mapping is None


def test_map_simple_trees_differing_by_single_edge():
    """Tests mapping trees that differ by single edge."""
    tree1, tree2 = fixture_for_simple_mapping_tests()
    tree1.add_edge(1, 3, 'failure')

    mapping = WorkflowTreeMapper(tree1, tree2).map()
    assert mapping is None


def test_map_trees_with_similar_root_nodes():
    """Forms mapping between two trees with similar
    root nodes.

    Workflow:
     n1:
      - (always) n2
       - (success) n3
       - (success) n4
        - (failure) n5
     n6:
      - (always) n7
       - (failure) n8
    """
    tree1 = WorkflowTree()
    tree1.add_nodes(1, 2, 3, 4, 5, 6, 7, 8)
    tree1.add_edge(1, 2, 'always')
    tree1.add_edge(2, 3, 'success')
    tree1.add_edge(2, 4, 'success')
    tree1.add_edge(4, 5, 'failure')
    tree1.add_edge(6, 7, 'always')
    tree1.add_edge(7, 8, 'failure')

    tree2 = WorkflowTree()
    tree2.add_nodes(11, 12, 13, 14, 15, 16, 17, 18)
    tree2.add_edge(11, 12, 'always')
    tree2.add_edge(12, 13, 'success')
    tree2.add_edge(12, 14, 'success')
    tree2.add_edge(14, 15, 'failure')
    tree2.add_edge(16, 17, 'always')
    tree2.add_edge(17, 18, 'failure')

    mapping = WorkflowTreeMapper(tree1, tree2).map()

    assert mapping == {1: 11, 2: 12, 3: 13, 4: 14,
                       5: 15, 6: 16, 7: 17, 8: 18}
