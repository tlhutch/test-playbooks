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
    [ ] ubuntu-12.04
    [ ] ubuntu-14.04
    [ ] rhel-6.5
    [ ] rhel-7.0 (beta)
    [ ] centos-6.5

### Upgrade
1. Upgrade completes on all supported platforms
    [ ] ubuntu-12.04
    [ ] ubuntu-14.04
    [ ] rhel-6.5
    [ ] rhel-7.0 (beta)
    [ ] centos-6.5
2. [ ] Test upgrades using the proper username/password (should pass)
3. [ ] Test upgrades using the improper username/password (should use existing password, pass)
4. [ ] Test upgrades with data, and ensure projects/inventory/jobs run post-upgrade

### Integration
1. [ ] End-to-end integration completed on all supported platforms
2. [ ] Add inventory_import tests
3. [ ] Add group disassociate/delete tests

### Feature: Installation improvements
1. [ ] Verify setup playbook w/o ansible installed
1. [ ] Verify setup playbook success (setup.log is saved to /var/log/awx/, appropriate message to console)
1. [ ] Verify setup playbook failure (setup.log is saved to /var/log/awx/, appropriate message to console)

### Feature: Inventory Performance
1. [ ] Verify POST to /inventory/N/groups/
2. [ ] Verify POST to /groups/N/children/
3. [ ] Verify DELETE to /groups/N/
4. [ ] Verify splunk inventory data
4. [ ] Verify UI behaves as expected

### UI Regresion
1. [ ] Verify links from Dashboard are correct
1. [ ] Verify organization CRUD
1. [ ] Verify user CRUD
1. [ ] Verify team CRUD
1. [ ] Verify project CRUD
1. [ ] Verify inventory CRUD
1. [ ] Verify group CRUD
1. [ ] Verify host CRUD
1. [ ] Verify job_template CRUD
1. [ ] Verify job CRUD
1. [ ] Verify job dialog tabs for various job types present correct information
