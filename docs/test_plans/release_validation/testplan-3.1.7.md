# Tower 3.1.7 Release Test Plan

## Overview

* Rabbit MQ Clustering Issue [here](https://github.com/ansible/tower/issues/1712)

## Notes

* Vagrant image not created for 3.1.7. (Generally omitted for older releases)
* Only running upgrades from latest point releases due to low risk / low return. Past migrations issues tend to affect major/minor releases more than patch releases.

## Resources
* jladd/jhill

## Hotfixes 

N/A

## Regression
1. [ ] UI regression completed (jhill)
1. [ ] API regression completed - standalone ( )
1. [ ] API regression completed - HA ( )
1. [ ] Tower HA installation regression completed ( )
1. [ ] Backup/restore successful ( )

### Installation
1. Installation completes successfully on all supported platforms ( . )
    * [ ] ubuntu-14.04
    * [ ] ubuntu-16.04
    * [ ] rhel-7.2
    * [ ] rhel-7.4
    * [ ] centos-7.latest
    * [ ] ol-7.latest
1. Installation completes successfully using supported ansible releases ( )
    * [ ] ansible-2.5 (devel branch)
    * [ ] ansible-2.4
    * [ ] ansible-2.3
    * [ ] ansible-2.2
1. Installation completes successfully on supported images ( )
    * [ ] AMI (unlicensed)
1. Bundled installation completes successfully on all supported platforms (Automated)  ( )
    * [ ] rhel-7.2
    * [ ] rhel-7.3
    * [ ] rhel-7.4
    * [ ] centos-7.latest
    * [ ] ol-7.latest

### Upgrades
1. [ ] Upgrade completes on all supported platforms from `3.0.4` to `3.1.7` ( )
1. [ ] Upgrade completes on all supported platforms from `3.1.6` to `3.1.7` ( )
1. [ ] Verify the following functions work as intended after upgrade
    * [ ] Launch project_updates for existing projects
    * [ ] Launch inventory_updates for existing inventory_source
    * [ ] Launch, and relaunch, existing job_templates
    * [ ] Migrations were successful
