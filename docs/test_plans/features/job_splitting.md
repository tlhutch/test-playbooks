Job Splitting
-------------

See:
* https://github.com/ansible/awx/pull/2174
* https://github.com/ansible/awx/issues/1283

Tower 3.4.0 introduces new capabilities for distributing work across a cluster. The basic functionality is this:

The user defines a “job slices” integer in the job template
When executed, Tower will execute a variation on a workflow job. The nodes of this workflow job execute in parallel, using a special type of limit.
Each node represents a subset of the inventory. These are all submitted to the queue for execution.
Slices do not share any information with each other, so stateful playbooks will not work in this paradigm.

Sliced Job Verification Criteria (API)
---------------------
- [ ] Can be created
- [ ] Job Template Parameters are applied to all slices
  - [ ] Prompts
    - [ ] Credentials
    - [ ] Limits (note: may result in 0 host slices)
    - [ ] Inventories
    - [ ] Projects
    - [ ] Credential Passwords
    - [ ] Survey Responses
    - [ ] Custom Virtualenv
  - [ ] Extra Vars
  - [ ] Credentials
  - [ ] Forks
  - [ ] Show Changes
  - [ ] Verbosity
  - [ ] Allow Simultaneous
- [ ] Hosts will not appear in more than one slice
- [ ] Callback Provisioning
  - [ ] Works
  - [ ] Does not create a workflow job
- [ ] Simultaneous execution
  - [ ] Can run simultaneously
  - [ ] Won't run simultaneously if that is disabled
- [ ] Cancellation
  - [ ] Cancelling the sliced job cancels all slices
  - [ ] Canceling a slice does not cancel the entire job
- [ ] Can be executed as part of a workflow
- [ ] Can be scheduled
- [ ] Notification templates only fire for the whole sliced job, as opposed to the slices
- [ ] Relaunching
  - [ ] Slices can be relaunced individually
  - [ ] The entire sliced job can be relaunched
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
- [ ] Job details for slices are only viewable by users with permission
- [ ] Sliced jobs work with large inventories
  - [ ] 5000
  - [ ] 10000
  - [ ] 20000
