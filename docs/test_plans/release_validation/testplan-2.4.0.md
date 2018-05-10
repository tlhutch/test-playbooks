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

1. [X] Verify settings.py honored (/api/v1/config/)
1. [X] Verify that three modes configurable: off, anonymous, and detailed
1. [X] Verify correct tags for anonymous and detailed modes
1. [X] Verify that Pendo defaults to "Detailed" mode after fresh install
1. [X] Verify that Pendo defaults to "Off" after upgrade in the absence of opt-in value
1. [X] Verify Pendo only gets downloaded when flagged appropriately in settings.py
1. [X] Verify Pendo network requests

### Pluggable Authentication

 1. [X] Verify enablement/disablement via social_auth.py
 1. [X] Verify [un]successful login with Google Hosted credentials
 1. [X] Verify [un]successful login with SAML credentials
 1. [X] Verify [un]successful login with RADIUS credentials
 1. [X] Verify [un]successful login with GitHub credentials
 1. [X] SAML and RADIUS are enterprise features

### Custom Rebranding

1. [X] Test base login modal image and text support
1. [X] Verify 'local_settings.json' support
1. [X] Verify custom branding remains after upgrade (nightly)
1. [X] Verify custom branding remains after backup/restore
1. [X] Test bogus image sizes and formats

### Session Fixes

1. [X] Verify number of concurrent logins (1, N)
1. [X] Verify new API timeout header exists for authentication connections
1. [X] Ensure that websockets are disabled for logged-out users
1. [X] Verify UI honors HTTP timeout header
1. [X] Verify UI logs user out when token expires, even when user is idle
1. [X] Verify logout modal
1. [X] Verify API honors HTTP timeout
1. [X] Verify that varying the timeout setting in `settings.py` causes appropriate newly set time results in HTTP headers
1. [X] With Tower loaded in multiple browser tabs, verify inactivity in one tab doesn't force a logout in another active tab

### Regression
1. [X] UI regression completed
1. [X] API regression completed
1. [X] Munin monitors work on all supported platforms
1. [X] Tower cluster installation
    * [X] Verify successful registration of secondary instances
    * [X] Verify secondary web traffic redirects to primary (excluding /api/v1/ping/)
    * [X] Verify promoting secondary instance
    * [X] Verified tower-manage commands: [list_instances,register_instance,remove_instance,update_instance]
1. [X] Tower LDAP Integration [jlaska]
    * [X] Verify license enablement with legacy or enterprise license (disabled elsewhere).
    * [X] Verify Tower respects LDAP username and password on login
    * [X] Verify Tower creates user related objects on successful login (User, Teams, Organization, Admin_of_organizations).
    * [X] Verify successful login for an Organization Administrator

#### Installation online installer
1. Installation completes successfully on all supported platforms
    * [X] ubuntu-12.04
    * [X] ubuntu-14.04
    * [X] rhel-6.5
    * [X] rhel-7.0
    * [X] centos-6.5
    * [X] centos-7.0
1. Installation completes successfully using supported ansible releases
    * [X] ansible-2.0
    * [X] ansible-1.9.x
    * [X] ansible-1.8.x (manually tested on EL platforms)
1. Installation completes successfully on supported images
    * [ ] AMI (unlicensed) [jlaska]
    * [X] Vagrant

#### Installation bundle installer
1. Installation completes successfully on all supported platforms
    * [X] rhel-6
    * [X] rhel-7
    * [X] centos-6
    * [X] centos-7

#### Upgrade installer
1. Upgrade completes on all supported platforms from `2.3.*`
    * [X] ubuntu-12.04
    * [X] ubuntu-14.04
    * [X] rhel-6.5
    * [X] rhel-7.0
    * [X] centos-6.5
    * [X] centos-7.0
1. Upgrade completes on all supported platforms from `2.2.*`
    * [ ] ubuntu-12.04
    * [ ] ubuntu-14.04
    * [ ] rhel-6.5
    * [ ] rhel-7.0
    * [ ] centos-6.5
    * [ ] centos-7.0
1. Verify the following functions work as intended after upgrade
    * [X] Launch project_updates for existing projects
    * [X] Launch inventory_udpates for existing inventory_source
    * [X] Launch, and relaunch, existing job_templates
