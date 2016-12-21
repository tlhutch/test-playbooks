# Tower 3.1.0 Release Test Plan

## Resources
* 3 full-time api quality engineers - cwang/jladd/rfitzpat
* 2 full-time ui quality engineers - jmcdermott/shane

## Features Not Tested

## Features Tested

### RBAC Copy/Edit Rework (Chris)
[Feature](https://docs.google.com/document/d/19qwq-6nAMAZcYonQjKERgVhK_dXJ3oLDNTmx5_rNZHU/edit)

1. [x] Tests for all main user_capabilities endpoints.
1. [x] Tests roles and access_list user_capabilities endpoints for "unattach" (covered in unittests).
1. [ ] Smokescreen testing of user_capabilities with team permissions.

### Timeouts (Chris)
[Feature](https://github.com/ansible/ansible-tower/issues/2363)

1. [x] Tests for timeouts with project updates, inventory updates, and jobs.
1. [x] Tests for universal /api/v1/settings/jobs/ timeout flags.
1. [x] Test that local timeout values override global timeout values.

### Configure Tower in Tower (Chris)
[Feature](https://drive.google.com/open?id=1Oc84TUnV2eh2Cy29vVfUfdJmV_qyg7NnTAEhuqoYdiQ)

1. [ ] Test basic functionality of all /api/v1/settings/ endpoints.
1. [ ] Test that that capabilities filtered by license.
1. [x] Test /api/v1/settings/ RBAC.
1. [x] Test that DELETE resets an endpoint.
1. [x] Test that changed entries listed under /api/v1/settings/changed/.
1. [ ] Test that sensitive values hidden on all settings endpoints.
1. [ ] Test that settings get migrated upon upgrade.

### Tower Module (Chris)
[Feature](https://docs.google.com/document/d/1OzgMmV3kM9CDnp1bymSc3gVIMndTZ2v2hKTqk6q4r9Q/edit#heading=h.9fzgd7wtce8c)

1. [ ] Test that modules posts correct payloads to Tower upon create request.
1. [ ] Test editing existing Tower resources.
1. [ ] Test that Tower resources deleted upon delete request.
1. [ ] Test non-standard config.
1. [ ] Test that modules are idempotent.

### Task Manager (???)
[Feature](https://github.com/ansible/ansible-tower/blob/devel/docs/task_manager_system.md)

Canceling jobs:

1. [ ] Cascade fail works with project updates (cancel the project update, dependent jobs are marked as "failed."
1. [ ] Cascade fail works with inventory updates (cancel the inventory update, dependent jobs are marked as "failed."
1. [ ] Fail dependent jobs upon cancelling update with job with multiple inventory updates.
1. [ ] Fail dependent jobs upon cancelling update with job with both inventory and project updates.

Update on launch:

1. [ ] For inventory updates, inventory update gets spawned before job.
1. [ ] For inventory updates with multiple inventory sources, all inventory sources get updated before job launches.
1. [ ] For project updates, two project updates get spawned before the job runs. One update is of type "check" and the other of type "run."

Cache timeout:

1. [ ] Cache timeout respected for inventory updates. If we're within our timeout window, no additional updates should get spawned.
1. [ ] Cache timeout respected for project updates. If we're within our timeout window, we still get a "run" project update
1. [ ] Cache timeout respected when we have cache timeouts for both our inventory sources and project. Project should have a "run" update, inventory sources should not update.

General acceptance criteria:

1. [ ] Groups of blocked tasks run in chronological order
1. [ ] Tasks that are not blocked run whenever there is capacity available
1. [ ] One job is always allowed to run, even if there isn't enough capacity.
1. [ ] Only one project updates for a project may be running
1. [ ] Only one inventory update for an inventory source may be running
1. [ ] For a related project, only a job xor project update may be running
1. [ ] For a related inventory, only a job xor inventory update(s) may be running
1. [ ] Only one job for a JT may be running (allow_simultaneous feature relaxes this condition)
1. [ ] Only one system job may be running

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
1. [ ] Expected events broadcasted by rbac read role filtering (https://github.com/ansible/ansible-tower/issues/4169)

### Clustering/HA (Ryan)
1. [x] Successful installation of 3 node + 1 db clustered system
1. [x] Successful installation of 5 node + 1 db clustered system
1. [x] Successful installation of 10 node + 1 db clustered system
1. [ ] Successful addition of new nodes to cluster via inventory update and setup.sh rerun
1. [ ] Successful addition of former standalone nodes to cluster via setup.sh rerun (https://github.com/ansible/ansible-tower/issues/4392)
1. [x] Successful deprovisioning of nodes via tower-manage command
1. [x] Expected distribution of 2000 launched jobs over 3 node cluster
1. [ ] Expected distribution of 2000 launched jobs over 5 node cluster
1. [ ] Expected distribution of 2000 launched jobs over 10 node cluster
1. [ ] Satisfactory create/run performance of 3.0.3 v. 3.1.0 standalone system w/ 2000 debug jobs over 10 hosts
1. [ ] Satisfactory query/delete performance of 3.0.3 v. 3.1.0 standalone system w/ 2000 debug jobs over 10 hosts
1. [ ] Satisfactory create/run performance of 3.0.3 v. 3.1.0 standalone system w/ 2000 debug jobs over 100 hosts
1. [ ] Satisfactory query/delete performance of 3.0.3 v. 3.1.0 standalone system w/ 2000 debug jobs over 100 hosts
1. [ ] Satisfactory create/run performance of 3.0.3 v. 3.1.0 standalone system w/ stress benchmarking job over 100 hosts (https://github.com/ansible/ansible-tower/issues/3990)
1. [ ] Satisfactory query/delete performance of 3.0.3 v. 3.1.0 standalone system w/ stress benchmarking job over 100 hosts (https://github.com/ansible/ansible-tower/issues/3990)
1. [ ] Satisfactory create/run performance of 3.1.0 standalone v. 3 node cluster w/ 2000 debug jobs over 10 hosts
1. [ ] Satisfactory query/delete performance of 3.1.0 standalone v. 3 node cluster w/ 2000 debug jobs over 10 hosts
1. [ ] Satisfactory create/run performance of 3.1.0 standalone v. 5 node cluster w/ 2000 debug jobs over 10 hosts
1. [ ] Satisfactory create/run performance of 3.1.0 standalone v. 10 node cluster w/ 2000 debug jobs over 10 hosts
1. [ ] Satisfactory create/run performance of 3.1.0 standalone v. 3 node cluster w/ 2000 debug jobs over 100 hosts
1. [ ] Satisfactory query/delete performance of 3.1.0 standalone v. 3 node cluster w/ 2000 debug jobs over 100 hosts
1. [ ] Satisfactory create/run performance of 3.1.0 standalone v. 5 node cluster w/ 2000 debug jobs over 100 hosts
1. [ ] Satisfactory create/run performance of 3.1.0 standalone v. 10 node cluster w/ 2000 debug jobs over 100 hosts
1. [ ] Satisfactory performance of 3.1.0 standalone v. 3 node clustered systems w/ stress benchmarking job over 100 hosts (https://github.com/ansible/ansible-tower/issues/3990)
1. [ ] Expected distribution and success of 2000 jobs over 3 node cluster w/ network disruption
1. [ ] Expected distribution and success of 2000 jobs over 5 node cluster w/ network disruption
1. [ ] Expected distribution and success of 2000 jobs over 10 node cluster w/ network disruption

### Job Events (Ryan)
1. [ ] Expected job events are visible for jobs with playbooks
1. [ ] Expected job events are visible for playbooks with async tasks
1. [ ] Expected job events are visible for playbooks when free strategy is used

## Regression
1. [ ] UI regression completed
1. [ ] API regression completed
1. [ ] Tower HA installation regression completed
1. [ ] Tower LDAP Integration regression completed
1. [ ] Tower RADIUS Integration regression completed
1. [ ] Social authentication regression completed
1. [ ] Backup/restore playbook

### Installation
1. Installation completes successfully on all supported platforms
    * [ ] ubuntu-14.04
    * [ ] ubuntu-16.04
    * [ ] rhel-7.latest
    * [ ] centos-7.latest
    * [ ] ol-7.latest
1. Installation completes successfully using supported ansible releases
    * [ ] ansible-2.3 (devel branch)
    * [ ] ansible-2.2
    * [ ] ansible-2.1
1. Installation completes successfully on supported images
    * [ ] AMI (unlicensed)
    * [ ] Vagrant
1. Bundled installation completes successfully on all supported platforms (Automated)
    * [ ] rhel-7.latest
    * [ ] centos-7.latest
    * [ ] ol-7.latest

### Upgrades
1. [ ] Upgrade completes on all supported platforms from `3.0.*`
1. [ ] Verify the following functions work as intended after upgrade
    * [ ] Launch project_updates for existing projects
    * [ ] Launch inventory_udpates for existing inventory_source
    * [ ] Launch, and relaunch, existing job_templates
    * [ ] Migrations were successful
