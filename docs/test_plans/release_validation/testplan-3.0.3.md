# Tower 3.0.3 Release Test Plan

## Resources
* 5 full-time quality engineers - cwang/jladd/rfitzpat/jmcdermott/shane

## Features Not Tested

## Features Tested

## Regression
* [ ] UI regression completed
* [x] API regression completed
* [x] Tower cluster installation regression completed
* [x] Backup/restore playbook

### Installation
1. Installation completes successfully on all supported platforms
    * [x] ubuntu-12.04
    * [x] ubuntu-14.04
    * [x] rhel-6.latest
    * [x] rhel-7.latest
    * [x] centos-6.latest
    * [x] centos-7.latest
    * [x] ol-6.latest
    * [x] ol-7.latest
1. Installation completes successfully using supported ansible releases
    * [x] ansible-2.3 (devel branch)
    * [x] ansible-2.2
    * [x] ansible-1.9
1. Installation completes successfully on supported images
    * [x] AMI (unlicensed)
    * [x] Vagrant
1. Bundled installation completes successfully on all supported platforms (Automated)
    * [x] rhel-6.latest
    * [x] rhel-7.latest
    * [x] centos-6.latest
    * [x] centos-7.latest
    * [x] ol-6.latest
    * [x] ol-7.latest

### Upgrades
1. Verify the following functions work as intended after upgrade
    1. Launch project_updates for existing projects
    1. Launch inventory_udpates for existing inventory_source
    1. Launch, and relaunch, existing job_templates
    1. Migrations were successful
    * [x] Upgrade completes on all supported platforms from `2.4.5`
    * [x] Upgrade completes on all supported platforms from `3.0.2`
