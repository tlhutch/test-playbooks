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
- [x] Job Results for slices are viewable when the workflow job is deleted
- [x] Sliced Job Results can be viewed
- [x] Sliced Job Results can only be viewed by people with appropriate permissions

## Inventory

- [x] Smart Inventories can be sliced
- [x] Hosts will not appear in more than one slice

## Workflows

- [x] Sliced Job Templates can be used as part of a Workflow Job Template
- [x] Workflow Jobs using a sliced job template can be cancelled
- [x] Workflow Jobs using a sliced job template can be relaunched

## Execution
- [x] Job Template Parameters are applied to all slices
  - [x] Prompts
    - [x] Credentials
    - [x] Limits (note: may result in 0 host slices)
    - [x] Survey Responses
  - [x] Extra Vars
  - [x] Credentials
  - [x] Forks
  - [x] Show Changes
  - [x] Verbosity
  - [x] Allow Simultaneous
  - [x] Timeout
- [x] Callback Provisioning
  - [x] Works
  - [x] Does not create a workflow job
- [x] Simultaneous execution
  - [x] Can run simultaneously
  - [x] Won't run simultaneously if that is disabled
- [x] Relaunching
  - [x] Slices can be relaunced individually
  - [x] The entire sliced job can be relaunched
- [x] Instance group settings are respected at all levels
  - [x] Organization
  - [x] Inventory
  - [x] Job Template
- [x] Sliced jobs can be executed with a custom virtualenv
- [x] When a job template is set to 0 or 1 slice, it launches as a regular job template
- [x] Cancellation
  - [x] Cancelling the sliced job cancels all slices
  - [x] Canceling a slice does not cancel the entire job
- [x] Can be executed as part of a workflow
- [x] Can be scheduled

