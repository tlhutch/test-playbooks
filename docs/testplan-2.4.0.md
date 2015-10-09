# Tower 2.4.0 Release Test Plan

## Resources
* 1 full-time quality engineer - cwang
* 1 part-time quality engineer - jlaska

## Assumptions
1. UI testing is performed manually.  While basic automated coverage exists, it is insufficient to test customer workflows.

## Features Not Tested
1. Comprehensive RBAC coverage is covered in API unit and integration tests, but not explicitly in the UI testing.

## Features Tested

### Pendo Integration
*QUESTION*: How to verify pendo communication?

1. [X] Verify settings.py honored (/api/v1/config/)
1. [X] Verify that three modes configurable: off, anonymous, and detailed
1. [ ] Verify correct tags for anonymous and detailed modes
1. [X] Verify that Pendo defaults to "Detailed" mode after fresh install
1. [ ] Verify that Pendo defaults to "Off" after upgrade in the absence of opt-in value
1. [X] Verify Pendo only gets downloaded when flagged appropriately in settings.py
1. [ ] Verify Pendo network requests

### Pluggable Authentication
*QUESTION*: who can help setup test environments

 1. [ ] Verify enablement/disablement via social_auth.py
 1. [ ] Verify [un]successful login with Google Hosted credentials
 1. [ ] Verify [un]successful login with SAML credentials
 1. [ ] Verify [un]successful login with RADIUS credentials
 1. [ ] Verify [un]successful login with GitHub credentials
 1. [ ] SAML and RADIUS are enterprise features

### Custom Rebranding

1. [X] Test base login modal image and text support
1. [X] Verify 'local_settings.json' support
1. [ ] Verify custom branding remains after upgrade (nightly)
1. [X] Verify custom branding remains after backup/restore
1. [X] Test bogus image sizes and formats
1. [ ] Verify that custom rebranding is enterprise only

### Session Fixes

1. [X] Verify number of concurrent logins (1, N)
1. [X] Verify new API timeout header exists for authentication connections
1. [ ] Ensure that websockets are disabled for logged-out users
1. [X] Verify UI honors HTTP timeout header
1. [X] Verify UI logs user out when token expires, even when user is idle
1. [ ] Verify logout modal
1. [X] Verify API honors HTTP timeout
1. [X] Verify that varying the timeout setting in `settings.py` causes appropriate newly set time results in HTTP headers
1. [X] With Tower loaded in multiple browser tabs, verify inactivity in one tab doesn't force a logout in another active tab

### Regression
1. [ ] Comprehensive RBAC coverage using EuroNext and NeuStar datasets
1. [ ] UI regression completed
1. [ ] API regression completed
1. [ ] End-to-end integration completed on all supported platforms
1. [ ] Munin monitors work on all supported platforms
1. [ ] Tower HA installation
    * [ ] Verify successful registration of secondary instances
    * [ ] Verify secondary web traffic redirects to primary (excluding /api/v1/ping/)
    * [ ] Verify promoting secondary instance
    * [ ] Verified tower-manage commands: [list_instances,register_instance,remove_instance,update_instance]
1. [ ] Tower LDAP Integration [jlaska]
    * [ ] Verify license enablement with legacy or enterprise license (disabled elsewhere).
    * [ ] Verify Tower respects LDAP username and password on login
    * [ ] Verify Tower creates user related objects on successful login (User, Teams, Organization, Admin_of_organizations).
    * [ ] Verify successful login for an Organization Administrator

#### Installation online installer
1. Installation completes successfully on all supported platforms
    * [ ] ubuntu-12.04
    * [ ] ubuntu-14.04
    * [ ] rhel-6.5
    * [ ] rhel-7.0
    * [ ] centos-6.5
    * [ ] centos-7.0
1. Installation completes successfully using supported ansible releases
    * [ ] ansible-2.0
    * [ ] ansible-1.9.x
    * [ ] ansible-1.8.x (not tested on *all* platforms)
1. Installation completes successfully on supported images
    * [ ] AMI (unlicensed) [jlaska]
    * [ ] Vagrant [jlaska]

#### Installation bundle installer
1. Installation completes successfully on all supported platforms
    * [ ] rhel 6.5
    * [ ] rhel 6.6
    * [ ] rhel 6.7
    * [ ] rhel 7.0
    * [ ] rhel 7.1
    * [ ] centos 6.5
    * [ ] centos 6.6
    * [ ] centos 6.7
    * [ ] centos 7.0
    * [ ] centos 7.1

#### Upgrade installer
1. Upgrade completes on all supported platforms from `2.3.*`
    * [ ] ubuntu-12.04
    * [ ] ubuntu-14.04
    * [ ] rhel-6.5
    * [ ] rhel-7.0
    * [ ] centos-6.5
    * [ ] centos-7.0
1. Upgrade completes on all supported platforms from `2.2.*`
    * [ ] ubuntu-12.04
    * [ ] ubuntu-14.04
    * [ ] rhel-6.5
    * [ ] rhel-7.0
    * [ ] centos-6.5
    * [ ] centos-7.0
1. Verify the following functions work as intended after upgrade
    * [ ] Launch project_updates for existing projects
    * [ ] Launch inventory_udpates for existing inventory_source
    * [ ] Launch, and relaunch, existing job_templates
