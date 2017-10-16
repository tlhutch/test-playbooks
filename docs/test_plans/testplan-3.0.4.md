# Tower 3.0.4 Release Test Plan

## Overview

* Estimating 3 days of work (due to job/test rot, dependency changes, and potential build issues)
* Release involved significant packaging changes. Warrants more careful attention to upgrade testing (including HA upgrades).
* Release also involves [security fix](https://github.com/ansible/ansible-tower/issues/7558) to be verified manually.
* 3.0.4 issues available [here](https://github.com/ansible/ansible-tower/issues?q=is%3Aopen+is%3Aissue+milestone%3Arelease_3.0.4)

## Resources
* 4 full-time quality engineers - cwang/jladd/mfoord/rfitzpat

## Features Not Tested

## Features Tested

## Targeted testing

* [x] Job Templates and Adhoc Commands can be used to gain escalated awx privilege [#7558](https://github.com/ansible/ansible-tower/issues/7558)

## Regression
* [ ] Limited manual UI testing completed
* [ ] API regression completed
* [ ] Tower HA regression completed
* [ ] Backup/restore playbook
* [ ] Third party authentication

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
1. HA installation completes successfully on all supported platforms
    * [ ] ubuntu-12.04
    * [ ] ubuntu-14.04
    * [ ] rhel-6.latest
    * [ ] rhel-7.latest
    * [ ] centos-6.latest
    * [ ] centos-7.latest
    * [ ] ol-6.latest
    * [ ] ol-7.latest
1. Installation completes successfully using supported ansible releases
    * [ ] ansible-2.3
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
1. Verify the following functions work as intended after upgrade
    1. Launch project_updates for existing projects
    1. Launch inventory_udpates for existing inventory_source
    1. Launch, and relaunch, existing job_templates
    1. Migrations were successful
    * [ ] Standalone upgrade completes on all supported platforms from `3.0.3`
    * [ ] HA upgrade completes on all supported platforms from `3.0.3`
