# Become Plugins

## Owner

elyezer, unlikelyzero

## Summary

Ansible 2.8 will add support to become plugins which allows users to create
custom become plugins. With that said, Ansible Tower should be able to handle
that and then it should support become plugins.

This feature will convert the become choices field into an input field. That
will allow users to enter the name of the become plugin to be used. Since
Ansible ships with some built-in become plugins the UI should present those as
options and also allow free typing.

## Related Information

- [AWX Ticket](https://github.com/ansible/awx/issues/2630)
- [Ansible PR](https://github.com/ansible/ansible/pull/50991)

## Verification Criteria

### API Verification Criteria

- [ ] Check if any Ansible built-in become plugin can be used.
- [ ] Check if inputting an invalid become plugin will make a job to fail.
- [ ] Check if a custom become plugin can be added and used.
- [ ] Check if leaving the become plugin blank will use ``sudo``.

### UI Verification Criteria

- [ ] Check if any Ansible built-in become plugin can be used.
- [ ] Check if inputting an invalid become plugin will make a job to fail.
- [ ] Check if a custom become plugin can be added and used.
- [ ] Check if leaving the become plugin blank will use ``sudo``.
- [ ] Check if the become method is an input field instead of a choice field.
- [ ] Check if when filling the become method the UI would show a list of
    built-in Ansible become plugins.

## Additional Information

The changes on AWX are already merged (see
https://github.com/ansible/awx/pull/3093) but the Ansible core related changes
are still to be merged (see the Ansible PR link on the Related Information
section).
