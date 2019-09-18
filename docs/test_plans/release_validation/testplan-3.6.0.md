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

## Features Tested

### Remove Ubuntu support (Yanis/Elijah)

- [x] [Testing complete](https://github.com/ansible/tower-qa/issues/3405)

### Remove /api/v1 (Elijah/Elyezer/Danny)

- [x] [Testing complete](https://github.com/ansible/tower-qa/issues/2935)

### Upgrade Django 2.2 LTS and DJRF (Yanis/Danny)

- [x] Testing complete (Existing regression testing was used for validation)

### Upgrade Node LTS (Yanis/Danny)

- [x] [Testing complete](https://github.com/ansible/tower-qa/issues/3407)

### Container Groups (Mat/Danny)

- [ ] Testing complete #NEEDLINK

### Remove Inventory computed field (Elijah/Elyezer)

- [x] PUNTED

### SSL for PostgreSQL and RabbitMQ (Yanis/Elijah)

- [ ] [Testing complete](https://github.com/ansible/tower-qa/issues/4090)

### Override SCM Branch on JT and related enhancements (Elijah/Caleb)

  - [x] [Testing complete](https://github.com/ansible/tower-qa/blob/devel/docs/test_plans/features/36_branch_on_jt.md)

### Subscription and Enforcement License Changes (Elijah/Caleb)

  - [x] [Testing complete](https://github.com/ansible/tower-qa/blob/devel/docs/test_plans/features/36_license_changes.md)

### Primary Galaxy Server (Danny, Mat, Elyezer, Caleb)

  - [ ] [Testing complete](https://github.com/ansible/tower-qa/blob/devel/docs/test_plans/features/36_primary_galaxy_server.md)

### Project with Collections Requirements (Eleyzer, Mat, Danny, Caleb)

  - [ ] [Testing complete](https://github.com/ansible/tower-qa/blob/devel/docs/test_plans/features/36_project_with_collections_requirements.md)

### Supported CLI shipped with Tower (Elijah, Caleb)

  - [ ] [Testing complete](https://github.com/ansible/tower-qa/blob/devel/docs/test_plans/features/36_supported_cli.md)

### Templated Notifications (Yanis, Mat, John)

  - [ ] [Testing complete](https://github.com/ansible/tower-qa/blob/devel/docs/test_plans/features/36_templated_notification.md)

### Upgrade to PostgresSQL 10 (Yanis, Mat)

  - [ ] [Testing complete](https://github.com/ansible/tower-qa/blob/devel/docs/test_plans/features/36_upgrade_to_postgres10.md)

### Webhook notification enhancement (Yanis, Mat, John)

  - [ ] [Testing complete](https://github.com/ansible/tower-qa/blob/devel/docs/test_plans/features/36_webhook_notification.md)

### Workflow Limit and scm_branch Prompting (Caleb, Danny)

  - [x] [Testing complete](https://github.com/ansible/tower-qa/blob/devel/docs/test_plans/features/36_workflow_limit.md)

### Workflow Approval Nodes (Apurva, Elijah)

  - [x] [Testing complete](https://github.com/ansible/tower-qa/blob/devel/docs/test_plans/features/36_workflow_pause_approve.md)

### Workflow Approval Notifications (Apruva, Elijah)

  - [ ] [Testing complete](https://github.com/ansible/tower-qa/blob/apurva-workflow-approval-notifications/docs/test_plans/features/36_workflow_approval_notifications.md)



## Verifications steps

### Install

  * [ ] Standalone
  * [ ] Standalone Bundle
  * [ ] Traditional Cluster with isolated nodes
  * [ ] Traditional Cluster Bundle with isolated nodes
  * [ ] OpenShift Cluster


### Upgrade


  * OpenShift 3.3.x to Release:
  * OpenShift 3.4.x to Release:
  * OpenShift 3.5.x to Release:
  * Non-OpenShift 3.3.x to Release:
  * Non-OpenShift 3.4.x to Release:
  * Non-OpenShift 3.5.x to Release:

  * [ ] Check ansible version check that is [hardcoded in tower-packaging](https://github.com/ansible/tower-packaging/blob/f8d3d4cd6d1cf35cad6e09de88068440d667ff42/setup/roles/preflight/defaults/main.yml#L6)
  * [ ] 3.2.8 to 3.5.0
    * [ ] Bundle/Plain - Standalone
  * [ ] 3.3.{0-5} -> 3.5.0
    * [ ] [Bundle/Plain - Standalone/Cluster]
    * [ ] [OpenShift]
  * [ ] 3.4.{0-3} -> 3.5.0
    * [ ] [Bundle/Plain - Standalone/Cluster]
    * [ ] [OpenShift]


### Regression

  * [ ] [UI regression]
  * [ ] [API regression - Standalone]
  * [ ] [API regression - Traditional Cluster]
  * [ ] [API regression - OpenShift Cluster]
  * [ ] Tower social authentication regression completed (vm)
    * [ ] Google OAuth
    * [ ] GitHub
    * [ ] GitHub Org
    * [ ] GitHub Team
    * [ ] Azure OAuth
    * [ ] Radius
  * [ ] Tower SAML integration regression completed (vm)
  * [ ] Logging regression completed - cluster
  * [ ] Backup/restore successful - standalone
  * [ ] Backup/restore successful - traditional cluster
  * [ ] [Backup/restore successful - OpenShift]
  * [ ] [Deploy tower with HTTPS+Load Balancer+Let's Encrypt + run tests against instance]
  * [ ] Deploy tower in OpenShift with an external DB + run tests against instance


### Artifacts

Use this pipeline to verify: #FIXME

  * [ ] [AMI]
  * [ ] [Vagrant image]
  * [ ] [Documentation]
