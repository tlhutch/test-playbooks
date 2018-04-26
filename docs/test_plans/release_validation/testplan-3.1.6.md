# Tower 3.1.6 Release Test Plan

## Overview

* 3.1.6 issues available [here](https://github.com/ansible/tower/issues?q=is%3Aopen+is%3Aissue+milestone%3Arelease_3.1.6)

## Notes

* Vagrant image not created for 3.1.6. (Generally omitted for older releases)
* Only running upgrades from latest point releases due to low risk / low return. Past migrations issues tend to affect major/minor releases more than patch releases.

## Resources
* 4 full-time automation engineers - cwang/jladd/rfitzpat/jhill

## Hotfixes 

1. [ ] Org admins can gain control of any other user [Issue](https://github.com/ansible/tower/issues/1237) (cwang)

## Regression
1. [x] UI regression completed (cwang)
1. [ ] API regression completed - standalone (jladd)
1. [ ] API regression completed - HA (cwang)
1. [x] Tower HA installation regression completed (cwang)
1. [x] Tower LDAP Integration regression completed (cwang)
1. [x] Tower RADIUS Integration regression completed (cwang)
1. [x] Social authentication regression completed (cwang)
1. [ ] Backup/restore successful (jladd)

### Installation
1. Installation completes successfully on all supported platforms (jladd)
    * [x] ubuntu-14.04
    * [x] ubuntu-16.04
    * [x] rhel-7.2
    * [x] rhel-7.4
    * [x] centos-7.latest
    * [x] ol-7.latest
1. Installation completes successfully using supported ansible releases (jladd)
    * [x] ansible-2.5 (devel branch)
    * [x] ansible-2.4
    * [x] ansible-2.3
    * [x] ansible-2.2
1. Installation completes successfully on supported images (jladd)
    * [x] AMI (unlicensed)
1. Bundled installation completes successfully on all supported platforms (Automated)  (jladd)
    * [x] rhel-7.2
    * [x] rhel-7.3
    * [x] rhel-7.4
    * [x] centos-7.latest
    * [x] ol-7.latest

### Upgrades
1. [x] Upgrade completes on all supported platforms from `3.0.4` to `3.1.6` (jhill)
1. [ ] Upgrade completes on all supported platforms from `3.1.5` to `3.1.6` (jhill)
1. [ ] Verify the following functions work as intended after upgrade
    * [ ] Launch project_updates for existing projects
    * [ ] Launch inventory_updates for existing inventory_source
    * [ ] Launch, and relaunch, existing job_templates
    * [ ] Migrations were successful
