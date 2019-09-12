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

- [ ] Confirm that a notification is sent only when it is enabled
- [ ] Confirm that a notification is not sent when it is disabled
- [ ] Confirm that a notification can be sent through following means:
    - [ ] Email
    - [ ] Grafana
    - [ ] IRC
    - [ ] Mattermost
    - [ ] Pagerduty
    - [ ] Rocketchat
    - [ ] Slack
    - [ ] Twilio
    - [ ] Webhook
- [ ] Confirm that a notification is received by all user(s)/channel(s) specified in the notification template.
- [ ] Confirm that a notification is received when the approval node:
    - [ ] Needs Approval
    - [ ] Is approved
    - [ ] Is denied
    - [ ] Is timed out
- [ ] Confirm that notifications can be set on
    - [ ] Organization level: confirm that notification is sent for all the approval nodes in the organization
    - [ ] Workflow level: confirm that the notification is sent for all the approval nodes in the workflow job template

### RBAC
- [ ] Confirm that a user with permissions can create/ enable notifications
- [ ] Confirm that a user without permissions can not create/ enable notifications

### Edge cases
- [ ] Confirm that the option for enabling approval notifications is not available for any tower resource apart from a workflow and organization eg: normal job, project
