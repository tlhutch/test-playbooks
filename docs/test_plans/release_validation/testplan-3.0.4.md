# Tower 3.0.4 Release Test Plan

## Overview

* Estimating 3 days of work (due to job/test rot, dependency changes, and potential build issues).
* Release involved significant packaging changes. Warrants more careful attention to upgrade testing (including HA upgrades).
* Release also involves [security fix](https://github.com/ansible/ansible-tower/issues/7558) to be verified manually.
* 3.0.4 issues available [here](https://github.com/ansible/ansible-tower/issues?q=is%3Aopen+is%3Aissue+milestone%3Arelease_3.0.4).
* HA integration consisted of basic sanity check on installs and job runs
* AMI / Vagrant images not created given that 3.0.x is nearly EOL and those images are generally created so users can get a trial copy of the most recent version of tower

## Resources
* 4 full-time quality engineers - cwang/jladd/mfoord/rfitzpat

## Features Not Tested

## Features Tested

## Targeted testing

* [x] Job Templates and Adhoc Commands can be used to gain escalated awx privilege [#7558](https://github.com/ansible/ansible-tower/issues/7558)

## Regression
* [x] Limited manual UI testing completed
* [x] API regression completed
* [x] Tower HA regression completed
* [x] Backup/restore playbook
* [x] Third party authentication

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
    * Results available [here](http://jenkins.testing.ansible.com/job/Test_Tower_Integration_3.0.4/) (Builds 1-24)
1. HA installation completes successfully on all supported platforms
    * [x] ubuntu-12.04
    * [x] ubuntu-14.04
    * [x] rhel-6.latest
    * [x] rhel-7.latest
    * [x] centos-6.latest
    * [x] centos-7.latest
    * [x] ol-6.latest
    * [x] ol-7.latest
    * Installs performed manually
1. Installation completes successfully using supported ansible releases
    * [x] ansible-2.3
    * [x] ansible-2.2
    * [x] ansible-1.9
1. Bundled installation completes successfully on all supported platforms (Automated)
    * [x] rhel-6.latest
    * [x] rhel-7.latest
    * [x] centos-6.latest
    * [x] centos-7.latest
    * [x] ol-6.latest
    * [x] ol-7.latest
    * Results available [here](http://jenkins.testing.ansible.com/job/Test_Tower_Bundle_Install_3.0.x/) (Builds 7, 8, 13)

### Upgrades
1. Verify the following functions work as intended after upgrade
    1. Launch project_updates for existing projects
    1. Launch inventory_udpates for existing inventory_source
    1. Launch, and relaunch, existing job_templates
    1. Migrations were successful
    * [x] Standalone upgrade completes on all supported platforms from `3.0.3` (Builds available [here](http://jenkins.testing.ansible.com/job/Test_Tower_Upgrade/) (Builds 1810 - 1818)
    * [x] HA upgrade completes on all supported platforms from `3.0.3`
