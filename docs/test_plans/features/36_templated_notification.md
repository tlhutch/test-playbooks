# Templated Notifications

## Owner

* Primary: Yanis Guenane (@Sprezy)
* Secondary: Mathew Wilson (@one-t)
* UI: John Hill (@unlikelyzero)


## Summary

Users should now be able to define custom messages in a notification template for
started, success and error events.


## Related Information

- [AWX Ticket](https://github.com/ansible/awx/issues/79)
- [AWX PR](https://github.com/ansible/awx/pull/4291)


## Verification Criteria

### API Verification Criteria

- [ ] By default, messages sent match `DEFAULT_MSG = "{{ job_friendly_name }} #{{ job.id }} '{{ job.name }}' {{ job.status }}: {{ url }}"`
- [ ] One should be able to update those messages altogether or separately
- [ ] Actual updated messages are sent as notifications
- [ ] API should provide a defensive mechanism around invalid payload (invalid event, not message or body, ...)
- [ ] Renderer is exercicsed to validate various input strings
- [ ] On upgrade already existing notification templates contains the new `messages` content

