# Tower 3.0.0 Release Test Plan

## Resources
* 3 full-time api quality engineers - cwang/jladd/rfitzpat
* 2 full-time ui quality engineers - jmcdermott/shane

## Features Not Tested

## Features Tested

### Django Upgrade
[Feature](https://drive.google.com/open?id=18RB73_CSFX6uSOZLmp9McHU1mVfhw5eUKNDEzJScnjA)
[Tracking](https://github.com/ansible/ansible-tower/issues/594)

1. [x] Tested via integration

### Mongo-ectomy and Installer changes (Jim / Ryan)
[Feature](https://drive.google.com/open?id=1fJeLZefxSia0-XSS0Gx_jeG5lYXUkU8V1LD9juEnlDc)

1. [x] Installer updated to only install PSQL
1. [x] Upgrades disable Mongo and future fact data stored to PSQL
1. [x] Upon upgrade, old fact data migrated to PSQL

### Notifications (Jim/Chris)
[Feature](https://drive.google.com/open?id=14qb12baMp5aYWVpxXGEKxiC_wX3ZpHe3Bf6hwUue9rI)
[Tracking](https://github.com/ansible/ansible-tower/issues/1291)
<ui ticket> 

###  Job Template Reorganization/Query Persistance/Filtering Improvements (Labels) (Chris/____?)
[Feature](https://docs.google.com/document/d/15FIaU-guKSfavK_pZ7f4k1Z9z3uXLFsYxXIFr3kzwcA/edit#heading=h.kr1zq13elnh)
[Tracking](https://github.com/ansible/ansible-tower/issues/1153)

1. [X] Manual testing completed - exact steps tracked in tracking issue
1. [X] Complete integration testing written and passing - tests added logged in tracking issue
1. [ ] UI testing completed

### RBAC Permission changes (Chris/Jake)
[Feature](https://drive.google.com/open?id=1n_hLt0vKV5ytyYtA5oj71QLKiWtKQkhVezbUvUj_npA)
[Tracking](https://github.com/ansible/ansible-tower/issues/1155)

1. [x] Integration tests written and passing for each user-role (user with organization "admin")
1. [x] Integration tests written and passing for each team-role (user in team with organization "admin")
1. [x] Performance testing with our new RBAC system
1. [x] Upgrade migrations tested

### Prompt for all the things (Chris)
[Feature](https://drive.google.com/open?id=15iSHWjgCk0oyuHX9soWtClB9dOJ4Qlxm5H8fsTqoTuo)
[Tracking](https://github.com/ansible/ansible-tower/issues/1136)

1. [x] Base flows (what the UI uses) manually tested
1. [x] Integration tests written and passing - tests added logged in tracking issue
1. [ ] RBAC testing completed for prompt for all the things
 
### Tower UX/UI Refresh (Jake/Shane)
[Feature](https://docs.google.com/document/d/1lvhjtjzKy4Ty9nusob2ZRDX5PpUC-CZ-2vLvnjQzF7k/edit)

1. [ ] FIXME

### Installer updates (Ryan)
[Feature](https://drive.google.com/open?id=1fJeLZefxSia0-XSS0Gx_jeG5lYXUkU8V1LD9juEnlDc)
[Issue](https://github.com/ansible/ansible-tower/issues/1194)

1. [ ] FIXME

### RedHat Integrations (Laska)
[Feature](https://docs.google.com/document/d/1a3_HMixPdCTxvLW8kySjyPKygP2QoYhz6iCcseyM020/edit)

1. [ ] FIXME

### Credential Updates (Chris, ____?)
[Network Credential](https://docs.google.com/document/d/1RqQboCQ3RJLjCuINwEC_AI-tkcN99G8qY91KrRgcsfQ/edit)

1. [ ] Microsoft Azure
2. [x] OpenStack_v3
3. [x] Network

## Regression
1. [ ] UI regression completed (Jake/Shane)
1. [ ] API regression completed (Chris/Jim)
1. [ ] Tower HA installation regression completed (Ryan)
1. [ ] Tower LDAP Integration regression completed (Ryan)
1. [ ] Social authentication regression completed (Chris)

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
    * [x] ansible-2.2 (devel branch)
    * [x] ansible-2.1
    * [x] ansible-1.9.x
1. Installation completes successfully on supported images
    * [ ] AMI (unlicensed) (Jim/James L.)
    * [x] Vagrant (Jim/James L.)
1. Bundled installation completes successfully on all supported platforms (Automated)
    * [x] rhel-6.latest
    * [x] rhel-7.latest
    * [x] centos-6.latest
    * [x] centos-7.latest
    * [x] ol-6.latest
    * [x] ol-7.latest

### Upgrades
1. [ ] Upgrade completes on all supported platforms from `2.4.*` (Ryan)
1. Verify the following functions work as intended after upgrade
    * [ ] Launch project_updates for existing projects
    * [ ] Launch inventory_udpates for existing inventory_source
    * [ ] Launch, and relaunch, existing job_templates
    * [ ] Migrations were successful
