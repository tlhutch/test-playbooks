# Tower 3.1.0 Release Test Plan

## Resources
* 4 full-time automation engineers - cwang/jladd/rfitzpat/jmcdermott

## Features Not Tested

## Features Tested

### RBAC Copy/Edit Rework (Chris)
[Feature](https://docs.google.com/document/d/19qwq-6nAMAZcYonQjKERgVhK_dXJ3oLDNTmx5_rNZHU/edit)

Top-level /api/v1/\w+/ user_capabilities:

1. [x] Expected flags for /api/v1/ad_hoc_commands/ against range of inventory permissions.
1. [x] Expected flags for /api/v1/credentials/ against range of credential permissions.
1. [x] Expected flags for /api/v1/inventories/ against range of inventory permissions.
1. [x] Expected flags for /api/v1/groups/ against range of inventory permissions.
1. [x] Expected flags for /api/v1/hosts/ against range of inventory permissions.
1. [x] Expected flags for /api/v1/inventory_scripts/ against range of inventory script permissions.
1. [x] Expected flags for /api/v1/jobs/ against range of job template permissions.
1. [x] Expected flags for /api/v1/inventory_updates/ against range of inventory permissions.
1. [x] Expected flags for /api/v1/project_updates/ against range of project permissions.
1. [x] Expected flags for /api/v1/job_templates/ against range of job template permissions.
1. [x] Expected flags for /api/v1/notification_templates/ against range of system permissions.
1. [x] Expected flags for /api/v1/organizations/ against range of organization permissions.
1. [x] Expected flags for /api/v1/schedules/ against range of system permissions.
1. [x] Expected flags for /api/v1/\w+/\d+/schedules/ against range of scheduled resource permissions (ex: inventory).
1. [x] Expected flags for /api/v1/system_jobs/ against range of system permissions.
1. [x] Expected flags for /api/v1/teams/ against range of team permissions.
1. [x] Expected flags for /api/v1/users/ against range of system permissions.

Additional cases:

1. [x] Expected flags for /api/v1/\w+/\d+/access_list/ against range of credential permissions (covered in unittests).
1. [x] Expected flags for special cases (manual groups and projects).
1. [x] Smoke testing of user_capabilities with team permissions.

### Timeouts (Chris)
[Feature](https://github.com/ansible/ansible-tower/issues/2363)

1. [x] Verify successful timeout with project update.
1. [x] Verify successful timeout with inventory update.
1. [x] Verify successful timeout with job.
1. [x] Test that by default that unified jobs run to completion.
1. [x] Test global timeout flags listed under /api/v1/settings/jobs/.
1. [x] Test that positive timeouts override global timeouts.
1. [x] Test that negative resource timeouts nullify global timeouts.

### Configure Tower in Tower (Chris)
[Feature](https://drive.google.com/open?id=1Oc84TUnV2eh2Cy29vVfUfdJmV_qyg7NnTAEhuqoYdiQ)

Third-party authentication:

1. [x] Test successful authentication via GitHub social auth.
1. [x] Test successful authentication via Github Teams social auth.
1. [x] Test successful authentication via Github Organizations social auth.
1. [x] Test successful authentication via Google social auth.
1. [x] Test successful authentication via AzureAD social auth.
1. [x] Test successful authentication via LDAP.
1. [x] Test successful authentication via RADIUS.
1. [x] Test successful authentication via SAML.
1. [x] Verify organization-mapping flag functionality.
1. [x] Verify team-mapping flag functionality.

Settings access:

1. [x] Test that options under /api/v1/settings/ filtered by license.
1. [x] Test that flags listed under /api/v1/settings/\w+/ filtered by license.
1. [x] Verify that nothing listed under /api/v1/settings/ against range of non-superusers.
1. [x] Verify RUD access to nested settings endpoints against range of non-superusers.
1. [x] Verify that DELETE resets a nested settings endpoint to factory defaults.
1. [x] Verify that changed settings get listed under /api/v1/settings/changed/.
1. [x] Test that sensitive values obscured on all nested settings endpoints.

Backward compatability:

1. [x] Test that static file settings still supported.
1. [x] Test that static file settings override database settings.
1. [x] Test that OPTIONS successfully updated for static settings.

Migrations:

1. [x] Test successful migration to database on EL7 Tower-3.0.3.
1. [x] Test successful migration to database on Ubuntu 14.04 Tower-3.03.
1. [x] Test successful third-party Tower authentication via upgraded test instance on EL7.
1. [x] Test successful third-party Tower authentication via upgraded test instance on Ubuntu 14.04.

Select flags:

1. [x] Test major flags listed under /api/v1/settings/authentication/.
1. [x] Test major flags listed under /api/v1/settings/jobs/.
1. [x] Test major flags listed under /api/v1/settings/system/.
1. [x] Test major flags listed under /api/v1/settings/ui/.

### Tower Module (???)
[Feature](https://docs.google.com/document/d/1OzgMmV3kM9CDnp1bymSc3gVIMndTZ2v2hKTqk6q4r9Q/edit#heading=h.9fzgd7wtce8c)

1. [ ] Test that modules posts correct payloads to Tower upon create request.
1. [ ] Test editing existing Tower resources.
1. [ ] Test that Tower resources deleted upon delete request.
1. [ ] Test non-standard config.
1. [ ] Test that modules are idempotent.

### Task Manager (Chris)
[Feature](https://github.com/ansible/ansible-tower/blob/devel/docs/task_manager_system.md)

General acceptance criteria:

1. [x] Groups of blocked tasks run in chronological order.
1. [ ] Tasks that are not blocked run whenever there is capacity available.
1. [x] One job is always allowed to run even if there isn't enough capacity.
1. [x] Only one project update for a project may be running at any given point in time.
1. [x] Only one inventory update for an inventory source may be running at any given point in time.
1. [x] For a related project, only one job xor project update may be running at any given point in time.
1. [x] For a related inventory, only one job xor inventory update(s) may be running at any given point in time.
1. [x] For a related inventory, only one command xor inventory update(s) may be running at any given point in time.
1. [x] Only one job for a JT may be running at any given point in time when allow_simultaneous is disabled.
1. [x] Multiple jobs from the same JT may be running at any given point in time when allow_simultaneous is enabled.
1. [x] Only one command for an inventory may be running for any given point in time.
1. [x] Only one system job may be running at any given point in time.

Cascade failing jobs:

1. [x] Cascade fail with project updates (cancel the project update, dependent jobs are failed).
1. [x] Cascade fail with inventory updates (cancel the inventory update, dependent jobs are failed).
1. [x] Fail dependent job upon cancelling update with job with multiple inventory updates.
1. [x] Fail dependent job upon cancelling project update with job with both inventory and project updates.
1. [x] Fail dependent job upon cancelling inventory update with job with both inventory and project updates.

Autospawned jobs:

1. [x] With inventory with a single inventory source with update_on_launch, inventory update must finish before job is allowed to run.
1. [x] With inventory with multiple inventory sources with update_on_launch, inventory updates must finish before job is allowed to run.
1. [x] For project updates, two project updates get spawned by the job: one of type "check" and one of type "run." Job is blocked by the "check" update.
1. [x] For a job with autospawned project and inventory updates, all updates except our "run" project update must run to completion before our job is allowed to start.

Autospawned jobs with cache timeout:

1. [x] Cache timeout respected for inventory updates. If we're within our timeout window, no additional updates should get spawned.
1. [x] Cache timeout respected for project updates. If we're within our timeout window, we still get a "run" project update.

### Logging (Jake)
[Feature](https://github.com/ansible/ansible-tower/blob/devel/docs/logging_integration.md)

- verify documented steps for setting up and connecting with all supported log aggregator services.
  - [ ] ELK
  - [ ] Splunk
- verify authentication and logins:
  - [x] ELK
  - [x] Splunk
- verify that tower succesfully creates and sends a log message in the expected format for each data type:
  - ELK:
    - [x] activity_stream
    - [x] job event
    - [x] fact scan / system tracking
    - [x] job status updates
  - Splunk:
    - [x] activity_stream
    - [x] job event
    - [x] fact scan / system tracking
    - [x] job status updates

### Channels (Ryan)
1. [x] \(Un\)subscription functional for inventory updates
1. [x] Expected status events are broadcasted for inventory updates
1. [x] \(Un\)subscription functional for project updates
1. [x] Expected status events are broadcasted for project updates
1. [x] \(Un\)subscription functional for launched job
1. [x] Expected status and job events are broadcasted for launched job
1. [x] \(Un\)subscription functional for launched workflow
1. [x] Expected status and workflow events are broadcasted for launched workflow
1. [ ] \(Un\)subscription functional for control events
1. [ ] Expected limit reached control event is broadcasted for auth
1. [x] Expected job events broadcasted by rbac roles filtering
1. [ ] Expected status and events are broadcasted over cluster

### Clustering/HA (Ryan)
1. [x] Successful installation of 3 node + 1 db clustered system
1. [x] Successful installation of 5 node + 1 db clustered system
1. [x] Successful installation of 10 node + 1 db clustered system
1. [x] Successful addition of new nodes to cluster via inventory update and setup.sh rerun
1. [x] Successful addition of former standalone nodes to cluster via setup.sh rerun
1. [x] Successful deprovisioning of nodes via tower-manage command
1. [x] Expected distribution of 2000 launched jobs over 3 node cluster
1. [x] Expected distribution of 2000 launched jobs over 5 node cluster
1. [x] Expected distribution of 2000 launched jobs over 10 node cluster
1. [x] Satisfactory create/run performance of 3.0.3 v. 3.1.0 standalone system w/ 2000 debug jobs over 10 hosts
1. [x] Satisfactory query/delete performance of 3.0.3 v. 3.1.0 standalone system w/ 2000 debug jobs over 10 hosts
1. [x] Satisfactory create/run performance of 3.0.3 v. 3.1.0 standalone system w/ 2000 debug jobs over 100 hosts
1. [x] Satisfactory query/delete performance of 3.0.3 v. 3.1.0 standalone system w/ 2000 debug jobs over 100 hosts
1. [x] Satisfactory performance of 3.0.3 v. 3.1.0 standalone system w/ stress benchmarking job over 100 hosts
1. [x] Satisfactory create/run performance of 3.1.0 standalone v. 3 node cluster w/ 2000 debug jobs over 10 hosts
1. [x] Satisfactory query/delete performance of 3.1.0 standalone v. 3 node cluster w/ 2000 debug jobs over 10 hosts
1. [x] Satisfactory create/run performance of 3.1.0 standalone v. 5 node cluster w/ 2000 debug jobs over 10 hosts
1. [x] Satisfactory create/run performance of 3.1.0 standalone v. 10 node cluster w/ 2000 debug jobs over 10 hosts
1. [x] Satisfactory create/run performance of 3.1.0 standalone v. 3 node cluster w/ 2000 debug jobs over 100 hosts
1. [x] Satisfactory query/delete performance of 3.1.0 standalone v. 3 node cluster w/ 2000 debug jobs over 100 hosts
1. [x] Satisfactory create/run performance of 3.1.0 standalone v. 5 node cluster w/ 2000 debug jobs over 100 hosts
1. [x] Satisfactory create/run performance of 3.1.0 standalone v. 10 node cluster w/ 2000 debug jobs over 100 hosts
1. [x] Satisfactory performance of 3.1.0 standalone v. 3 node clustered systems w/ stress benchmarking job over 100 hosts
1. [ ] Expected survivability, distribution, and success of 2000 jobs over 3 node cluster w/ network disruption
1. [x] Logging functions as expected for all nodes in 3 node cluster

### Job Events (Ryan)
1. [x] Expected job events are visible for playbooks with multiple plays
1. [x] Expected job events are visible for playbooks with async tasks
1. [x] Expected job events are visible for playbooks when free strategy is used

### Workflows (Jim)
[Feature](https://github.com/ansible/ansible-tower/blob/devel/docs/workflow.md)

#### CRUD-related

1. [x] Verify that CRUD operations on all workflow resources are working properly. Note workflow job nodes cannot be created or deleted independently, but verifications are needed to make sure when a workflow job is deleted, all its related workflow job nodes are deleted.
1. [x] Verify the RBAC property of workflow resources. More specifically:
 - [x] Workflow job templates can only be accessible by superusers ---- system admin, admin of the same organization and system auditor and auditor of the same organization with read permission only.
 - [x] Workflow job read and delete permissions follow from its associated workflow job template.
 - [x] Workflow job relaunch permission consists of the union of execute permission to its associated workflow job template, and the permission to re-create all the nodes inside of the workflow job.
 - [x] Workflow job template nodes rely their permission rules on the permission rules of both their associated workflow job template and unified job template for creation and editing.
 - [x] Workflow job template nodes can be deleted with admin permission to their workflow job template (even lacking permission to the node's job template).
 - [x] Workflow job nodes are viewable if its workflow job is viewable.
 - [x] No CRUD actions are possible on workflow job nodes by any user, and they may only be deleted by deleting their workflow job.
 - [x] Workflow jobs can be deleted by superusers and org admins of the organization of its associated workflow job template, and no one else.
 - [x] Copying workflow job templates based on permission rules of workflow job template, unified job templates, and all related resources used by nodes.
1. [x] Verify that workflow job template nodes can be created under, or (dis)associated with workflow job templates.
1. [x] Verify that only the permitted types of job template types can be associated with a workflow job template node. Currently the permitted types are job templates, inventory sources and projects.
1. [x] Verify that workflow job template nodes under the same workflow job template can be associated to form parent-child relationship of decision trees. More specifically, one node takes another as its child node by POSTing another node's id to one of the three endpoints: /success_nodes/, /failure_nodes/ and /always_nodes/.
1. [x] Verify that workflow job template nodes are not allowed to have invalid association. Any attempt to create an invalid association will trigger 400-level response. The three types of invalid associations are cycle, convergence(multiple parent) and mutex('always' XOR the rest).
1. [x] Verify that a workflow job template can be successfully copied and the created workflow job template does not miss any field that should be copied or intentionally modified.
1. [x] Verify that if a user has no access to any of the related resources of a workflow job template node, that node will not be copied and will have null as placeholder.

#### Task-related

1. [x] Verify that workflow jobs can be launched by POSTing to endpoint /workflow_job_templates/\d/launch/.
1. [x] Verify that schedules can be successfully (dis)associated with a workflow job template, and workflow jobs can be triggered by the schedule of associated workflow job template at specified time point.
1. [x] Verify that extra variables work for workflow job templates as described. In specific, verify the role of workflow job extra variables as a set of global runtime variables over all its spawned jobs.
1. [x] Verify that extra variables of a workflow job node are correctly overwritten in order by the cumulative job artifacts of ancestors, and the overwrite policy of cumulative job artifacts is correct (artifacts of parent overwrite artifacts of grandparent).
1. [x] Verify that during a workflow job run, all its decision trees follow their correct paths of execution. Unwarranted behaviors include child node executing before its parent and wrong path being selected (failure nodes are executed when parent node succeeds and so on).
1. [x] Verify that a subtree of execution will never start if its root node runs into internal error (not ends with failure).
1. [x] Verify that a subtree of execution will never start if its root node is successfully canceled.
1. [x] Verify that cancelling a workflow job that is cancellable will consequently cancel any of its cancellable spawned jobs and thus interrupts the whole workflow execution.
1. [x] Verify that during a workflow job run, deleting its spawned jobs are prohibited.
1. [x] Verify that at the beginning of each spawned job run, its prompted fields will be populated by the wrapping workflow job node with correct values. For example, credential field of workflow job node goes to credential field of spawned job.
1. [x] Verify that notification templates can be successfully (dis)associated with a workflow job template. Later when its spawned workflow jobs finish running, verify that the correct type of notifications will be sent according to the job status.
1. [x] Verify that a workflow job can be successfully relaunched.
1. [x] Verify that `artifacts` is populated when `set_stats` is used in Ansible >= v2.2.1.0-0.3.rc3 (Unable to use on stable-2.2: https://github.com/ansible/ansible/issues/21079)

#### Test Notes

Non-trivial topology should be used when testing workflow run. A non-trivial topology for a workflow job template should include:
- [x] Multiple decision trees.
- [x] Relatively large height in each decision tree.
- [x] All three types of relationships (success, failure and always).

## Regression
1. [ ] UI regression completed
1. [ ] API regression completed
1. [x] Tower HA installation regression completed
1. [x] Tower LDAP Integration regression completed
1. [x] Tower RADIUS Integration regression completed
1. [x] Social authentication regression completed
1. [x] Backup/restore successful

### Installation
1. Installation completes successfully on all supported platforms
    * [x] ubuntu-14.04
    * [x] ubuntu-16.04
    * [x] rhel-7.latest
    * [x] centos-7.latest
    * [x] ol-7.latest
1. Installation completes successfully using supported ansible releases
    * [x] ansible-2.3 (devel branch)
    * [x] ansible-2.2
    * [x] ansible-2.1
1. Installation completes successfully on supported images
    * [x] AMI (unlicensed)
    * [ ] Vagrant
1. Bundled installation completes successfully on all supported platforms (Automated)
    * [x] rhel-7.latest
    * [x] centos-7.latest
    * [x] ol-7.latest

### Upgrades
1. [x] Upgrade completes on all supported platforms from `3.0.*`
1. [x] Verify the following functions work as intended after upgrade
    * [x] Launch project_updates for existing projects
    * [x] Launch inventory_updates for existing inventory_source
    * [x] Launch, and relaunch, existing job_templates
    * [x] Migrations were successful
