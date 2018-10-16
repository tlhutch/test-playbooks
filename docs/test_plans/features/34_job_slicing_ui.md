##### ISSUE TYPE
 - Test cases

##### COMPONENT NAME
 - UI

##### SUMMARY
UI Test cases for https://github.com/ansible/awx/issues/1283

_When running a job across a large (huge) number of endpoints, an appropriate fork count is issued, and cycling occurs until the job is done. This feature will slice a job into different ansible-playbook executions on a subset of inventory that can be scheduled in parallel. Explicit opt-in is required as trying to analyze playbooks for slicing support is extremely complex._


##### Related issues:
https://github.com/ansible/awx/issues/1283 - Overall issue
https://github.com/ansible/awx/issues/2305 - Creating a sliced JT
https://github.com/ansible/awx/issues/2306 - Editing a sliced JT
https://github.com/ansible/awx/issues/2310 - Launch WF jobs with a sliced JT
https://github.com/ansible/awx/issues/2311 - Cancel part or whole of WF jobs with a sliced JT
https://github.com/ansible/awx/issues/2312 - Relaunch part or whole of WF jobs with a sliced JT
https://github.com/ansible/awx/issues/2314 - Detail view about WF and sliced jobs within sliced JT
https://github.com/ansible/awx/issues/2333 - Ability to search for sliced jobs


## Test Cases
### Sliced Job Template Creation/Editing
- [ ] Ensure sliced JT can be created and that the slice value is saved.
- [ ] Ensure that a slice value of 0 results in an error specifying that a minimum slice of 1 must be defined.
- [ ] Ensure that the field is optional.
### Workflows
- [ ] Ensure sliced JTs can be launched from the JT list
- [ ] Ensure that sliced JTs without prompt fields send the user to the WF job viewer on successful launch.
- [ ] Ensure that sliced JTs with prompts and/or extra variables work the same as normal JTs when it comes to prompting, with all variables and limits being applied to the entire set of slice jobs in the resulting workflow job.
- [ ] Default JT launch and prompt behavior is restored when slice = 1 or set to blank.
- [ ] Ensure sliced jobs can be canceled individually or as an entire workflow job either from the jobs list or WF job details view. 
- [ ] If JT slice is turned off during a job, ensure that expected behavior continues to work and UI remains intact.
- [ ] Ensure sliced jobs can be relaunched...same as above
- [ ] Ensure WF job view is loaded on launch for sliced JTs
- [ ] WF jobs from sliced JTs are marked as slice jobs in job lists
- [ ] Playbook job view is loaded if slice value is set to 1 and job is reverted to non-sliced job.
