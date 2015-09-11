# Tower 2.3.0 Release Test Plan

## Resources
* 1 full-time quality engineer - cwang
* 1 part-time quality engineer - jlaska

## Assumptions
1. UI testing is performed manually.  While basic automated coverage exists, it is insufficient to test customer workflows.

## Features Not Tested
1. Comprehensive RBAC coverage is covered in API unit and integration tests, but not explicitly in the UI testing.

## Features Tested

### Installation online installer
1. Installation completes successfully on all supported platforms
    * [x] ubuntu-12.04
    * [x] ubuntu-14.04
    * [x] rhel-6.5
    * [x] rhel-7.0
    * [x] centos-6.5
    * [x] centos-7.0
1. Installation completes successfully using supported ansible releases
    * [x] ansible-2.0
    * [x] ansible-1.9.x
    * [x] ansible-1.8.x (not tested on *all* platforms)
1. Installation completes successfully on supported images
    * [ ] AMI (unlicensed) [jlaska]
    * [ ] Vagrant [jlaska]

### Installation bundle installer
1. Installation completes successfully on all supported platforms
    * [X] rhel 6.5
    * [X] rhel 6.6
    * [X] rhel 6.7
    * [X] rhel 7.0
    * [X] rhel 7.1
    * [X] centos 6.5
    * [X] centos 6.6
    * [X] centos 6.7
    * [X] centos 7.0
    * [X] centos 7.1

### Upgrade online installer
1. Upgrade completes on all supported platforms from `2.2.*`
    * [X] ubuntu-12.04
    * [X] ubuntu-14.04
    * [X] rhel-6.5
    * [X] rhel-7.0
    * [X] centos-6.5
    * [X] centos-7.0
1. Upgrade completes on all supported platforms from `2.1.*`
    * [X] ubuntu-12.04
    * [X] ubuntu-14.04
    * [X] rhel-6.5
    * [X] rhel-7.0
    * [X] centos-6.5
    * [X] centos-7.0
1. Verify the following functions work as intended after upgrade
    * [x] Launch project_updates for existing projects
    * [x] Launch inventory_udpates for existing inventory_source
    * [x] Launch, and relaunch, existing job_templates

### Integration
1. [X] End-to-end integration completed on all supported platforms

### Feature: Offline installer
1. [X] Retest the configure script
1. [X] Running the installer on the same box as Tower
1. [X] Running the installer on a different box as Tower and connecting remotely (sudo and su)
1. [X] Installer is single downloadable object
1. [X] Installer signed by Ansible
1. [X] Installer contains all non-distribution dependencies needed to install Ansible and Tower
1. [X] Installation of non-distribution dependencies should use the bundled repository
1. [X] Installer includes list of vendor repositories
1. [X] Installer should leave pre-existing versions of Ansible intact
1. [X] Integration passes

### Feature: Package Signing
1. [X] Verified creation and install of signed DEB builds
1. [X] Verified creation and install of signed RPM builds
1. [X] Verified manual creation of signed TAR builds
1. [X] Verified manual creation of signed Bundle_TAR builds

### Regression
1. [X] UI regression completed
1. [X] API regression completed
1. [X] Munin monitors work on all supported platforms
1. [X] Tower HA installation [jlaska]
    * [X] Verify successful registration of secondary instances
    * [X] Verify secondary web traffic redirects to primary (excluding /api/v1/ping/)
    * [X] Verify promoting secondary instance
    * [X] Verified tower-manage commands: [list_instances,register_instance,remove_instance,update_instance]
1. [X] Tower LDAP Integration [jlaska]
    * [X] Verify license enablement with legacy or enterprise license (disabled elsewhere).
    * [X] Verify Tower respects LDAP username and password on login
    * [X] Verify Tower creates user related objects on successful login (User, Teams, Organization, Admin_of_organizations).
    * [X] Verify successful login for an Organization Administrator
