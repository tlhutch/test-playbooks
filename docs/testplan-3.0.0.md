# Tower 3.0.0 Release Test Plan

## Resources
* 3 full-time api quality engineers - cwang/jladd/rfitzpat
* 2 full-time ui quality engineers - jmcdermott/shane

## Assumptions
1. UI testing is performed manually.  While basic automated coverage exists, it is insufficient to test customer workflows.

## Features Not Tested

## Features Tested

### Django Upgrade
[Feature](https://drive.google.com/open?id=18RB73_CSFX6uSOZLmp9McHU1mVfhw5eUKNDEzJScnjA)
[Tracking](https://github.com/ansible/ansible-tower/issues/594)

1. [x] Tested via integration

### Mongo-ectomy and Installer changes
[Feature](https://drive.google.com/open?id=1fJeLZefxSia0-XSS0Gx_jeG5lYXUkU8V1LD9juEnlDc)

1. [x] Installer updated to only install PSQL
1. [x] Upgrades disable Mongo and future fact data stored to PSQL
1. [x] Upon upgrade, old fact data migrated to PSQL

### Notifications
[Feature](https://drive.google.com/open?id=14qb12baMp5aYWVpxXGEKxiC_wX3ZpHe3Bf6hwUue9rI)
[Tracking](https://github.com/ansible/ansible-tower/issues/1291)

1. [ ] FIXME

###  Job Template Reorganization/Query Persistance/Filtering Improvements (Labels)
[Feature](https://docs.google.com/document/d/15FIaU-guKSfavK_pZ7f4k1Z9z3uXLFsYxXIFr3kzwcA/edit#heading=h.kr1zq13elnh)
[Tracking](https://github.com/ansible/ansible-tower/issues/1153)

1. [X] Manual testing completed - exact steps tracked in tracking issue
1. [X] Complete integration testing written and passing - tests added logged in tracking issue
1. [ ] UI testing completed

### RBAC Permission changes
[Feature](https://drive.google.com/open?id=1n_hLt0vKV5ytyYtA5oj71QLKiWtKQkhVezbUvUj_npA)
[Tracking](https://github.com/ansible/ansible-tower/issues/1155)

1. [x] Integration tests written and passing for each user-role (user with organization "admin")
1. [ ] Integration tests written and passing for each team-role (user in team with organization "admin")
1. [x] Performance testing with our new RBAC system
1. [x] Upgrade migrations tested

### Prompt for all the things
[Feature](https://drive.google.com/open?id=15iSHWjgCk0oyuHX9soWtClB9dOJ4Qlxm5H8fsTqoTuo)
[Tracking](https://github.com/ansible/ansible-tower/issues/1136)

1. [x] Base flows (what the UI uses) manually tested
1. [x] Integration tests written and passing - tests added logged in tracking issue
1. [ ] RBAC testing completed for prompt for all the things
 
### Tower UX/UI Refresh
[Feature](https://docs.google.com/document/d/1lvhjtjzKy4Ty9nusob2ZRDX5PpUC-CZ-2vLvnjQzF7k/edit)

1. [ ] FIXME

### Installer updates
[Feature](https://drive.google.com/open?id=1fJeLZefxSia0-XSS0Gx_jeG5lYXUkU8V1LD9juEnlDc)
[Issue](https://github.com/ansible/ansible-tower/issues/1194)

1. [ ] FIXME

### RedHat Integrations
[Feature](https://docs.google.com/document/d/1a3_HMixPdCTxvLW8kySjyPKygP2QoYhz6iCcseyM020/edit)

1. [ ] FIXME

### Credential Updates
[Network Credential](https://docs.google.com/document/d/1RqQboCQ3RJLjCuINwEC_AI-tkcN99G8qY91KrRgcsfQ/edit)

1. [ ] Microsoft Azure
2. [x] OpenStack_v3
3. [x] Network

## Regression
1. [ ] UI regression completed
1. [ ] API regression completed
1. [ ] Tower HA installation regression completed
1. [ ] Tower LDAP Integration regression completed
1. [ ] Social authentication regression completed

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
    * [ ] ansible-2.0
    * [ ] ansible-1.9.x
    * [ ] ansible-1.8.x (manually tested on EL platforms)
1. Installation completes successfully on supported images
    * [ ] AMI (unlicensed)
    * [ ] Vagrant
1. Bundled installation completes successfully on all supported platforms
    * [ ] rhel-6.latest
    * [ ] rhel-7.latest
    * [ ] centos-6.latest
    * [ ] centos-7.latest
    * [ ] ol-6.latest
    * [ ] ol-7.latest

### Upgrades
1. [ ] Upgrade completes on all supported platforms from `2.4.*`
1. [ ] Upgrade completes on all supported platforms from `2.3.*`
1. Verify the following functions work as intended after upgrade
    * [ ] Launch project_updates for existing projects
    * [ ] Launch inventory_udpates for existing inventory_source
    * [ ] Launch, and relaunch, existing job_templates
