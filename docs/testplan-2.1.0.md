# Tower 2.1.0 Release Test Plan

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
    [ ] rhel-7.0
    [ ] centos-6.5
    [ ] centos-7.0

2. Verify AWS AMI boot successfully, and includes the expected license information
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

2. [ ] Test upgrades using correct and incorrect values for the following fields: [admin_password, pg_password, rabbitmq_password]
3. [ ] Test upgrades with data, and ensure projects/inventory/jobs run post-upgrade

### Integration
1. [ ] End-to-end integration completed on all supported platforms

### Feature: Bind installer with package version
1. [ ] Verify setup playbook correctly installs a package within the desired version yum-based distros
2. [ ] Verify setup playbook correctly installs a package within the desired version apt-based distros
3. [ ] Verify using older setup playbook (with appropriate modifications) correctly installs older ansible-tower

### Feature: System Jobs
1. API - FIXME
2. UI - FIXME

### Feature: HA
1. Installer
    1. [ ] Verify ./configure completes successfully for localhost tower with internal db
    2. [ ] Verify ./configure completes successfully for remote tower with internal db
    3. [ ] Verify ./configure completes successfully for localhost tower with external db
    4. [ ] Verify ./configure completes successfully for remote tower with external db
    5. [ ] Verify ./configure completes successfully for localhost tower with external db and secondaries
    6. [ ] Verify ./configure completes successfully for remote tower with external db and secondaries
    7. [ ] Verify ./configure completes successfully when adding a secondary after initial install
2. Runtime
    1. [ ] Verify accessing secondary via http (application and /api) redirects to primary
    2. [ ] Verify no issues introduced wrt saving/reading job_stdout
    3. [ ] Verify incorrect usage of `tower-manage ha`
    4. [ ] Verify correct behavior when promoting a secondary
    5. [ ] Verify correct behavior when promoting a secondary while jobs are running

### Feature: Portal Mode UI
1. [ ] Verify portal URLs redirect after login
2. [ ] Verify login after timeout redirects to portal
3. [ ] Verify web-socket updates job status and job rows
3. [ ] Verify web-socket updates job status and

### Feature: Survey
1. API
  1. [ ] Verify posting various surveys to endpoint
  2. [ ] Verify /launch endpoint reflects state of enabled survey
  3. [ ] Verify variables supplied at /launch resource correctly passed to job
  4. [ ] Verify survey variables cannot overwrite job environment variables (HOME, PATH, _ etc...)
  5. [ ] Verify behavior when POSTing to /api/v1/jobs/N/relaunch -- (FIXME: what is the behavior?)

2. UI
  1. [ ] Verify survey modal dialogs hold up to monkey clicking
  2. [ ] Verify job_template creation and edit behaves as expected without a survey
  2. [ ] Verify enabling and creating a survey on job_template create+update
  3. [ ] Verify enabling and but *not* creating a survey on job_template create+update
  4. [ ] Verify disabling a survey on job_template create+update
  5. [ ] Verify survey modal on job launch accurately reflects survey questions
  6. [ ] Verify survey modal correctly submits variables to job

### Feature: Only superuser can create job without job_template
1. [ ] Verify that *only* superusers can POST to /api/v1/jobs

### Feature: VMware inventory_import updates
1. [ ] Verify VMware inventory_imports continue to import successfully and include more detailed information to access/filter VMware hosts

### Regresion
1. [ ] UI regression completed
2. [ ] API regression completed
