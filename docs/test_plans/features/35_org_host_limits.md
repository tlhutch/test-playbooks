# Per-Org Host limits

## Feature Summary

This feature introduces the ability to limit the number of hosts a given org can add to their inventories.
This is helpful in multitenant situations, preventing a given org from using more than their share of the license.

## Related Information

* [Tower Ticket](https://github.com/ansible/tower/issues/1542)

## Acceptance criteria

* [ ] API
  * [ ] Inventory updates fail if they would bring an organization out of compliance with the policy
  * [ ] Hosts cannot be added to an inventory if they would bring it out of compliance
  * [ ] Inventories shared between orgs do not count against the org recieving permission
  * [ ] This feature can be disabled
  * [ ] This feature can be selectively enabled
  * [ ] RBAC
    * [ ] Only Super Users can change these settings
  * [ ] If the limit is set below the current host count for an org, ???
