# Tower 3.6.0: Release Test Plan

## Table of Contents

  * [Resources](#resources)
  * [Supported Platforms](#supported-platforms)
    * [Ansible Versions](#ansible-versions)
    * [Operating Systems Versions](#operating-systems-versions)
  * [Features Tested](#features-tested)
  * [Verifications Steps](#verifications-steps)
    * [Install](#install)
    * [Upgrade](#upgrade)
    * [Regression](#regression)
    * [Artifacts](#arfifacts)

## Resources

* Quality Engineers Danny, Elijah, Elyezer, John, Mat, Yanis, Apurva, Caleb
* Initial planning document for whole engineering org (API + UI + QE) [here](https://docs.google.com/spreadsheets/d/1NNTN-SBM23UQPZAH9HylKhYQBAoyIsDcTlvl_ItDzHs/edit#gid=762158314)
* Ansible Tower 3.6.0 Project [here](https://github.com/orgs/ansible/projects/8)

## Supported Platforms

### Ansible Versions

  * stable-2.7
  * stable-2.8
  * stable-2.9

### Operating Systems Versions

  * RHEL Derivatives 7.4+
  * RHEL Derivatives 8.0+

**Note**: Starting with Ansible Tower release 3.6.0 Oracle Enterprise Linux won't be supported anymore.

## Features Tested

### Remove Ubuntu support (Yanis/Elijah)

- [x] [Testing complete](https://github.com/ansible/tower-qa/issues/3405)

### Remove /api/v1 (Elijah/Elyezer/Danny)

- [x] [Testing complete](https://github.com/ansible/tower-qa/issues/2935)

### Upgrade Django 2.2 LTS and DJRF (Yanis/Danny)

- [x] Testing complete (Existing regression testing was used for validation)

### Upgrade Node LTS (Yanis/Danny)

- [x] [Testing complete](https://github.com/ansible/tower-qa/issues/3407)

### Container Groups (Mat/Elijah/Danny)

- [x] [Testing complete](https://github.com/ansible/tower-qa/issues/3443)

### Remove Inventory computed field (Elijah/Elyezer)

- [x] PUNTED

### SSL for PostgreSQL and RabbitMQ (Yanis/Elijah)

- [x] [Testing complete](https://github.com/ansible/tower-qa/pull/4169)

### Override SCM Branch on JT and related enhancements (Elijah/Caleb)

  - [x] [Testing complete](https://github.com/ansible/tower-qa/blob/devel/docs/test_plans/features/36_branch_on_jt.md)

### Subscription and Enforcement License Changes (Elijah/Caleb)

  - [x] [Testing complete](https://github.com/ansible/tower-qa/blob/devel/docs/test_plans/features/36_license_changes.md)

### Primary Galaxy Server (Danny, Mat, Elyezer, Caleb)

  - [x] [Testing complete](https://github.com/ansible/tower-qa/blob/devel/docs/test_plans/features/36_primary_galaxy_server.md)

### Project with Collections Requirements (Eleyzer, Mat, Danny, Caleb)

  - [x] [Testing complete](https://github.com/ansible/tower-qa/blob/devel/docs/test_plans/features/36_project_with_collections_requirements.md)

### Supported CLI shipped with Tower (Elijah, Caleb)

  - [x] [Testing complete](https://github.com/ansible/tower-qa/blob/devel/docs/test_plans/features/36_supported_cli.md)

### Templated Notifications (Yanis, Mat, John)

  - [x] [Testing complete](https://github.com/ansible/tower-qa/blob/devel/docs/test_plans/features/36_templated_notification.md)

### Upgrade to PostgresSQL 10 (Yanis, Mat)

  - [x] [Testing complete](https://github.com/ansible/tower-qa/blob/devel/docs/test_plans/features/36_upgrade_to_postgres10.md)

### Webhook notification enhancement (Yanis, Mat, John)

  - [x] [Testing complete](https://github.com/ansible/tower-qa/blob/devel/docs/test_plans/features/36_webhook_notification.md)

### Webhook receiver (Mat, Elyezer, Apurva, Danny)

  - [x] [Testing complete](https://github.com/ansible/tower-qa/issues/4088)

### Workflow Limit and scm_branch Prompting (Caleb, Danny)

  - [x] [Testing complete](https://github.com/ansible/tower-qa/blob/devel/docs/test_plans/features/36_workflow_limit.md)

### Workflow Approval Nodes (Apurva, Elijah)

  - [x] [Testing complete](https://github.com/ansible/tower-qa/blob/devel/docs/test_plans/features/36_workflow_pause_approve.md)

### Workflow Approval Notifications (Apurva, Elijah)

  - [x] [Testing complete](https://github.com/ansible/tower-qa/issues/4089)

### Automation Analytics (Mat, Elyezer)

  - [x] [Testing complete](https://github.com/ansible/tower-qa/issues/3444)



## Verifications steps

### Install

  * [x] Standalone (automated)
    * [x] [RHEL 7.6](http://jenkins.ansible.eng.rdu2.redhat.com/job/Pipelines/job/integration-pipeline/6732/)
    * [x] [RHEL 8.0](http://jenkins.ansible.eng.rdu2.redhat.com/job/Pipelines/job/integration-pipeline/6724/)
  * [x] Standalone Bundle (automated)
    * [x] [RHEL 7.6](http://jenkins.ansible.eng.rdu2.redhat.com/job/Pipelines/job/integration-pipeline/6735/)
    * [x] [RHEL 8.0](http://jenkins.ansible.eng.rdu2.redhat.com/job/Pipelines/job/integration-pipeline/6727/)
  * [x] Traditional Cluster with isolated nodes (automated)
    * [x] [RHEL 7.6](http://jenkins.ansible.eng.rdu2.redhat.com/job/Pipelines/job/integration-pipeline/6745/)
    * [x] [RHEL 8.0](http://jenkins.ansible.eng.rdu2.redhat.com/job/Pipelines/job/integration-pipeline/6738/)
  * [x] Traditional Cluster Bundle with isolated nodes (automated)
    * [x] [RHEL 7.6](http://jenkins.ansible.eng.rdu2.redhat.com/job/Pipelines/job/integration-pipeline/6750/)
    * [x] [RHEL 8.0](http://jenkins.ansible.eng.rdu2.redhat.com/job/Pipelines/job/integration-pipeline/6739/)
  * [x] [OpenShift Cluster (automated)](http://jenkins.ansible.eng.rdu2.redhat.com/job/Pipelines/job/openshift-integration-pipeline/123/)


### Upgrade


  * [x] [OpenShift 3.4.x to Release](http://jenkins.ansible.eng.rdu2.redhat.com/job/Pipelines/job/Release%2034%20to%20devel%20-%20OpenShift%20-%20Release%20Verification/13/)
  * [x] [OpenShift 3.5.x to Release](http://jenkins.ansible.eng.rdu2.redhat.com/job/Pipelines/job/upgrade-release35-openshift-release-verification/17/)
  * Non-OpenShift 3.4.x to Release: Use this [Pipeline](http://jenkins.ansible.eng.rdu2.redhat.com/job/Pipelines/job/upgrade-release34-release-verification/) to verify
    * [x] [Non-OpenShift 3.4.x to Release](http://jenkins.ansible.eng.rdu2.redhat.com/job/Pipelines/job/upgrade-release34-release-verification/18/)
  * Non-OpenShift 3.5.x to Release: Use this [Pipeline](http://jenkins.ansible.eng.rdu2.redhat.com/job/Pipelines/job/upgrade-release35-release-verification/) to verify
    * [x] [Non-OpenShift 3.5.x to Release - RHEL 7.6](http://jenkins.ansible.eng.rdu2.redhat.com/job/Pipelines/job/upgrade-release35-release-verification/8/)
    * [x] [Non-OpenShift 3.5.x to Release - RHEL 8.0](http://jenkins.ansible.eng.rdu2.redhat.com/job/Pipelines/job/upgrade-release35-release-verification/6/)

  * [ ] 3.4.{0-5} -> Release
    * [x] [Bundle/Plain - Standalone/Cluster - non FIPS](http://jenkins.ansible.eng.rdu2.redhat.com/job/Pipelines/job/upgrade-release34-release-verification/18/)
    * [ ] [Bundle/Plain - Standalone/Cluster - FIPS](http://jenkins.ansible.eng.rdu2.redhat.com/job/Pipelines/job/upgrade-release34-release-verification/19/)
    * [ ] [OpenShift]
  * [x] 3.5.{0-3} -> Release
    * [x] [RHEL8 Bundle Cluster 3.5.3 to release](http://jenkins.ansible.eng.rdu2.redhat.com/job/Pipelines/job/upgrade-pipeline/18644/)
    * [x] [RHEL8 Bundle Standalone 3.5.3 to release](http://jenkins.ansible.eng.rdu2.redhat.com/job/Pipelines/job/upgrade-pipeline/18643/)
    * [x] [RHEL8 Plain Cluster 3.5.3 to release](http://jenkins.ansible.eng.rdu2.redhat.com/job/Pipelines/job/upgrade-pipeline/18642/parameters/)
    * [x] [RHEL8 Plain Standalone 3.5.3 to release](http://jenkins.ansible.eng.rdu2.redhat.com/job/Pipelines/job/upgrade-pipeline/18641/)
    * [x] [OpenShift](http://jenkins.ansible.eng.rdu2.redhat.com/job/Pipelines/job/upgrade-release35-openshift-release-verification/18/)

### Other

  * [x] Check ansible version check that is [hardcoded in tower-packaging](https://github.com/ansible/tower-packaging/blob/release_3.6.0/setup/roles/preflight/defaults/main.yml#L6)
  * [x] Check that Tower minimum version in the update is at n - 2 [value](https://github.com/ansible/tower-packaging/blob/release_3.6.0/setup/roles/preflight/tasks/main.yml#L78-L81)

### Regression

  * [x] [UI regression] (automated + manual monday 28th october)
  * [x] API regression - Standalone w/ TLS enabled
    * [x] [API regression - Standalone w/ TLS enabled RHEL 7.6](http://jenkins.ansible.eng.rdu2.redhat.com/job/Test_Tower_Yolo_Express/6793/)
    * [x] [API regression - Standalone w/ TLS enabled RHEL 7.7](http://jenkins.ansible.eng.rdu2.redhat.com/job/Test_Tower_Yolo_Express/6774/)
    * [x] [API regression - Standalone w/ TLS enabled RHEL 8.0](http://jenkins.ansible.eng.rdu2.redhat.com/job/Test_Tower_Yolo_Express/6784/)
      * [Re-run of the services tests](http://jenkins.ansible.eng.rdu2.redhat.com/job/Test_Tower_Yolo_Express/6798/)
  * [x] [API regression - Standalone w/ TLS disabled] (automated)
    * [x] [API regression - Standalone w/ TLS disabled RHEL 7.6](http://jenkins.ansible.eng.rdu2.redhat.com/job/Test_Tower_Yolo_Express/6879/)
    * [x] [API regression - Standalone w/ TLS disabled RHEL 7.7](http://jenkins.ansible.eng.rdu2.redhat.com/job/Test_Tower_Yolo_Express/6880/)
    * [x] [API regression - Standalone w/ TLS disabled RHEL 8.0](http://jenkins.ansible.eng.rdu2.redhat.com/job/Test_Tower_Yolo_Express/6881/)
  * [x] API regression - Traditional Cluster w/ TLS enabled
    * [x] [API regression - Traditional Cluster w/ TLS enabled RHEL 7.7](http://jenkins.ansible.eng.rdu2.redhat.com/job/Test_Tower_Yolo_Express/6776/)
    * [x] [API regression - Traditional Cluster w/ TLS enabled RHEL 8.0](http://jenkins.ansible.eng.rdu2.redhat.com/job/Test_Tower_Yolo_Express/6796/)
  * [x] [API regression - Traditional Cluster w/ TLS disabled] (automated)
    * [x] [API regression - Traditional Cluster w/ TLS disabled RHEL 7.6](http://jenkins.ansible.eng.rdu2.redhat.com/job/Test_Tower_Yolo_Express/6888/)
    * [x] [API regression - Traditional Cluster w/ TLS disabled RHEL 7.7](http://jenkins.ansible.eng.rdu2.redhat.com/job/Test_Tower_Yolo_Express/6889/)
    * [x] [API regression - Traditional Cluster w/ TLS disabled RHEL 8.0](http://jenkins.ansible.eng.rdu2.redhat.com/job/Test_Tower_Yolo_Express/6883/)
  * [x] [API regression - OpenShift Cluster](http://jenkins.ansible.eng.rdu2.redhat.com/job/Pipelines/job/openshift-integration-pipeline/129/)
  * [x] Tower social authentication regression completed (vm)
    * [x] Google OAuth (@elijah + @appuk)
    * [x] GitHub (@elijah + @appuk)
    * [x] GitHub Org (@elijah + @appuk)
    * [x] GitHub Team (@elijah + @appuk)
    * [x] Azure OAuth (@elyezer)
    * [x] Radius (@one-t)
  * [x] Tower SAML integration regression completed (vm) (@one-t)
  * [x] [Backup/restore successful - standalone](http://jenkins.ansible.eng.rdu2.redhat.com/job/Pipelines/job/backup-and-restore-pipeline/8842/)
  * [x] [Backup/restore successful - traditional cluster](http://jenkins.ansible.eng.rdu2.redhat.com/job/Pipelines/job/backup-and-restore-pipeline/8848/)
  * [x] [Backup/restore successful - OpenShift](http://jenkins.ansible.eng.rdu2.redhat.com/job/Pipelines/job/openshift-backup-and-restore-pipeline/92/)
  * [x] Deploy tower in OpenShift with an external DB + run tests against instance (@elijah + @calebb)
        - found and fixed https://github.com/ansible/tower-packaging/issues/482


### Artifacts

Use this [Pipeline](http://jenkins.ansible.eng.rdu2.redhat.com/job/Pipelines/job/build-artifacts-pipeline/) to verify

  * [x] [AMI](http://jenkins.ansible.eng.rdu2.redhat.com/job/Build_Tower_Image/477/)
  * [x] [Vagrant image](http://jenkins.ansible.eng.rdu2.redhat.com/job/Build_Tower_Vagrant_Box/418/)
  * [x] [Documentation](http://jenkins.ansible.eng.rdu2.redhat.com/job/Build_Tower_Docs/3758/)
