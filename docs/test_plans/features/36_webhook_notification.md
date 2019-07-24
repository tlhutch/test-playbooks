# Webhook notification enhancement

## Owner

Primary: Yanis Guenane (@Spredzy)
Secondary: Mathew Wilson (@one-t)
UI: John Hill (@johill)

## Summary

Bring some enhancements to the current webhook notifications. For this cycle, there are two targeted enhancements:

  * Custom HTTP Method (either `POST` or `PUT`)
  * Added support for Basic Auth

## Related Information

- [AWX Ticket](https://github.com/ansible/awx/issues/79)
- [AWX PR](https://github.com/ansible/awx/pull/4124)

## Verification Criteria

### API Verification Criteria

- [x] Should FAIL if any other method than `POST` and `PUT` can is provided for webhook notification template
- [x] Should send a `POST` request if `POST` is selected
- [x] Should send a `PUT` request if `PUT` is selected
- [x] HTTP_METHOD should *not* be removable via `PATCH`/`PUT` action on notification template
- [x] On upgrade all previous webhooks should be present of type `POST` with `username` and `password` set to empty
- [x] Ensure `Authorization: Basic X` is *not* sent if none of `username`/`password` is specified
- [x] Ensure `Authorization: Basic X` is sent if `username` and `password` or `username` only or `password` only is specified


### UI Verification Criteria

- [ ] TBD
