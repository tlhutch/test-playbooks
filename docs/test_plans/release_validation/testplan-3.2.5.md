# Tower 3.2.5 Release Test Plan

## Overview

* Rabbit MQ Clustering Issue [here](https://github.com/ansible/tower/issues/1712)

## Resources
* jladd/jhill

## Features Not Tested

## Features Tested

## Targeted Testing

## Regression
1. [ ] UI regression completed (jhill)
1. [ ] API regression completed - standalone ( )
1. [ ] API regression completed - HA ( )
1. [ ] Tower HA installation regression completed ( )
1. [ ] Backup/restore successful ( )

### Installation
1. Installation completes successfully on all [supported platforms](https://docs.ansible.com/ansible-tower/3.2.3/html/installandreference/requirements_refguide.html) ( )
    * [ ] ubuntu-14.04
    * [ ] ubuntu-16.04
    * [ ] rhel-7.2
    * [ ] rhel-7.4 (latest)
    * [ ] centos-7.latest
    * [ ] ol-7.latest
1. Installation completes successfully using supported ansible releases ( )
    * [ ] ansible-2.6 (devel)
    * [ ] ansible-2.5
    * [ ] ansible-2.4
    * [ ] ansible-2.3
    * [ ] ansible-2.2
1. Bundled installation completes successfully on all [supported platforms](https://docs.ansible.com/ansible-tower/3.2.3/html/installandreference/tower_installer.html#bundled-install) (jladd)
    * [ ] rhel-7.latest
    * [ ] centos-7.latest
    * [ ] ol-7.latest
1. [ ] Installation completes successfully for HA deployment (RHEL-7.2) ( )
1. [ ] Bundled installation completes successfully for HA deployment ( )

### Upgrades
1. [ ] Successful migrations from `3.0.0` - `3.0.4` ( )
1. [ ] Successful migrations from `3.1.0` - `3.1.6` ( )
1. [ ] Successful upgrades on all supported platforms from `3.0.4` -> `3.2.4` - standalone ( )
1. [ ] Successful upgrades on all supported platforms from `3.1.6` -> `3.2.4` - standalone ( )
1. [x] Successful upgrades on all supported platforms from `3.2.3` -> `3.2.4` - standalone ( )
1. [x] Successful upgrades on all supported platforms from `3.2.0` - `3.2.3` - HA ( )

* Verify the following functionality after upgrade
    * Resource migrations
    * Launch project_updates for existing projects
    * Launch inventory_updates for existing inventory_source
    * Launch, and relaunch, existing job_templates

### Provided Images
1. Installation completes successfully on supported images
    * [ ] AMI (unlicensed) ( )
    * [ ] Vagrant ( )
