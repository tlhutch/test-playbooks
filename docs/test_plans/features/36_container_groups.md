# Feature Title

## Owner

@one-t Mat
@kdelee / @elijahd Elijah
@unlikelyzero John Hill

## Summary

Allow new "instance group" type object that represents a connection to a k8s/openshift cluster where we can spawn pods for running jobs and report back results. Jobs are run using similar mechanism as isolated instance groups.

## Related Information

- [AWX Ticket](https://github.com/ansible/awx/issues/1485)
- [AWX PR](https://github.com/ansible/tower/pulls/4189)
- [tower-qa Ticket](https://github.com/ansible/tower-qa/issues/3443)

### API Verification Criteria

- [ ] Verify can associate with JT and:
    - [x] launch job
    - [x] pod is spun up in namespace specified
    - [x] job is run + expected result reported
    - [ ] results are reported

- [ ] Verify can associate with organization (as only instance group) and:
    - [x] launch adhoc command against inventory in org
    - [x] pod is spun up in namespace specified for adhoc job
    - [x] job is run + expected result reported
    - [ ] adhoc results are reported
    - [x] project updates run on controller tower node (NOT container group)
          - [ ] Fix bug where container group is shown on job + execution node is not set
          - [ ] execution node is properly reported as the controller node that handled update
    - [x] inventory updates run on controller tower node (NOT container group)
          - [ ] Fix bug where container group is shown on job + execution node is not set
          - [ ] execution node is properly reported as the controller node that handled update

- [x] Verify that a bad token for a kubernetes_bearer_token type credential causes job to fail with 401 error displayed to user
- [x] Verify that a bad CA certificate for a kubernetes_bearer_token type credential causes job to fail with an error displayed to user that says something about SSL
- [ ] Verify that a bad image that awx/tower cannot connect to has job fail with state ERROR and a sensible message is displayed in result_traceback
- [ ] Verify that when a container becomes unavailable during the job run that the job fails with state ERROR and a traceback is returned
 


### UI Verification Criteria

#### OpenShift and Kubernetes API Bearer Token Form

 - [x] Create a new credential
 - [x] We can edit an existing credential
 - [x] We can delete the credential
 - [x] We can copy the credential
 - [x] We can create two credentials of the same name @shanemcd is this intended
 - [x] Create a working credential

#### Container Group Form

 - [ ] Fix bug: Name helper tooltip is out of alignment. Name tooltip needs to say ("Name of this container group")
 - [x] Create a Container group with default pod spec
 - [ ] Cannot copy the container group
 - [x] Can delete container group
 - [ ] Fix bug where customize Pod Spec toggle is always enabled
 - [x] Can change pod spec while it's yaml

#### Job Template Form

 - [x] A JT can be configured to run against a container group
 - [ ] On the form, the Instance Groups tooltip should say Instance and Container Group

#### Organization Form

 - [x] An organization can be configured to use a container group
 - [ ] On the form, the Instance Groups tooltip should say Instance and Container Group

#### Inventory Form

 - [x] An inventory can be configured to use a container group in jobs run against hosts in the inventory
 - [ ] On the form, the Instance Groups tooltip should say Instance and Container Group

#### CG Execute

- [ ] A JT can be configured to run on a CG and
- [ ] A SJT can be configured to run on a CG
- [ ] A WFJT can be configured to run on a CG
- [ ] A JT can be configured to run and canceled on a CG and the pod should be killed @shanemcd what happens in this scenario
- [ ] If the user enters incorrect or invalid credentials, a 401 traceback appears on the job results page.
- [ ] If a user inputs the wrong api endpoint config, then no error is displayed when the job is executed and the job appears to run for an indeterminate amount of time.
Job Results page.

- [ ] Errors from job run should be displayed.
- [ ] Container group should be shown and when clicked, the user is navigated to the container group

## Future RFE's

- [ ] Ability to test connection with cluster from the credential view
    - note: not sure if we have this for our several other credential types either that allow connection with external services
- [ ] show controller node for the job on the job or on the ContainerGroup if it is always the same. This would be useful if something goes wrong when we are trying to communicate with kubernetes/openshift and something goes wrong on Tower side
