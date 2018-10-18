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
[UI Testcases here](https://docs.google.com/document/d/1zZZwzq3gggQtlmuxoTFFUC8UldPC84AKc2CQB1H-0Zs/edit)
