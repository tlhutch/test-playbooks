# Workflow Approval Notifications

## Feature Summary
With this feature enhancement, notifications can be enabled to be sent out whenever an approval node needs approval, is approved, denied or timed out.
Notifications can be enabled at organization level or workflow level as well.

## Related Information
* [PR](https://github.com/ansible/awx/pull/4657)
* [Issue](https://github.com/ansible/tower-qa/issues/4089)
* [Integration tests] ()

## Scenarios to test

### Basic Flow

- [x] Confirm that a notification is sent only when it is enabled
- [x] Confirm that a notification is not sent when it is disabled
- [x] Confirm that a notification can be sent through following means:
    - [x] Slack
    - [x] Webhook
- [x] Confirm that a notification is received by all user(s)/channel(s) specified in the notification template.
- [x] Confirm that a notification is received when the approval node:
    - [x] Needs Approval
    - [x] Is approved
    - [x] Is denied
    - [x] Is timed out
- [x] Confirm that notifications can be set on
    - [x] Organization level: confirm that notification is sent for all the approval nodes in the organization
    - [x] Workflow level: confirm that the notification is sent for all the approval nodes in the workflow job template

### RBAC
- [ ] Confirm that a user with permissions can create/ enable notifications
- [ ] Confirm that a user without permissions can not create/ enable notifications

### Edge cases
- [ ] Confirm that the option for enabling approval notifications is not available for any tower resource apart from a workflow and organization eg: normal job, project
- [ ] Confirm notifications on "any" event