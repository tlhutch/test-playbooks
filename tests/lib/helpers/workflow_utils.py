import logging

# Utilities for testing workflows

log = logging.getLogger(__name__)


class WorkflowTree(object):
    """Represents workflow tree structure. Can be built manually, but also has
    a constructor that supports building a `WorkflowTree` using a
    `WorkflowJobTemplate` or `WorkflowJob` page.

    ex:
    # Create tree based on WFJT page object
    >>> wfjt = v2.workflow_job_templates.get(id=1).results.pop()
    >>> tree1 = WorkflowTree(wfjt)

    # Create tree by hand
    >>> tree2 = WorkflowTree()
    >>> tree2.add_nodes(1, 2, 3)
    >>> tree2.add_edge(1, 2, 'success')

    # Assert equality
    >>> assert tree1 == tree2
    """

    def __init__(self, workflow=None):
        """Initialize `WorkflowTree`. May optionally provide reference to a
        `WorkflowJobTemplate` or `WorkflowJob` object.
        """
        self._graph = {}

        if workflow:
            # Get nodes
            try:
                workflow.get()
                nodes = workflow.get_related('workflow_nodes').results
            except:
                log.error("Unable to get 'workflow_nodes' from:\n{}".format(workflow))
                raise

            # Process nodes
            for node in nodes:
                self._graph[node.id] = {}
                for condition in ('always', 'failure', 'success'):
                    triggered_node_ids = getattr(node, condition + '_nodes', set())
                    if len(triggered_node_ids):
                        self._graph[node.id][condition] = set(triggered_node_ids)

    def __repr__(self):
        return str(self._graph)

    def __str__(self):
        output = ['Nodes  Edges', '-----  -----------------']
        if not len(self._graph):
            output.append('(No nodes)')
            return '\n'.join(output)

        nodes = sorted(self._graph.keys())
        for node in nodes:
            line = '{0:<5}  '.format(node)
            conditions = sorted(self._graph[node].keys())
            for condition in conditions:
                line += '{0}: {1} '.format(condition, list(self._graph[node][condition]))
            output.append(line)
        return '\n'.join(output)

    def __eq__(self, workflow_tree):
        return self._graph == workflow_tree._graph

    def __ne__(self, workflow_tree):
        return self._graph != workflow_tree._graph

    def get_node(self, id):
        """Returns a node. If node does not exist, returns `None`."""
        return self._graph.get(id)

    def add_node(self, id, always_nodes=[], failure_nodes=[], success_nodes=[]):
        """Add single node to workflow tree. Requires id of node.
        May optionally specify triggered nodes using lists of integers.

        Raises `Exception` if node with `id` already exists.
        Raises `Exception` if node includes edges to nodes that do not exist.

        ex:
        >>> tree = WorkflowTree()
        >>> tree.add_nodes(3)
        >>> tree.add_node(2, always_nodes=[3])
        >>> tree.add_node(1, sucess_nodes=[2,3])
        """
        # Node should not already exist
        if id in self._graph:
            raise Exception("Cannot create node '{}'; node already exists.".format(id))

        # Edge nodes should already exist
        edge_nodes = set(always_nodes + failure_nodes + success_nodes)
        for node in edge_nodes:
            if node not in self._graph:
                error = "Cannot create node '{}'. Includes edge to node '{}', which does not exist.".format(id, node)
                raise Exception(error)

        self._graph[id] = {}

        if always_nodes:
            self._graph[id]['always'] = set(always_nodes)
        if failure_nodes:
            self._graph[id]['failure'] = set(failure_nodes)
        if success_nodes:
            self._graph[id]['success'] = set(success_nodes)

    def add_nodes(self, *ids):
        """Add one or more nodes to workflow tree.

        Raises `Exception` if node with id found in `ids` already exists.
        (If this happens, no nodes are created).

        ex:
        >>> tree = WorkflowTree()
        >>> tree.add_nodes(1)
        >>> tree.add_nodes(2, 3, 4)
        """
        # Cannot reference same node more than once
        if len(ids) != len(set(ids)):
            raise Exception('Cannot reference same id more than once. Given: {}'.format(ids))

        # Cannot already have any nodes with id found in `ids`
        for id in ids:
            if id in self._graph:
                raise Exception("Cannot create node '{}'; node already exists.".format(id))

        for id in ids:
            self._graph[id] = {}

    def remove_nodes(self, *ids):
        """Remove one or more nodes from workflow tree.

        Automatically removes any edges that referred to deleted nodes.

        Note that nodes must already exist, otherwise raises `Exception`.
        If ids contains a reference to a node that is not in the
        `WorkflowTree`, no nodes will be deleted.
        """
        if not len(ids):
            return

        # All nodes must exist
        for id in ids:
            if id not in self._graph:
                raise Exception('Cannot delete node {}. Node does not exist.'.format(id))

        # Delete nodes
        for id in ids:
            del self._graph[id]

        # Clean-up any edges that referred to deleted nodes
        ids = set(ids)
        for id in self._graph:
            # Get all keys in advance (otherwise, size of dict may change, interrupting iteration)
            conditions = self._graph[id].keys()
            for condition in conditions:
                self._graph[id][condition] = self._graph[id][condition] - ids
                if not len(self._graph[id][condition]):
                    del self._graph[id][condition]

    def add_edge(self, node, triggered_node, condition):
        """Adds an edge from `node` to `triggered_node` of type `condition`.

        Note that both `node` ande `triggered_node` must both exist, otherwise
        raises `Exception`.

        `condition` must be one of 'always', 'failure', or 'success', otherwise
        raises `Exception`.

        >>> tree = WorkflowTree()
        >>> tree.add_nodes(1)
        >>> tree.add_nodes(2)
        >>> tree.add_edge(1, 2, 'always')
        """
        if condition not in ('always', 'failure', 'success'):
            raise Exception("Node {0}: cannot add edge of type '{1}'.".format(node, condition))
        if node not in self._graph:
            raise Exception("Cannot add edge; node '{}' does not exist.".format(node))
        if triggered_node not in self._graph:
            raise Exception("Cannot add edge; second node '{}' does not exist.".format(triggered_node))
        if condition not in self._graph[node]:
            self._graph[node][condition] = set([])

        self._graph[node][condition].add(triggered_node)

    def remove_edge(self, node, triggered_node, condition):
        """Removes an edge from `node` to `triggered_node` of type `condition`.

        * `condition` must be one of 'always', 'failure', or 'success', otherwise raises `Exception`.
        * If edge does not exist, raises `ExceptionError`.
        """
        if condition not in ('always', 'failure', 'success'):
            raise Exception("Node {0}: cannot remove edge of type '{1}'.".format(node, condition))
        if node not in self._graph:
            raise Exception('Cannot remove edge from node {0}; node does not exist.'.format(node))
        if condition not in self._graph[node] or triggered_node not in self._graph[node][condition]:
            raise Exception("Cannot remove edge of type '{0}' from node '{1}'; edge does not exist.".format(condition, node))

        self._graph[node][condition].remove(triggered_node)

        if not len(self._graph[node][condition]):
            del self._graph[node][condition]


class WorkflowTreeMapper(object):
    """Finds a mapping of one graph's nodes onto the other's.
    (i.e. a graph homomorphism).
    """

    def __init__(self, tree1, tree2):
        """Create `WorkflowTreeMapper` with references
        to two `WorkflowTree`s being compared.
        """
        self._tree1 = tree1
        self._tree2 = tree2

    def _get_root_nodes(self, tree):
        """Gets the root nodes for a given tree."""
        nodes = tree._graph.keys()

        # Node is root node if it is not triggered by any
        # other node
        triggered_nodes = []
        for node in nodes:
            for condition in tree._graph[node]:
                triggered_nodes.extend(tree._graph[node][condition])

        return list(set(nodes) - set(triggered_nodes))

    def _match(self, node1, node2):
        """Two nodes match if they have the same number
        of edges (for each edge type).
        """
        for condition in node1:
            if condition not in node2:
                return False
            if len(node1[condition]) != len(node2[condition]):
                return False
        return True

    def map(self):
        """Returns a dictionary containing a one-to-one
        mapping of nodes from `self.tree1` to nodes from `self.tree2`
        if a mapping exists. Returns None if mapping does not exist.

        Note that method does not guarantee that
        mapping is unique.
        """
        root_nodes1 = self._get_root_nodes(self._tree1)
        root_nodes2 = self._get_root_nodes(self._tree2)
        return self._map(root_nodes1, root_nodes2)

    def _map(self, root_nodes1, root_nodes2):
        """Returns a dictionary containing a one-to-one
        mapping of nodes from `root_nodes1` to nodes from `root_nodes2`
        if a mapping exists. Returns None if mapping does not exist.

        Note that method does not guarantee that
        mapping is unique.
        """
        # If number of root nodes differ on each side,
        # then no mapping exists
        if len(root_nodes1) != len(root_nodes2):
            return None

        # If there are no nodes, nothing to be done
        if not len(root_nodes1):
            return {}

        # Map first root node
        node1 = root_nodes1[0]

        # ..to one of the root nodes in second graph
        for node2 in root_nodes2:
            temp_mapping = {}

            # If the two nodes are a match..
            if self._match(self._tree1._graph[node1], self._tree2._graph[node2]):
                temp_mapping = {node1: node2}

                # Recursively map each set of trigger nodes
                mapping_successful = True
                for condition in self._tree1._graph[node1]:
                    trigger_nodes1 = list(self._tree1._graph[node1][condition])
                    trigger_nodes2 = list(self._tree2._graph[node2][condition])
                    mapping = self._map(trigger_nodes1, trigger_nodes2)

                    if mapping:
                        temp_mapping.update(mapping)
                    else:
                        mapping_successful = False
                        break

                # If recursive mapping not successful,
                # attempt to map node1 to different node
                if not mapping_successful:
                    continue

                # Attempt to map remaining root nodes
                if len(root_nodes1) == 1:
                    # This was the last root node, return results
                    return temp_mapping

                # (Use list to create copy)
                new_root_nodes1 = list(root_nodes1)
                new_root_nodes2 = list(root_nodes2)
                new_root_nodes1.remove(node1)
                new_root_nodes2.remove(node2)
                mapping = self._map(new_root_nodes1, new_root_nodes2)

                # If mapping successful, then the mapping is complete
                if mapping:
                    temp_mapping.update(mapping)
                    return temp_mapping

                # Otherwise, try to map node1 to next node

        # No mapping found
        return None
