# Per-Org Host limits

## Feature Summary

This feature introduces the ability to limit the number of hosts a given org can add to their inventories.
This is helpful in multitenant situations, preventing a given org from using more than their share of the license.

## Related Information

* [Tower Ticket](https://github.com/ansible/tower/issues/1542)

## Acceptance criteria

* [x] API
  * [x] Hosts cannot be added to an inventory if they would bring it out of compliance
  * [x] Max hosts applies across all inventories of an organization 
  * [x] Inventories shared between orgs do not count against the org recieving permission
  * [x] This feature can be disabled
  * [x] This feature can be selectively enabled
  * [x] Limits do not apply to an inventory if it is moved to an org with a higher limit
  * [x] RBAC
    * [x] Only Super Users can change these settings
  * [x] If the limit is set below the current host count for an org, jobs can't launch until rectified
  * [x] If a dynamic inventory update would bring an org out of compliance, the update will fail in a similar way to an update that would bring Tower out of license compliance.
* [ ] [UI Testplan](https://docs.google.com/document/d/1dNBbEAQgHc1P3EtMi079PgLrZM_HFRQ93I_sE4NVHC0/edit)
