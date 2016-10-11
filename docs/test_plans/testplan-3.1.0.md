# Tower 3.1.0 Release Test Plan

## Resources
* 3 full-time api quality engineers - cwang/jladd/rfitzpat
* 2 full-time ui quality engineers - jmcdermott/shane

## Features Not Tested

## Features Tested

### RBAC Copy/Edit Rework (Chris)
[Feature](https://docs.google.com/document/d/19qwq-6nAMAZcYonQjKERgVhK_dXJ3oLDNTmx5_rNZHU/edit)

1. [x] Integration for all new user_capabilities endpoints
2. [ ] Smokescreen testing for team permissions

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
