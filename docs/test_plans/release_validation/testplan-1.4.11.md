# Tower 1.4.11 Release Test Plan

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
    [x] rhel-7.0 (rc)
    [x] centos-6.5

### Upgrade
1. Upgrade completes on all supported platforms
    [x] ubuntu-12.04
    [x] ubuntu-14.04
    [x] rhel-6.5
    [x] rhel-7.0 (beta)
    [x] centos-6.5
2. [x] Test upgrades using the proper username/password (should pass)
3. [x] Test upgrades using the improper username/password (should use existing password, pass)
4. [x] Test upgrades with data, and ensure projects/inventory/jobs run post-upgrade

### Integration
1. [x] End-to-end integration completed on all supported platforms
2. [x] Add inventory_import tests
3. [x] Add group disassociate/delete tests

### Feature: Installation improvements
1. [x] Verify setup playbook w/o ansible installed
1. [x] Verify setup playbook success (setup.log is saved to /var/log/awx/, appropriate message to console)
1. [x] Verify setup playbook failure (setup.log is saved to /var/log/awx/, appropriate message to console)

### Feature: Inventory Performance
1. [x] Verify POST to /inventory/N/groups/
2. [x] Verify POST to /groups/N/children/
3. [x] Verify DELETE to /groups/N/
4. [x] Verify splunk inventory data
4. [x] Verify UI behaves as expected

### UI Regresion
1. [x] Verify links from Dashboard are correct
1. [x] Verify organization CRUD
1. [x] Verify user CRUD
1. [ ] Verify team CRUD
1. [ ] Verify project CRUD
1. [ ] Verify inventory CRUD
1. [ ] Verify group CRUD
1. [ ] Verify host CRUD
1. [ ] Verify job_template CRUD
1. [ ] Verify job CRUD
1. [ ] Verify job dialog tabs for various job types present correct information
