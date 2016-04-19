# Tower 2.4.5 Release Test Plan

## Resources
* 3 full-time quality engineers - cwang, jladdjr, jakemcdermott

## Assumptions
1. UI testing is performed manually.  While basic automated coverage exists, it is insufficient to test customer workflows.

## Features Not Tested

## Features Tested

### Regression
1. [x] API regression completed (Chris)
1. [x] Tower LDAP Integration (Chris)
    * [x] Verify license enablement with legacy or enterprise license (disabled elsewhere).
    * [x] Verify Tower respects LDAP username and password on login
    * [x] Verify Tower creates user related objects on successful login (User, Teams, Organization, Admin_of_organizations).
    * [x] Verify successful login for an Organization Administrator

#### Installation online installer
1. Installation completes successfully on all supported platforms (Chris)
    * [x] ubuntu-12.04
    * [x] ubuntu-14.04
    * [x] rhel-6.7
    * [x] rhel-7.2
    * [x] centos-6.7
    * [x] centos-7.1
1. Installation completes successfully using supported ansible releases
    * [x] ansible-2.0 (Chris)
    * [x] ansible-1.9.x (Jim)
1. Installation completes successfully on supported images
    * [X] AMI (unlicensed) (James)
    * [X] Vagrant (James)

#### Installation bundle installer
1. Installation completes successfully on all supported platforms (Jim)
    * [x] rhel-6.7
    * [x] rhel-7.2
    * [x] centos-6.7
    * [x] centos-7.1

#### Upgrade installer
1. Upgrade completes on all supported platforms from `2.4.4` (Jim)
    * [x] ubuntu-12.04
    * [x] ubuntu-14.04
    * [x] rhel-6.7
    * [x] rhel-7.2
    * [x] centos-6.7
    * [x] centos-7.1
1. Upgrade completes on all supported platforms from `2.3.*` (Chris)
    * [x] ubuntu-12.04
    * [x] ubuntu-14.04
    * [x] rhel-6.7
    * [x] rhel-7.2
    * [x] centos-6.7
    * [x] centos-7.2
1. Verify the following functions work as intended after upgrade (Everyone)
    * [x] Launch project_updates for existing projects
    * [x] Launch inventory_updates for existing inventory_source
    * [x] Launch, and relaunch, existing job_templates
