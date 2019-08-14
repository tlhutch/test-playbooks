# Override SCM Branch on JT and related enhacements
## Owner

Primary: Elijah DeLee (@kdelee)
Secondary: Caleb (@squidboylan)
UI: Danny Sami (@dsesami)

## Summary

Allow users to:
 - Create projects that allow their dependent JTs to override the scm branch
 - Create projects that take the scm_refspec (GIT ONLY) argument and pass it to the underlying git module
 - If JT uses a project that allows branch override, allow it to set scm branch (could also be a commit or ref)
 - Also allow scm_branch to be a promptable value

## Related Information

- [SCM Branch override ticket](https://github.com/ansible/awx/issues/282)
- [scm refspec ticket](https://github.com/ansible/awx/issues/4258)
- [AWX PR](https://github.com/ansible/awx/pull/4265)

## Verification Criteria

### API Verification Criteria

- [x] Verify can set `allow_override` on new projects
- [x] Verify can update `allow_override` on existing projects
- [x] Verify can unset `allow_override` on a project that is used only in job templates that do not specify or prompt for branch.
- [x] verify when we have a project that has `allow_override` set to true, we can provide `scm_branch` to job template and it is used on job launch
- [x] Verify we can set `scm_branch` to prompt on launch and then provide on launch and it is used
- [x] Verify that when a JT has a project with `allow_override` and a JT with prompt on launch for `scm_branch`, that we can provide value for `scm_branch` when JT is used on node in workflow job template.
- [x] Verify that when JT has `ask_scm_branch_on_launch` set to `True`, and a WFJT node has provided the value, it is then used in a workflow job
- [x] Verify we CANNOT set `scm_branch` in workflow job template node if it is NOT set as prompt on launch on Job Template
- [x] Verify we can differentiate between a commit hash and a branch name that share the first 6 characters
- [x] Verify we can specify a github PR when we use a project that specifies the `scm_refspec`
- [x] Verify that if the `scm_refspec` is set to a value that would not allow you to checkout a certain ref, that the ref is indeed non-checkout-able.
- [x] Verify that if the `scm_refspec` is set to an invalid value and we have a failed update, then we can correct the value and have a working project with successful updates
- [x] Verify that  Jobs that come from the same JT (and hence share a project), but use two different commits or hashes on launch operate in their own working directory and are not polluted by other job's activities
- [x] Verify that branch-specific galaxy requirements are correctly picked up and installed
- [x] verify when we have a project that has `allow_override` set to False, when we attempt to make a JT with `scm_branch` we get a sensible error message
- [x] Verify that if we attempt to create a non-git based Project with `scm_refspec` it throws a BadRequest exception
- [x] Verify that if we attempt to create a non-git based Project with `scm_refspec` we get a sensible error message
- [x] Verify that git submodules work with this feature, if they previously worked (test added separately)
- [x] Verify that temporary job folders do not contain the full git history of the project
- [x] Verify that if a branch does not contain a playbook a 400 is not raised. This is because we cannot know what playbooks are available beforehand.
- [x] Verify that if a project has `allow_override` set to `False`, when a JT is created specifying a playbook that does not exist we get a 400 response with an explanation.
This is because we do know what playbooks are available when the scm branch is not able to be overriden.



### UI Verification Criteria
- [x] Verify there is a checkbox for allowing branch override on the project form
- [x] verify there is a textbox for taking the scm_refspec on the project
- [x] Verify the tooltip for the scm_refspec textbox with example like `refs/*:refs/remotes/origin/*` mentioning if you want to build PRs with job templates this would be how you would do it
- [x] Verify scm_branch is shown on job details pane, and only when a project that has `allow_override` set.
Verify override branch behavior on JT forms.
- [x] Verify that branches that do not contain the desired playbook show an error and link to the proper project sync job.
- [x] Verify scm_branch is available as prompt on WFJT node form and is applied in WF Vizualizer
- [x] Verify that we can fill in arbitrary playbook name since if it is on non standard branch, Tower won't yet know about it
- [x] Verify that if a branch does not contain a playbook, that an off-list playbook returns an error (and vice versa). This is because we cannot know what playbooks are available beforehand.
- [x] Verify prompting for just a branch, not projects, not playbook
- [x] Schedules/WFJT prompting behavior
- [x] Verify that configure-tower-in-tower setting to enable/disable collections exists in UI and can be used.
- [x] Create a project that does not allow branch override, and make a job template that uses it. Enable the branch override on the project, and ensure that the existing job template then gets the freeform field for arbitrary playbooks, as well as all other necessary additional fields, like scm branch.
