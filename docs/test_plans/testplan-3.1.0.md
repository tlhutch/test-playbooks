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
1. [ ] Test that that enterprise_auth enforced.
1. [ ] Test that DELETE resets an endpoint.
1. [ ] Test /api/v1/settings/ RBAC.
1. [ ] Test that settings get migrated upon upgrade.

### Tower Module (Chris)
[Feature](https://docs.google.com/document/d/1OzgMmV3kM9CDnp1bymSc3gVIMndTZ2v2hKTqk6q4r9Q/edit#heading=h.9fzgd7wtce8c)

1. [ ] Test that modules posts correct payloads to Tower upon create request.
1. [ ] Test editing existing Tower resources.
1. [ ] Test that Tower resources deleted upon delete request.
1. [ ] Test non-standard config.
1. [ ] Test that modules are idempotent.

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
    * [ ] ansible-2.2 (devel branch)
    * [ ] ansible-2.1
1. Installation completes successfully on supported images
    * [ ] AMI (unlicensed)
    * [ ] Vagrant
1. Bundled installation completes successfully on all supported platforms (Automated)
    * [ ] rhel-7.latest
    * [ ] centos-7.latest
    * [ ] ol-7.latest

### Upgrades
1. [ ] Upgrade completes on all supported platforms from `3.1.*`
1. Verify the following functions work as intended after upgrade
    * [ ] Launch project_updates for existing projects
    * [ ] Launch inventory_udpates for existing inventory_source
    * [ ] Launch, and relaunch, existing job_templates
    * [ ] Migrations were successful
