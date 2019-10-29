# Templated Notifications

## Owner

* Primary: Yanis Guenane (@Sprezy)
* Secondary: Mathew Wilson (@one-t)
* UI: John Hill (@unlikelyzero)

## Secondary component (Jinja templating + custom workflow approval notifications)
Owners: Danny (@dsesami) and Elyezer (@elyezer)

## Summary

Users should now be able to define custom messages in a notification template for
started, success and error events.

See https://github.com/ansible/tower/pull/3823 for details about the secondary PR for this feature. 
1. All backend notifications are now Jinja-templated
2. Custom notification messages are now available for workflow approval events.


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
- [ ] Notification regression testing (automated)
- [ ] Ensure custom notification messages for approval events can be created normally.

### UI Verification Criteria
- [x] [Initial Testplan](https://docs.google.com/document/d/1G3fPj7svjJaFMEg1OFksVOmzqIcu5p5HYYk8qqiFusI/edit#heading=h.38pe2ra5qkye)
- [ ] Expanded support PR
