# Tower 1.4.12 Release Test Plan

## Resources
* 1 full-time quality engineer (jlaska)

## Assumptions
1. UI testing is performed manually.  While basic automated coverage exists, it is insufficient to test customer workflows.

## Features Not Tested
1. Comprehensive RBAC coverage

## Features Tested

### Installation
1. Installation completes successfully on all supported platforms
    [x] ubuntu-12.04
    [x] ubuntu-14.04
    [x] rhel-6.5
    [x] rhel-7.0 (ansible installed via pip)
    [x] centos-6.5

### Upgrade
1. Upgrade completes on all supported platforms
    [x] ubuntu-12.04
    [x] ubuntu-14.04
    [x] rhel-6.5
    [ ] rhel-7.0 - unable to validate due to missing optional repo
    [x] centos-6.5
2. [x] Test upgrades using the proper username/password (should pass)
3. [x] Test upgrades using the improper username/password (should use existing password, pass)
4. [x] Test upgrades with data, and ensure projects/inventory/jobs run post-upgrade

### Integration
1. [x] End-to-end integration completed on all supported platforms
2. [x] Added automated test to verify that unicode playbook output is properly handled by Tower
3. [x] Manually verified that variables in ansible playbook stdout display correctly

### UI Regresion
1. [X] Verify links from Dashboard are correct
1. [X] Verify organization CRUD
1. [X] Verify user CRUD
1. [X] Verify team CRUD
1. [X] Verify project CRUD
1. [X] Verify inventory CRUD
1. [X] Verify group CRUD
1. [X] Verify host CRUD
1. [ ] Verify job_template CRUD
1. [ ] Verify job CRUD
1. [ ] Verify job dialog tabs for various job types present correct information
