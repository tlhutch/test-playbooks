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

- [x] Verify can associate with organization and in a sliced JT with more slices than the namespace has resources to launch pods:
    - [ ] launch job
    - [ ] check following for for each slice
      - [ ] pod is spun up in namespace specified
      - [ ] job is run + expected result reported
      - [ ] results are reported
      - [ ] the "overcommitted" slices wait and then are launched later (don't fail with trace back as is currently expected due to capacity short-circuit)

- [ ] Verify can associate with organization (as only instance group) and:
    - [x] launch adhoc command against inventory in org
    - [x] pod is spun up in namespace specified for adhoc job
    - [x] job is run + expected result reported
    - [x] adhoc results are reported
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
- [ ] Verify that when we exceed resource limits on kubernetes cluster we get sensible error message, job fails with ERROR state.

- [ ] Verify that we can cancel a job and pod is cleaned up
- [ ] Verify there is a cleanup job to clean up hanged pods
      - [ ] @one-t has observed that adhoc job pods don't get cleaned up. This is a high priority bug. This could harm a cluster by over-consuming resources
      - [ ] @elijahd has observed some other flaky instances of pods hanging out forever after the job has been cancelled. We may not be able to squash every cause of a hanging pod.
      - [ ] Given that the pod name being `job-123` may not be sufficient to correlate between awx jobs and pods in the cluster, we may need some addtional metadata like a label
            - example: multiple things are pointed at this namespace and creating pods, don't want to clean up pods that are not ours
            - This is a downside of defaulting to the `default` namespace, maybe should put something in the docs about requiring exclusivity of access to namespace for best UX (hacky?)
      - [ ] Observed weakness of pod spec override implementation: will make upgrades difficult if default pod_spec changes but user has mostly custom pod_specs
            - Seeing as most any manifest can be applied to any namespace, with the namespace specified seperately, this would help because likely most people will only need to override the namespace
- [ ] Verify that pods are cleaned up after jobs run -- doing this in teardown of namespace

- [ ] Bad UX/will disrupt normal Tower operations: No pre-flight check for Container Group readiness. @one-t has confirmed that when a Container Group has exceeded capacity, jobs will still be sent to it because of lack of capacity calculation, then they immediately fail and don't get passed onto other instance group.
      - Normally we wait until an instance group that the job has access to has capacity, and then be dispatched to first instance group with capacity.
      - For example, if we added Container Group as a resource available to an organization or just in general with other instance groups, if a job is launched when other instance groups are out of capacity, it will always go to the container group and if it is also over resource limits, job would be sent to Container Group and then fail, instead of waiting for normal instance group to have capacity.

### Container verificaiton criteria

Need to think about how this gets specified and tags for the container.

Are we specifying tag in the packaging?

For this release, we should pin against a version of the container or we might end up in a "world of hurt".

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

## Future RFE's

- [ ] Ability to test connection with cluster from the credential view
- [ ] Static validation of format of CA crt in UI. We had alot of trouble using UI to paste CA crt because of newline stuff
    - note: not sure if we have this for our several other credential types either that allow connection with external services
- [ ] show controller node for the job on the job or on the ContainerGroup if it is always the same. This would be useful if something goes wrong when we are trying to communicate with kubernetes/openshift and something goes wrong on Tower side
