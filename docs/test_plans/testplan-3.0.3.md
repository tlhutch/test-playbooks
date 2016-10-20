# Tower 3.0.0 Release Test Plan

## Resources
* 5 full-time quality engineers - cwang/jladd/rfitzpat/jmcdermott/shane

## Features Not Tested

## Features Tested

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
    * [ ] ubuntu-12.04
    * [ ] ubuntu-14.04
    * [ ] rhel-6.latest
    * [ ] rhel-7.latest
    * [ ] centos-6.latest
    * [ ] centos-7.latest
    * [ ] ol-6.latest
    * [ ] ol-7.latest
1. Installation completes successfully using supported ansible releases
    * [ ] ansible-2.3 (devel branch)
    * [ ] ansible-2.2
    * [ ] ansible-1.9
1. Installation completes successfully on supported images
    * [ ] AMI (unlicensed)
    * [ ] Vagrant
1. Bundled installation completes successfully on all supported platforms (Automated)
    * [ ] rhel-6.latest
    * [ ] rhel-7.latest
    * [ ] centos-6.latest
    * [ ] centos-7.latest
    * [ ] ol-6.latest
    * [ ] ol-7.latest

### Upgrades
1. [ ] Upgrade completes on all supported platforms from `2.4.*`
1. [ ] Upgrade completes on all supported platforms from `3.0.0`
1. [ ] Upgrade completes on all supported platforms from `3.0.1`
1. [ ] Upgrade completes on all supported platforms from `3.0.2*`
1. Verify the following functions work as intended after upgrade
    * [ ] Launch project_updates for existing projects
    * [ ] Launch inventory_udpates for existing inventory_source
    * [ ] Launch, and relaunch, existing job_templates
    * [ ] Migrations were successful
