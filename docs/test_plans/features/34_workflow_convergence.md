# Workflow Convergence Node

## Scenarios to test

### Convergence node

- [x] Confirm that convergence job can take the form of any job type supported by workflows
    - [x] The converngence node can be an inventory update
    - [x] The convergence node can be a project update
    - [x] The convergence node can be a job template
    - [ ] The convergence node can be a workflow job template (To be implemented in "monster" workflow test case)

### Valid workflows

- [x] Confirm that convergence node can be
	- [x] .. the final node in a workflow job
	- [x] .. an intermediate node in a workflow job

### Modified workflows

- [x] Confirm that when an intermediate node that triggers a convergence node is deleted, that (a) all other nodes that previously triggered the convergence node still trigger the convergence node and (b) the parent of the deleted node *does not* trigger the convergence node.

### Dense workflows

- [x] Create and run a dense DAG with workflow job template nodes in ascending order (add each new node as a child of all previous nodes)
    - [x] 10
    - [x] 50
- [x] Create and run a dense DAG with workflow job template nodes in descending order (after creating all nodes, construct graph using node with highest id as root node, and work through list backwards )
    - [x] 10
    - [x] 50
    - Data: https://docs.google.com/spreadsheets/d/1FdryO2PcQ7ItQLx5WTW7Qtu7UEP1GnY8gEcurwScQZk/edit?usp=sharing
Note: it was determined the "longest pole" is the fact that the WF jobs only start every 20 seconds due to how scheduler is run.
- [x] Confirm that the time to add nodes to large graphs does not grow exponentially
    - The time to add nodes does not grow appreciably.
- [x] Assert that job completes

### Illegal workflows

- [x] Confirm that a convergence node cannot trigger itself using any possible trigger event (success, failure, always)
- [x] Confirm that you cannot create a cycle in workflows using convergence jobs

### Passing data between jobs

- [x] Confirm set_stats vars are [inherited correctly](https://gist.github.com/jladdjr/fa7acf58f937f4ff5d9475dc31340ade) by the 'convergence node' (for all possible types of jobs that the converge job can take - project update, inventory sync, regular job, possible ad hoc command if that is supported in 3.4)
    - [x] Confirm that unique keys from parent jobs are merged correctly (they are all present)
    - [x] Confirm that shared keys from parent jobs are merged correctly given precedence (highest precedence wins all for each given key)
- [x] That set_stats variables are correctly received by a convergence job..
	- [x] Data is passed from failed nodes if `set_stats` is called before failure occurs
    - [x] Data is passed from nodes that succeed
	- [x] When the path to the 'convergence node' involves a single node along some paths and multiple nodes along other paths
	- [x] When some jobs involved in the convergence experience a failure

### Error conditions

- [x] Confirm that if no parent reached a state that a convergence node should be triggered by, then it does not run.

### Path execution

- [x] Confirm that workflow job nodes have the new `do_no_run` field set correctly for a variety of workflow topologies
- [x] Confirm that convergence job does not start running until all nodes leading into convergence node have completed or been marked with [new `do_not_run` field](https://github.com/ansible/awx/pull/2389/files#diff-a81324c523b41de7296fdd5ff9063d10R3867)
- [x] Confirm that convergence node can be triggered by parent node by way of all three trigger conditions:
    - [x] always
    - [x] success
    - [x] failure
- [x] Confirm that convergence node does not start if final running node is in waiting, pending, or running state
- [x] Confirm that convergence node runs even if final remaining parent node to the convergence node experiences an error or fails
- [x] Confirm that if convergence node has an "failure" relation to a parent, and it is canceled, this triggers the convergence node
- [x] Confirm that workflows with convergence nodes behave correctly when re-launched (this test is a little more than just path execution)

### Deep / complex workflows
- [x] Confirm that if there is a large / complex / deep set of jobs that enter a variety of states (success, failure, error) along different branches preceding a convergence node, the jobs still converges
- [x] Confirm that two or more convergence nodes, can themselves point to a convergence node
- [x] Confirm that you can have a workflow job steeped in convergence nodes

### RBAC / Security

- [x] Confirm that sensitive data is not exposed in any of the data (jt_extra_vars, extra_vars, set_stats vars) passed to a convergence node (or surfaced elsewhere indirectly - e.g. activity stream)
    - These nodes behave the same as all other nodes in this respect
- [x] Confirm that RBAC for creating a convergence node is the same as RBAC for creating other nodes in a workflow
    - These nodes behave the same as all other nodes in this respect

### Misc

- [x] Confirm that convergence nodes correctly send notifications
    - These nodes behave the same as all other nodes in this respect

### UI
- [ ] Confirm that the workflow job template editor can correctly handle various ways of creating / deleting convergence nodes
- [ ] Confirm that the workflow job template editor correctly renders the same workflow job template when closed and re-opened multiple times (should the layout of the WFJT be stable across editor sessions?)
- [ ] Confirm that the workflow job UI correctly shows workflow jobs with convergence nodes in progress for all the different scenarios listed for the API tests ^
