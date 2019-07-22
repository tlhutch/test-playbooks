# Remove license-scoped feature restriction

## Feature Summary

Disabling any feature gating based on basic/enterprise license types.

## Related Information

* [AWX PR](https://github.com/ansible/awx/pull/3581)
* [Tower License PR](https://github.com/ansible/tower-license/pull/5)

## Acceptance criteria

* [ ] API
  * [ ] Ensure previous features limited in basic scope is not limited anymore
  * [ ] Ensure host count still applies for basic scope
  * [ ] Ensure feature available in enterprise scope are still available
