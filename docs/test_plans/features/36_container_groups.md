# Container Groups

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

### Bug tickets:
https://github.com/ansible/awx/issues/4911
https://github.com/ansible/awx/issues/4910
https://github.com/ansible/awx/issues/4909
https://github.com/ansible/awx/issues/4908
https://github.com/ansible/awx/issues/4907
https://github.com/ansible/awx/issues/4848


### API Verification Criteria

- [x] Verify can associate with JT and:
    - [x] launch job
    - [x] pod is spun up in namespace specified
    - [x] job is run + expected result reported
    - [x] results are reported

- [x] Verify can associate with organization and in a WFJT using that org:
    - [x] launch job
	 	- for WFJT confirm:
      - [x] pod is spun up in namespace specified
      - [x] job is run + expected result reported
      - [x] results are reported

- [ ] @one-t Verify can associate with organization and in a sliced JT with more slices than the namespace has resources to launch pods:
    - [x] launch job
    - [x] check following for for each slice
      - [x] pod is spun up in namespace specified
      - [x] job is run + expected result reported
      - [x] results are reported
      - [x] the "overcommitted" slices wait and then are launched later (don't fail with trace back as is currently expected due to capacity short-circuit)

- [x] @one-t Verify that when we exceed resource limits on kubernetes cluster no job is sent to it until it has capacity

- [ ] @one-t Verify can associate with organization (as only instance group) and:
    - [x] launch adhoc command against inventory in org
    - [x] pod is spun up in namespace specified for adhoc job
    - [x] job is run + expected result reported
    - [x] adhoc results are reported
    - [x] project updates run on controller tower node (NOT container group)
          - [ ] @one-t execution node is properly reported as the controller node that handled update
    - [x] inventory updates run on controller tower node (NOT container group)
          - [ ] @one-t execution node is properly reported as the controller node that handled update

- [x] Verify that a bad token for a kubernetes_bearer_token type credential causes job to fail with 401 error displayed to user
- [x] Verify that a bad CA certificate for a kubernetes_bearer_token type credential causes job to fail with an error displayed to user that says something about SSL
- [ ] Verify that a bad image that awx/tower cannot connect to has job fail with state ERROR and a sensible message is displayed in result_traceback
- [ ] Verify that when a container becomes unavailable during the job run that the job fails with state ERROR and a traceback is returned
- [x] @elijahd Verify that we can cancel a job from a jt and pod is cleaned up
- [ ] @elijahd Verify that we can cancel an ad hoc command and pod is cleaned up
- [ ] @elijahd Verify that pods are cleaned up after jobs run -- doing this in teardown of namespace
  - [x] regular job
  - [ ] adhoc

- [ ] @elijahd Verify a job template that has galaxy requirements gets them installed properly and is able to use them

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
- [ ] An adhoc command can be configured to run and canceled on a CG and the pod should be killed @shanemcd what happens in this scenario
- [ ] If the user enters incorrect or invalid credentials, a 401 traceback appears on the job results page.
- [ ] If a user inputs the wrong api endpoint config, then no error is displayed when the job is executed and the job appears to run for an indeterminate amount of time.
Job Results page.

- [ ] Errors from job run should be displayed.
- [ ] Container group should be shown and when clicked, the user is navigated to the container group

### Packaging verification

- [ ] Verify that tower-packaging overrides default image with downstream ansible-runner pinned at a certain tag. We want to make sure that in the future breaking changes to this container won't be automatically pulled into older versions of Tower.

## To resolve before initial merge:

- [ ] Fix bug where we get 500 Internal Server error on request to /api/v2/instance_groups/1. This is reproducible with `tests.api.cluster.test_instance_groups.TestInstanceGroups.test_verify_tower_instance_group_is_a_partially_protected_group`. Appears to be happening with `PUT` to the `tower` instance group
- [ ] `TestCredentialTypes.test_managed_by_tower_credential_types_are_read_only` is failing when trying to check that the kubernetes bearer token credential type is immutable because when doing the `PUT` on the credential type it is first failing because `kubernetes` is not a valid choice for `kind` according to `OPTIONS` on `api/v2/credential_types/`
- [ ] Banner on Container Groups creation form that says "TECH PREVIEW" and directs to docs 

## Bugs to file + resolve during hardening
- [ ] Need a cleanup job/reaper process to clean up hanged pods, we have seen pods hanging out. If we lose connection or have other error before normal cleanup, need to still look back and clean up if job should not be still running. This might be aided by more meta data as mentioned in "optional RFEs".
- [ ] adhoc job pods don't get cleaned up. This is a high priority bug. This could harm a cluster by over-consuming resources
- [ ] Fix bug where execution node is not set on project updates when org only has container group
- [ ] Fix bug where execution node is not set on inventory updates when org only has container group
- [ ] Fix a bug that when job fails because of a bad image that tower cannot connect to, the job fails with ERROR and pod is cleaned up -- currently set to FAILED and pod not cleaned up
- [ ] Fix a bug that when job fails because container disappears mid-job (is killed) that the job fails with ERROR and pod is cleaned up -- currently set to FAILED

## Bugs to file + may not be resolved (though would be good if we did)
- [ ] No pre-flight check for Container Group readiness that could cause disruption of normal Tower operations. @one-t has confirmed that when a Container Group has exceeded capacity, jobs will still be sent to it because of lack of capacity calculation, then they immediately fail and don't get passed onto other instance group. This means in a Tower environment that is saturated with jobs such that all other resources available to a new job are out of capacity, the Container Group will still appear to have capacity even if it itself has also exceeded resource limits. This will cause the job and any future jobs dispatched to the CG to immediately fail until resources are freed up.

## Upgrade concerns

- Observed weakness of pod spec override implementation: will make upgrades difficult if default pod_spec changes but user has mostly custom pod_specs. Seeing as most any manifest can be applied to any namespace, with the namespace specified seperately, this would help because likely most people will only need to override the namespace
- Address similar problems about wanting to pin default image for different releases of Tower to different versions of the default job runner container. If we specify this in this pod spec then when users upgrade, they will not pick up new default if they have made any other changes to the default pod spec.

## Docs concerns

- depending on what happens with pre-flight check for container group capacity, may need to document risks around ResourceQuota impact on jobs failing

## Future RFE's

- [ ] RFE: show controller node for the job on the job or on the ContainerGroup if it is always the same. This would be useful if something goes wrong when we are trying to communicate with kubernetes/openshift and something goes wrong on Tower side. Other, perhaps more pressing reason is we can't be certain all Tower nodes have access to the kubernetes/openshift cluster because of firewall reasons. Users expect the ability to set the controller node because of existing isolated node feature.
- [ ] Ability to test connection with cluster from the credential view
- [ ] Static validation of format of CA crt in UI. We had alot of trouble using UI to paste CA crt because of newline stuff
    - note: not sure if we have this for our several other credential types either that allow connection with external services
- [ ] More metadata on the pod to ease coorelation between pods in cluster and jobs that spawned them in Tower. This will help idenitify problems with zombie pods and also provide cluster administrator ability to cross reference with tower jobs if certain pods are causing problems cluster side (resource consumption, check if job status in tower, etc). Lacking more metadata may make it hard to find correct pod. This is exacerbated by defaulting to the `default` namespace, where pods might be mixed with many others of various origin.
