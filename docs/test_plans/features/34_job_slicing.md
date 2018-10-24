Job Slicing
-------------

See:
* https://github.com/ansible/awx/pull/2174
* https://github.com/ansible/awx/issues/1283

Tower 3.4.0 introduces new capabilities for distributing work across a cluster. The basic functionality is this:

The user defines a “job slices” integer in the job template
When executed, Tower will execute a variation on a workflow job. The nodes of this workflow job execute in parallel, using a special type of limit.
Each node represents a subset of the inventory. These are all submitted to the queue for execution.
Slices do not share any information with each other, so stateful playbooks will not work in this paradigm.

# Sliced Job Verification Criteria (API)

## Basic CRUD Operations

- [x] Slice parameter can be set on job templates
- [x] Sliced job results can be deleted
- [x] Job results for slices can be deleted
- [ ] Search Results
  - [ ] Slices
  - [ ] Sliced Jobs
- [x] Sliced Job Results can be viewed
- [x] Sliced Job Results can only be viewed by people with appropriate permissions

## Inventory

- [ ] Script Endpoint
  - [ ] Arbitrary slices can be created with the script endpoint (`/api/v2/inventories/N/script/?hostvars=1&subset=split2of3`)
  - [ ] Inventory Group membership is reflected in slices
  - [ ] Smart Inventories can be sliced
  - [ ] Slices are consistent between runs
- [ ] Sliced jobs work with large inventories
  - [ ] 5000
  - [ ] 10000
  - [ ] 20000
- [ ] Hosts will not appear in more than one slice

## Workflows

- [ ] Sliced Job Templates can be used as part of a Workflow Job Template
- [ ] Workflow Jobs using a sliced job template can be cancelled
- [ ] Workflow Jobs using a sliced job template can be relaunched

## Execution
- [ ] Job Template Parameters are applied to all slices
  - [ ] Prompts
    - [ ] Credentials
    - [ ] Limits (note: may result in 0 host slices)
    - [ ] Inventories
    - [ ] Projects
    - [ ] Credential Passwords
    - [x] Survey Responses
    - [ ] Custom Virtualenv
  - [ ] Extra Vars
  - [ ] Credentials
  - [ ] Forks
  - [ ] Show Changes
  - [ ] Verbosity
  - [ ] Allow Simultaneous
- [ ] Callback Provisioning
  - [ ] Works
  - [ ] Does not create a workflow job
- [ ] Simultaneous execution
  - [x] Can run simultaneously
  - [ ] Won't run simultaneously if that is disabled
- [ ] Notification templates only fire for the whole sliced job, as opposed to the slices
- [ ] Relaunching
  - [x] Slices can be relaunced individually
  - [x] The entire sliced job can be relaunched
  - [ ] Values carried over to the relaunced job:
    - [ ] slice number
    - [ ] static fields
- [ ] Projects and Inventories that update on launch only do so for the workflow job
- [ ] Failure
  - [ ] Failed when all workflow nodes are failed
  - [ ] If a single slice fails, the others keep running
- [ ] Instance group settings are respected at all levels
  - [ ] Organization
  - [ ] Inventory
  - [ ] Job Template
- [ ] Sliced jobs can be executed with a custom virtualenv
- [ ] When a job template is set to 0 or 1 slice, it launches as a regular job template
- [ ] Auditors can view job results for sliced jobs
- [ ] Cancellation
  - [ ] Cancelling the sliced job cancels all slices
  - [ ] Canceling a slice does not cancel the entire job
- [ ] Can be executed as part of a workflow
- [x] Can be scheduled

