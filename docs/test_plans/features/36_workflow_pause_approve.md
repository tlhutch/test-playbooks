# Workflow Pause Approve

## Feature Summary
With this feature, a Pause/Approve node can be added in the workflow job template, where the workflow job halts until it receives an input from the user.
Any user with right permissions can approve to proceed or deny to fail the node in the workflow.

## Related Information
* [Feature request](https://github.com/ansible/awx/issues/1206)
* [Initial PR](https://github.com/ansible/awx/pull/2352)
* [Main PR](https://github.com/ansible/awx/pull/3801)
* [Integration Tests](https://github.com/ansible/tower-qa/blob/workflow_pause_approve/tests/api/workflows/test_workflow_approval_nodes.py)

## Scenarios to test

### Basic Flow

- [ ] Confirm that superuser can add workflow pause node and give various permissions to users
- [ ] Confirm that a user can convert any workflow node into a workflow pause approval node
- [ ] Confirm indirectly in tests that an approval node can be added and approved in the following places in a workflow job template
    - [ ] In the beginning of the workflow
    - [ ] In between two workflow nodes
    - [ ] At the end
    - [ ] As an only node in the template
- [ ] Confirm that an approval node waiting for a user to approve or deny does not impact the running of a node in another parallel path in the workflow template
- [ ] Confirm that an approval node that has been denied does not impact the running of a node in another parallel path in the workflow template
- [ ] Confirm that a workflow job can be successful if an approval node has been denied but there is an alternate path to take
- [ ] Confirm that a workflow job will be failed if the approval node that has been denied is the last node

### Timeout Feature Verification

- [ ] Confirm that a user can specify timeout during creation of the approval node
- [ ] Confirm that if a timeout is not specified, it is set to 0(unlimited) by default
- [ ] Confirm that any user cannot approve/deny after the timeout period
- [ ] Confirm that after the timeout, the approval node fails with a reason of failure and the attribute timeout is true

### Workflow and Workflow Approval node state Verification

- [ ] Confirm that in the beginning of the workflow job run, the state of the workflow job is “running” and the state of the approval node is “never updated”
- [ ] Confirm that when the workflow approval node is waiting for approval, the state of the node is “pending” and the state of the workflow job is still “running”
- [ ] Confirm that the state of the node is “successful” if approved and “failed” if denied

### Activity Stream Scenarios

- [ ] Confirm the details such as name of the node, person who approved/denied it, reason of failure if any, person who launched the job are present in the activity stream. Verify this in all scenarios of: approval, denial, timeout.

### RBAC

- [ ] Confirm that all valid users with permission according to the table below can
    - [ ] See the workflow approval node
    - [ ] See the activity stream entry for the job
    - [ ] Create an approval node
    - [ ] Approve or deny
    - [ ] Grant approval permissions to other users
- [ ] Confirm that all invalid users without the permission cannot according to the table below cannot
    - [ ] See the workflow approval node
    - [ ] See the activity stream entry for the job
    - [ ] Create an approval node
    - [ ] Approve or deny
    - [ ] Grant approval permissions to other users


| Scope  | Role Type | Can view workflow approval  | Can view activity stream entry | Can create  | Approve/Deny |Grant approval  |
| ------------- | ------------- | ------------- | ------------- | ------------- | ------------- | ------------- |
| Org <br> WFJT | WF Admin | ✔️ | ✔️ | ✔️ | ✔️ | Org ❌ <br> WFJT ✔️ |
| Org <br> WFJT | Executor in WF | ✔️ | ✔️ | ❌ | ❌ | ❌ |
| Org | Org Admin | ✔️ | ✔️ | ✔️ | ✔️ | ✔️ |
| System | System Admin | ✔️ | ✔️ | ✔️ | ✔️ | ✔️ |
| Org <br> WFJT | Approver | ✔️ | ✔️ | ❌️ | ✔️ | ❌ |
| Org <br> WFJT | Read on WF | ✔️ | ✔️ | ❌ | ❌ | ❌ |
| System | System Auditor | ✔️ | ✔️ | ❌ | ❌ | ❌ |
| Random user in org | No Permission | ❌ | ❌ | ❌ | ❌ | ❌ |
| Random user outside org | No Permission | ❌ | ❌ | ❌ | ❌ | ❌ |

### Interaction with other workflow features:

- [ ] Confirm that the set_stats artifacts in nodes before the approval node can pass through the approval node and the nodes after the approval node have access to the artifacts

### Random Scenarios

- [ ] Confirm that if a workflow job template is deleted, previously run workflow approvals are not deleted but the template itself is deleted
- [ ] Confirm that if a workflow approval node is deleted, its approvals are not deleted
- [ ] Confirm that if an approval node is acted upon (approve/deny) it cannot be approved/denied again
- [ ] Confirm that if the tower restarts, once it is up again, the approval nodes previously in pending state are still pending and they can be approved and the workflow job finishes and succeeds
