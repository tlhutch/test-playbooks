# Tower 3.0.0 Release Test Plan

## Resources
* 3 full-time quality engineers - cwang/jladd/jmcdermott

## Assumptions
1. UI testing is performed manually.  While basic automated coverage exists, it is insufficient to test customer workflows.

## Features Not Tested

## Features Tested

### Mongo-ectomy and Installer changes
Feature: https://drive.google.com/open?id=1fJeLZefxSia0-XSS0Gx_jeG5lYXUkU8V1LD9juEnlDc

1. [ ] FIXME

### Notifications
Feature: https://drive.google.com/open?id=14qb12baMp5aYWVpxXGEKxiC_wX3ZpHe3Bf6hwUue9rI

1. [ ] FIXME

### RBAC Permission changes
Feature: https://drive.google.com/open?id=1n_hLt0vKV5ytyYtA5oj71QLKiWtKQkhVezbUvUj_npA

1. [ ] FIXME

### Prompt for all the things
Feature: https://drive.google.com/open?id=15iSHWjgCk0oyuHX9soWtClB9dOJ4Qlxm5H8fsTqoTuo

1. [ ] FIXME

### Database Config (e.g. /api/v1/settings)
Feature: https://drive.google.com/open?id=1Oc84TUnV2eh2Cy29vVfUfdJmV_qyg7NnTAEhuqoYdiQ

1. [ ] FIXME
 
### Tower UX/UI Refresh
Feature: https://drive.google.com/open?id=1fJeLZefxSia0-XSS0Gx_jeG5lYXUkU8V1LD9juEnlDc

1. [ ] FIXME

### Django Upgrade
Feature: https://drive.google.com/open?id=18RB73_CSFX6uSOZLmp9McHU1mVfhw5eUKNDEzJScnjA

1. [ ] FIXME

### Regression
1. [ ] UI regression completed
1. [ ] API regression completed
1. [ ] Munin monitors work on all supported platforms
1. [ ] Tower HA installation
    * [ ] Verify successful registration of secondary instances
    * [ ] Verify secondary web traffic redirects to primary (excluding /api/v1/ping/)
    * [ ] Verify promoting secondary instance
    * [ ] Verified tower-manage commands: [list_instances,register_instance,remove_instance,update_instance]
1. [ ] Tower LDAP Integration
    * [ ] Verify license enablement with legacy or enterprise license (disabled elsewhere).
    * [ ] Verify Tower respects LDAP username and password on login
    * [ ] Verify Tower creates user related objects on successful login (User, Teams, Organization, Admin_of_organizations).
    * [ ] Verify successful login for an Organization Administrator

#### Installation online installer
1. Installation completes successfully on all supported platforms
    * [ ] ubuntu-12.04
    * [ ] ubuntu-14.04
    * [ ] rhel-6.7
    * [ ] rhel-7.2
    * [ ] centos-6.7
    * [ ] centos-7.1
1. Installation completes successfully using supported ansible releases
    * [ ] ansible-2.0
    * [ ] ansible-1.9.x
    * [ ] ansible-1.8.x (manually tested on EL platforms)
1. Installation completes successfully on supported images
    * [ ] AMI (unlicensed)
    * [ ] Vagrant

#### Installation bundle installer
1. Installation completes successfully on all supported platforms
    * [ ] rhel-6.7
    * [ ] rhel-7.2
    * [ ] centos-6.7
    * [ ] centos-7.1

#### Upgrade installer
1. Upgrade completes on all supported platforms from `2.4.*`
    * [ ] ubuntu-12.04
    * [ ] ubuntu-14.04
    * [ ] rhel-6.7
    * [ ] rhel-7.2
    * [ ] centos-6.7
    * [ ] centos-7.1
1. Upgrade completes on all supported platforms from `2.3.*`
    * [ ] ubuntu-12.04
    * [ ] ubuntu-14.04
    * [ ] rhel-6.7
    * [ ] rhel-7.2
    * [ ] centos-6.7
    * [ ] centos-7.1
1. Verify the following functions work as intended after upgrade
    * [ ] Launch project_updates for existing projects
    * [ ] Launch inventory_udpates for existing inventory_source
    * [ ] Launch, and relaunch, existing job_templates
