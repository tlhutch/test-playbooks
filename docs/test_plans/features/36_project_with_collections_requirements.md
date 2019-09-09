# Project with Collections Requirements

## Owners

API: Elyézer (@elyezer), Mat (@one-t)

UI: Danny (@dsesami), Caleb (@squidboylan)

## Summary

Ansible Core 2.9 adds support to pull collections, because of that, if a Job
Template has collections requirements, Ansible Tower should pull these required
collections before running the template.

When running with older versions of Ansible Core (`< 2.9`), the job template
should be run but any collections will be pulled.

## Related Information

- [AWX PR](https://github.com/ansible/awx/pull/4265)
- [Initial API tests](https://github.com/ansible/tower-qa/pull/3641/files#diff-75a733831b759e3f9eb108dcae92a4e3)
- [tower-qa Ticket](https://github.com/ansible/tower-qa/issues/3922)

## Verification Criteria

- [x] API verification
  - [x] Add test that will sync a project with collection requirements on Ansible `< 2.9` and ensure that the project is synced successful but any collection will be pulled.
  - [x] Add test that will sync a project with collection requirements on Ansible `< 2.9` and try to run a playbook that is using the collections feature. The job should fail and provide a meaningful message.
  - [x] Add test that ensures the verification of collections requirements happen when running a Job Template.
  - [x] Add test that ensures the project requirements are downloaded whenever they are specified on the Collections requirements file.
  - [x] Add test that ensures the toggle for processing of collections requirements is working properly. This is a similar toggle as for the roles/requirements.yml.
- [x] UI verification
  - [x] Ensure that the Project sync will pull collection requirements whenever the automatic collection requirements download setting is enabled.
  - [x] Ensure that the toggle for processing of collection requirements is working properly. This is a similar toggle as for the roles/requirements.yml.
