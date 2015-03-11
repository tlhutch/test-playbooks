# Tower 2.2.0 Release Test Plan

## Resources
* 2 full-time quality engineer (cwang, jlaska)

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
    [ ] rhel-7.0
    [ ] centos-6.5
    [ ] centos-7.0

2. Installation completes successfully using supported ansible releases
    [ ] ansible-2.0
    [ ] ansible-1.9.x
    [ ] ansible-1.8.x

3. Verify AWS AMI boot successfully, and includes the expected license information
    [ ] license: unlicensed
    [ ] license: 100

### Upgrade
1. Upgrade completes on all supported platforms
    [ ] ubuntu-12.04
    [ ] ubuntu-14.04
    [ ] rhel-6.5
    [ ] rhel-7.0
    [ ] centos-6.5
    [ ] centos-7.0

2. [ ] Test upgrades using correct and incorrect values for the following fields: [admin_password, pg_password, redis_password, munin_password]
3. [ ] Test upgrades with data, and ensure projects/inventory/jobs run post-upgrade

### Integration
1. [ ] End-to-end integration completed on all supported platforms

### Feature: Job Template Status

### Feature: Ad Hoc Commands

### Feature: Product Differentiation

### Feature: Compliance

### Feature: UI Refresh

### Feature: OpenStack Inventory

### Regresion
1. [ ] UI regression completed
2. [ ] API regression completed
3. [ ] Munin monitors work on all supported platforms

## Retrospective

This section is intended to gather feedback on things that worked well and
things that could have been better during the release cycle. The feedback will
be used as a basis for identifying areas for improvement for future releases.
Any thoughts, big or small, are valuable.

### Feedback/issues/concerns

### Recommendations
