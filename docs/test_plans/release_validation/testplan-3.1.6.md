# Tower 3.1.6 Release Test Plan

## Overview

* 3.1.6 issues available [here](https://github.com/ansible/tower/issues?q=is%3Aopen+is%3Aissue+milestone%3Arelease_3.1.6)

## Resources
* 4 full-time automation engineers - cwang/jladd/rfitzpat/jhill

## Hotfixes 

1. [ ] Org admins can gain control of any other user [Issue](https://github.com/ansible/tower/issues/1237) (cwang)

## Regression
1. [x] UI regression completed (needs_owner)
1. [ ] API regression completed - standalone (jladd)
1. [ ] API regression completed - HA (cwang)
1. [x] Tower HA installation regression completed (cwang)
1. [ ] Tower LDAP Integration regression completed (cwang)
1. [ ] Tower RADIUS Integration regression completed (cwang)
1. [x] Social authentication regression completed (cwang)
1. [ ] Backup/restore successful (jladd)

### Installation
1. Installation completes successfully on all supported platforms (jladd)
    * [ ] ubuntu-14.04
    * [ ] ubuntu-16.04
    * [ ] rhel-7.latest
    * [ ] centos-7.latest
    * [ ] ol-7.latest
1. Installation completes successfully using supported ansible releases (jladd)
    * [ ] ansible-2.3 (devel branch)
    * [ ] ansible-2.2
    * [ ] ansible-2.1
1. Installation completes successfully on supported images (jladd)
    * [ ] AMI (unlicensed)
    * [ ] Vagrant
1. Bundled installation completes successfully on all supported platforms (Automated)  (jladd)
    * [ ] rhel-7.latest
    * [ ] centos-7.latest
    * [ ] ol-7.latest

### Upgrades
1. [ ] Upgrade completes on all supported platforms from `3.0.*` (needs_owner)
1. [ ] Verify the following functions work as intended after upgrade
    * [ ] Launch project_updates for existing projects
    * [ ] Launch inventory_updates for existing inventory_source
    * [ ] Launch, and relaunch, existing job_templates
    * [ ] Migrations were successful
