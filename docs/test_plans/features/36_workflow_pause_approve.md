# Workflow Pause Approve

## Feature Summary
With this feature, a Pause/Approve node can be added in the workflow job template, where the workflow job halts until it receives an input from the user.
Any user with right permissions can approve to proceed or deny to fail the node in the workflow.

## Related Information
* [Feature request](https://github.com/ansible/awx/issues/1206)
* [Issue](https://github.com/ansible/tower-qa/issues/3401)
* [PR](https://github.com/ansible/awx/pull/4264)
* [Integration Tests](https://github.com/ansible/tower-qa/pull/3801)

## Scenarios to test

### Basic Flow

- [x] Confirm that an approval node can be added to a workflow job template
- [x] Confirm that a user can convert any workflow node into a workflow pause approval node
- [x] Confirm that an approval node can be added and approved in the following places in a workflow job template
    - [x] In the beginning of the workflow
    - [x] In between two workflow nodes
    - [x] At the end
        - [x] Confirm that a workflow job will be failed if the approval node at the end of the branch is denied
    - [x] As an only node in the template
        - [x] Confirm that the approval/ denial of the approval node will directly impact the job status
- [x] Confirm that an approval node does not impact the running of a node in another parallel branch in the workflow template
    - [x] When the approval node is pending approval
    - [x] When the approval node is denied
- [x] Confirm that a workflow job can be successful if an approval node has been denied but there is an error handling path to take

### Timeout Feature Verification

- [x] Confirm that a user can specify timeout during creation of the approval node
- [x] Confirm that if a timeout is not specified, it is set to 0(unlimited) by default
- [x] Confirm that any user cannot approve/deny after the timeout period
- [x] Confirm that after the timeout, the approval node fails with a reason of failure and the attribute timeout is true

### Workflow and Workflow Approval node state Verification

- [x] Confirm that in the beginning of the workflow job run, the state of the workflow job is “running” and the state of the approval node is “never updated”
- [x] Confirm that when the workflow approval node is waiting for approval, the state of the node is “pending” and the state of the workflow job is still “running”
- [x] Confirm that the state of the node is “successful” if approved and “failed” if denied

### Able to copy a workflow job template with an approval node

- [x] Given that a workflow job template is copied, confirm that following objects are copied too:
    - [x] attributes such as 'type', 'extra_data', 'job_type', 'job_tags', 'skip_tags', 'limit', 'diff_mode', 'verbosity'
    - [x] the labels
    - [x] the survey spec
    - [x] approval nodes

### Activity Stream Scenarios

- [ ] Given that a workflow approval node has been APPROVE, confirm that the:
    - [x] approver is identified
    - [x] workflow job that it ran is is identified
    - [x] Confirm this is visible to anyone with read access to WF approval
- [ ] Given that a workflow approval node has been DENIED, confirm that the:
    - [x] approver is identified
    - [x] workflow job that it ran is is identified
    - [ ] ???? Reason for denial
    - [x] Confirm this is visible to anyone with read access to WF approval
- [ ] Given that a workflow approval node TIMED OUT, confirm that the:
    - [x] Timed Out is changed from False to True
    - [ ] ???? Reason for failure

### RBAC

- [x] Confirm that all valid users with permission according to the table below can
    - [x] See the workflow approval node
    - [x] See the activity stream entry for the job
    - [x] Create an approval node
    - [x] Approve or deny
    - [x] Grant approval permissions to other users
- [x] Confirm that all invalid users without the permission according to the table below cannot
    - [x] See the workflow approval node
    - [x] See the activity stream entry for the job
    - [x] Create an approval node
    - [x] Approve or deny
    - [x] Grant approval permissions to other users


| Scope  | Role Type | Can view workflow approval  | Can view activity stream entry | Can create  | Approve/Deny |Grant approval  |
| ------------- | ------------- | ------------- | ------------- | ------------- | ------------- | ------------- |
| Org <br> WFJT | WF Admin | ✔️ | ✔️ | ✔️ | ✔️ | Org ❌ <br> WFJT ✔️ |
| Org <br> WFJT | Executor in WF | ✔️ | ✔️ | ❌ | ❌ | ❌ |
| Org | Org Admin | ✔️ | ✔️ | ✔️ | ✔️ | ✔️ |
| System | System Admin | ✔️ | ✔️ | ✔️ | ✔️ | ✔️ |
| Org <br> WFJT | Approver | ✔️ | ✔️ | ❌️ | ✔️ | ❌ |
| Org <br> WFJT | Read on WF | Org ❌ <br> WFJT ✔️ | Org ❌ <br> WFJT ✔️ | ❌ | ❌ | ❌ |
| System | System Auditor | ✔️ | ✔️ | ❌ | ❌ | ❌ |
| Random user in org | No Permission | ❌ | ❌ | ❌ | ❌ | ❌ |
| Random user outside org | No Permission | ❌ | ❌ | ❌ | ❌ | ❌ |

### Edge Cases

- [x] Confirm that if a workflow job template is deleted, previously run workflow approvals are not deleted but the template itself is deleted
- [x] Confirm that if a workflow approval node is deleted, its approvals are not deleted
- [x] Confirm that if an approval node is acted upon (approve/deny) it cannot be approved/denied again
- [x] Confirm that if the tower restarts, once it is up again, the approval nodes previously in pending state are still pending and they can be approved and the workflow job finishes and succeeds
- [x] Confirm that the set_stats artifacts in nodes before the approval node can pass through the approval node and the nodes after the approval node have access to the artifacts

