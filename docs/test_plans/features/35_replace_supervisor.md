# Replace Supervisor

## Owner

elyezer

## Summary

Replace supervisor with a different process control system. Part of the work on
this is to find a good replacement for supervisor. This is not defined yet but
some candidates are [Circus](https://circus.readthedocs.io/en/latest/) or systemd.

## Related Information

- [AWX Ticket](https://github.com/ansible/awx/issues/173)

## Verification Criteria

- [ ] The replacement works on the supported OSes.
- [ ] The installation works and no issues are introduced by this change.
- [ ] The upgrade works and no issues are introduced by this change.
- [ ] Check if the sosreport config is updated
