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

### Install (@elyezer)

  * [ ] Standalone (automated)
  * [ ] Standalone Bundle (automated)
  * [ ] Traditional Cluster with isolated nodes (automated)
  * [ ] Traditional Cluster Bundle with isolated nodes (automated)
  * [ ] OpenShift Cluster (automated)


### Upgrade (@elyezer)


  * OpenShift 3.4.x to Release: Use this [Pipeline](http://jenkins.ansible.eng.rdu2.redhat.com/job/Pipelines/job/Release%2034%20to%20devel%20-%20OpenShift%20-%20Release%20Verification/) to verify
  * OpenShift 3.5.x to Release: Use this [Pipeline](http://jenkins.ansible.eng.rdu2.redhat.com/job/Pipelines/job/upgrade-release35-openshift-release-verification/) to verify
  * Non-OpenShift 3.4.x to Release: Use this [Pipeline](http://jenkins.ansible.eng.rdu2.redhat.com/job/Pipelines/job/upgrade-release34-release-verification/) to verify
  * Non-OpenShift 3.5.x to Release: Use this [Pipeline](http://jenkins.ansible.eng.rdu2.redhat.com/job/Pipelines/job/upgrade-release35-release-verification/) to verify

  * [ ] RPM install 3.4.{0-3} -> Release
    * [ ] [Bundle/Plain - Standalone/Cluster]
    * [ ] [OpenShift]
  * [ ] RPM install 3.5.{0-3} -> Release
    * [ ] [Bundle/Plain - Standalone/Cluster]
    * [ ] [OpenShift]

### Other

  * [x] Check ansible version check that is [hardcoded in tower-packaging](https://github.com/ansible/tower-packaging/blob/devel/setup/roles/preflight/defaults/main.yml#L6)

### Regression

  * [ ] [UI regression] (automated + manual monday 28th october)
  * [ ] [API regression - Standalone] (automated) @elyezer
  * [ ] [API regression - Traditional Cluster] (automated) @elyezer
  * [ ] [API regression - OpenShift Cluster] (automated) @elyezer
  * [ ] Tower social authentication regression completed (vm)
    * [x] Google OAuth (@elijah + @appuk)
    * [x] GitHub (@elijah + @appuk)
    * [x] GitHub Org (@elijah + @appuk)
    * [x] GitHub Team (@elijah + @appuk)
    * [ ] Azure OAuth (@elyezer + )
    * [x] Radius (@one-t + please recruit one other to teach)
  * [x] Tower SAML integration regression completed (vm) (@one-t + please recruit one other to teach)
  * [ ] Backup/restore successful - standalone (automated) @elyezer
  * [ ] Backup/restore successful - traditional cluster (automated) @elyezer
  * [ ] [Backup/restore successful - OpenShift] (automated) @elyezer
  * [ ] [Deploy tower with HTTPS+Load Balancer+Let's Encrypt + run tests against instance] (@unlikelyzero + @Spredzy)
  * [ ] Deploy tower in OpenShift with an external DB + run tests against instance (@elijah + @calebb)


### Artifacts

Use this [Pipeline](http://jenkins.ansible.eng.rdu2.redhat.com/job/Pipelines/job/build-artifacts-pipeline/) to verify

  * [ ] [AMI]
  * [ ] [Vagrant image]
  * [ ] [Documentation]
