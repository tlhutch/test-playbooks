---
about: 'Template for feature tracking issues'
label: 'type:feature'
name: 'Feature Tracking'
title: '[Tower Version] Title of the feature'
---

<!--
  This template helps creating a feature tracking issue that will make easy
  translating it into a test plan. Use the test plan template to help creating
  the actual test plan
  https://github.com/ansible/tower-qa/blob/devel/docs/test_plans/features/_template.md.

  Assign all the QE owners to the issue so that people can know who is taking
  care of testing the feature.

  Include the issue on the related project. The issue should be at least on the
  tower-qa project related to the current Tower version under development.
-->

## Summary

<!--
  Provide a brief description of the feature, try to describe it in a way that
  will help anyone understand it.
-->

## Related Information

<!--
  Provide a list of related tickets, for example: AWX ticket, Tower ticket,
  tower-qa ticket, related tickets, etc.

  Once the test plan is created, move the verification criteria section from
  the issue to related section on the test plan document.
-->

- [AWX Issue](https://github.com/ansible/awx/issues/<id>)
- [Related PRs on any repo](https://github.com/ansible/awx/pull/<id>)
- [Related meeting recordings](https://bluejeans.com/s/<recording>)
- [Related tower-qa PRs](https://github.com/ansible/tower-qa/pull/<id>)
- [Tower Issue](https://github.com/ansible/tower/issues/<id>)
- [Test Plan](https://github.com/ansible/tower-qa/blob/devel/docs/test_plans/features/<test_plan.md>)

### Blockers

<!-- In case you find any blockers use this section to track them. -->

## Draft Verification Criteria

<!--
  For each of the following sections, include the verification criteria for all
  components such as: API, CLI, UI, Docs, Packaging, etc. Use checkbox items to
  help tracking it and make sure to keep the items up to date. When the
  verification criteria is finalized, make sure to send a PR with the test plan
  document.
-->

### API

- [ ] Ensure the new API endpoint was added
- [ ] Ensure the API endpoint supports the expected HTTP methods

### CLI

- [ ] Ensure CLI supports the new API endpoint added
- [ ] Ensure CLI requires the required fields as information on the command
      that talks to the new API added

### UI

- [ ] Ensure UI provides a page to deal with the new API endpoing added
- [ ] Ensure new UI fields are doing validation

### Docs

- [ ] Ensure the Docs are updated and has the expected information

<!--
### Installer/Packaging

- [ ] Ensure the installer is updated with the expect new procedures
- [ ] Ensure packaging is updated with the new expected packages
-->
