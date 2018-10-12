# Workflow Convergence Node

## Scenarios to test

### Convergence node

- [ ] Confirm that convergence job can take the form of any job type supported by workflows

### Valid workflows

- [ ] Confirm that convergence node can be
	- [ ] .. the final node in a workflow job
	- [ ] .. an intermediate node in a workflow job

### Illegal workflows

- [ ] Confirm that a convergence node cannot trigger itself using any possible trigger event (success, failure, always)
- [ ] Confirm that you cannot create a cycle in workflows using convergence jobs

### Passing data between jobs

- [ ] Confirm jt_extra_vars, extra_vars, set_stats vars are inherited correctly by the 'convergence node'
	- [ ] When some nodes pass and others fail
	- [ ] When the path to the 'convergence node' involves a single node along some paths and multiple nodes along other paths
	- [ ] When some jobs involved in the convergence experience an error
- [ ] That jt_extra_vars, extra_vars, and set_stats variables are correctly received by a convergence job for all possible types of jobs that the converge job can take (project update, inventory sync, regular job, possible ad hoc command if that is supported in 3.4)

### Error conditions

- [ ] Confirm that if all jobs leading into convergence node experience an error, then child node is not triggered
- [ ] Confirm that if at least one job leading into a convergence node hangs indefinitely (in pending or waiting state), then convergence node never runs
- [ ] Confirm that if workflow job is interrupted (e.g. due to nodes being taken offline) before a convergence node is able to begin
	- [ ] .. and workflow job automatically resumes (e.g. after node is brought back online), then convergence happens correctly
	- [ ] .. and workflow job is reaped, then convergence node does not run / all jobs in workflow stop.
- [ ] Confirm that when the job template associated with a convergence node is deleted, and the workflow job is run, that at the point the workflow reaches the convergence node, that particular job completes with an error status (and that the subsequent events in the workflow reflect what would normally happen if a node encountered an error)

### Path execution

- [ ] Confirm that convergence job does not start running until all nodes leading into convergence node have completed
- [ ] Confirm that convergence node can be triggered by parent node by way of all three trigger conditions (always, success, failure)
- [ ] Confirm that convergence node does not start if final running node is in waiting, pending, or running state
- [ ] Confirm that convergence mode runs even if final node experiences an error
- [ ] Confirm that workflows with convergence nodes behave correctly when re-launched (this test is a little more than just path execution)

### Deep / complex workflows
- [ ] Confirm that if there is a large / complex / deep set of jobs that enter a variety of states (success, failure, error) along different branches preceding a convergence node, the jobs still converges
- [ ] Confirm that two or more convergence nodes, can themselves point to a convergence node
- [ ] Confirm that you can have a workflow job steeped in convergence nodes

### RBAC / Security

- [ ] Confirm that sensitive data is not exposed in any of the data (jt_extra_vars, extra_vars, set_stats vars) passed to a convergence node (or surfaced elsewhere indirectly - e.g. activity stream)
- [ ] Confirm that RBAC for creating a convergence node is the same as RBAC for creating other nodes in a workflow

### Misc

- [ ] Confirm that convergence nodes correctly send notifications
- [ ] Confirm that related fields for convergence nodes are correct under all relevant scenarios described here (e.g. is there a field that mentions the job / node that triggered the convergence job?)

### UI
- [ ] Confirm that the workflow job template editor can correctly handle various ways of creating / deleting convergence nodes
- [ ] Confirm that the workflow job template editor correctly renders the same workflow job template when closed and re-opened multiple times (should the layout of the WFJT be stable across editor sessions?)
- [ ] Confirm that the workflow job UI correctly shows workflow jobs with convergence nodes in progress for all the different scenarios listed for the API tests ^
