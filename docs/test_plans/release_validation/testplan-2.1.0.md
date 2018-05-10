# Tower 2.1.0 Release Test Plan

## Resources
* 2 full-time quality engineer (cwang, jlaska)

## Assumptions
1. UI testing is performed manually.  While basic automated coverage exists, it is insufficient to test customer workflows.

## Features Not Tested
1. Comprehensive RBAC coverage

## Features Tested

### Installation
1. Installation completes successfully on all supported platforms
    [X] ubuntu-12.04
    [X] ubuntu-14.04
    [X] rhel-6.5
    [X] rhel-7.0
    [X] centos-6.5
    [X] centos-7.0

2. Installation completes successfully using supported ansible releases
    [X] ansible-1.9.x (devel)
    [X] ansible-1.8.x
    [X] ansible-1.7.x

3. Verify AWS AMI boot successfully, and includes the expected license information
    [X] license: unlicensed
    [X] license: 100

### Upgrade
1. Upgrade completes on all supported platforms
    [X] ubuntu-12.04
    [X] ubuntu-14.04
    [X] rhel-6.5
    [X] rhel-7.0
    [X] centos-6.5
    [X] centos-7.0

2. [X] Test upgrades using correct and incorrect values for the following fields: [admin_password, pg_password, redis_password, munin_password]
3. [X] Test upgrades with data, and ensure projects/inventory/jobs run post-upgrade

### Integration
1. [X] End-to-end integration completed on all supported platforms

### Feature: Bind installer with package version
1. [X] Verify setup playbook correctly installs a package within the desired version yum-based distros
2. [X] Verify setup playbook correctly installs a package within the desired version apt-based distros
3. [X] Verify using older setup playbook (with appropriate modifications) correctly installs older ansible-tower

### Feature: System Jobs
1. API
  1. [X] Verify only accessible to superuser
2. UI
  1. [X] Verify system job modal dialogs hold up to monkey clicking
  2. [X] Verify system job schedules

### Feature: Cluster
1. Installer
    1. [X] Verify `configure` completes successfully for localhost tower with internal db
    2. [X] Verify `configure` completes successfully for remote tower with internal db
    3. [X] Verify `configure` completes successfully for localhost tower with external db
    4. [X] Verify `configure` completes successfully for remote tower with external db
    5. [X] Verify `configure` completes successfully for localhost tower with external db and secondaries
    6. [X] Verify `configure` completes successfully for remote tower with external db and secondaries
    7. [X] Verify `setup.sh` completes successfully when adding a secondary after initial install
    8. [X] Verify adding secondaries to `inventory` and rerunning./setup.sh works
    9. [X] Verify running `configure` and `setup.sh` on a secondary successfully installs and adds to cluster deployment
2. Runtime
    1. [X] Verify accessing secondary via http (application and /api) redirects to primary
    2. [X] Verify no issues introduced wrt saving/reading job_stdout
    3. [X] Verify incorrect usage of `tower-manage register_instance` (several low priority issues filed)
    4. [X] Verify promoting a secondary
    5. [X] Verify promoting a secondary when jobs are running
    6. [X] Verify promoting a secondary when the primary is unreachable
    9. [X] Verify removing a secondary with --hostname=<valid>
    10. [X] Verify removing a secondary with --uuid=<valid>
    11. [X] Verify changing primary hostname with with --hostname=<valid> --primary
    12. [X] Verify changing secondary hostname with with --hostname=<valid> --secondary
    13. [X] Verify integration completes successfully in a cluster environment

### Feature: Multi-tenancy
1. [X] Verify when AWX_PROOT_ENABLED, a job is unable to view details from other jobs on disk.  Includes the following:
     - /var/lib/awx/projects/ - only a single directory exists for the current job
     - /var/lib/awx/job_status/ - no files are present (job status isn't created until after a job completes)
     - /tmp/ansible_tower_* - only a single matching directory exists
     - /etc/awx/settings.py - No such file or directory
     - /var/log/supervisor/* - Permission Denied
2. [X] Verify when AWX_PROOT_ENABLED, a custom_inventory_script is unable to view details from other jobs on disk.  Includes the above expectations.

### Feature: Portal Mode UI
1. [X] Add a survey showing all the question types
1. [X] Validate the survey can set variables
1. [X] Test all question types and constraints
1. [X] Ensure navigation from portal -> main -> portal works
1. [X] Makes sure there the “can_launch” behavior of the job API indicates when a survey is enabled
1. [X] Make sure disabling the survey doesn’t delete the survey
1. [X] Make sure survey has precedence over “prompt for variables”
1. [X] Make sure both prompt for variables and survey can be used seperately
1. [X] Make sure the API validates survey responses if submitted directly and not via API
1. [X] Verify portal URLs redirect after login
1. [X] Verify login after timeout redirects to portal
1. [X] Verify web-socket updates job status and job rows

### Feature: Survey
1. API
  1. [X] Verify posting various surveys to endpoint
  2. [X] Verify /launch endpoint reflects state of enabled survey
  3. [X] Verify variables supplied at /launch resource correctly passed to job
  4. [X] Verify survey variables cannot overwrite job environment variables (HOME, PATH, _ etc...)
  5. [X] Verify behavior when POSTing to /api/v1/jobs/N/relaunch

2. UI
  1. [X] Verify survey modal dialogs hold up to monkey clicking
  2. [X] Verify job_template creation and edit behaves as expected without a survey
  2. [X] Verify enabling and creating a survey on job_template create+update
  3. [X] Verify enabling and but *not* creating a survey on job_template create+update
  4. [X] Verify disabling a survey on job_template create+update
  5. [X] Verify survey modal on job launch accurately reflects survey questions
  6. [X] Verify survey modal correctly submits variables to job

### Feature: EC2 instance_filters and group_by
1. [X] Verify valid and invalid inputs to group_by
2. [X] Verify valid and invalid inputs to instance_filters
3. [X] Verify group_by limits group creation to provided list
4. [X] Verify instance_filters honored on host import

### Feature: Only superuser can create job without job_template
1. [X] Verify that *only* superusers can POST to /api/v1/jobs

### Feature: VMware inventory_import updates
1. [X] Verify VMware inventory_imports continue to import successfully and include more detailed information to access/filter VMware hosts

### Feature: Custom Inventory Scripts
1. UI
   1. [X] Verify account menu option only available for superuser
   2. [X] Verify basic inventory_script modal functionality
   3. [X] Verify basic inventory_script table functionality (searching, sorting, pagination)
2. API
   1. [X] Verify non-superusers cannot create/edit/delete inventory_scripts
   2. [X] Verify anonymous users cannot see inventory_scripts
   3. [X] Verify org_users can see inventory_scripts, but cannot read 'script' contents
   4. [X] Verify superusers have full access

### Regresion
1. [X] UI regression completed
2. [X] API regression completed
3. [ ] Munin monitors work on all supported platforms

## Retrospective

This section is intended to gather feedback on things that worked well and
things that could have been better during the release cycle. The feedback will
be used as a basis for identifying areas for improvement for future releases.
Any thoughts, big or small, are valuable.

### Feedback/issues/concerns

* QA UI automation exists, but isn't run on a regular automatic basis through jenkins.  Several UI changes to improve UI test-ability introduced regressions elsewhere in the UI.  These would have been caught with existing UI automation.
* We didn't specify the cluster tower-manage interfaces in a detailed fashion in the spec (or update it), and eng didn't publish a "this is what we're doing" guide, so we end up reverse-engineering what got done, and QE isn't sure what to test, or what is supported.

### Recommendations

1. Selenium UI automation needs to be fully automated by jenkins
