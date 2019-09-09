# Workflow Limit and scm\_branch Prompt

This features allows users to create a Workflow that prompts for limit on
launch and propogates that limit down to job templates that also prompt for
limit on launch. If a workflow prompts for limit on launch and a job tempalte
does not, the entered value on prompt is ignored by the job template.

Owner: Caleb Boylan (squidboylan)

## API

- Limit Prompt
    - [x] Test that a promptable WF passes the input down to a promptable JT
    - [x] Test that a promptable WF doesn't pass the input down to a non-promptable JT
    - [x] Test that `limit` on a WF passes down to a promptable JT
    - [x] Test that `limit` on a WF doesn't pass down to a non-promptable JT
    - [ ] Test that `ask_limit_on_launch` on a WF can be updated
    - [ ] Test that `limit` on a WF can be updated
    - [ ] Test that an empty `limit` on a WF is not used
- scm\_branch Prompt
    - [x] Test that a promptable WF passes the input down to a promptable JT
    - [ ] Test that a promptable WF doesn't pass the input down to a non-promptable JT
    - [x] Test that `scm_branch` on a WF passes down to a promptable JT
    - [ ] Test that `scm_branch` on a WF doesn't pass down to a non-promptable JT
    - [ ] Test that `ask_scm_branch_on_launch` on a WF can be updated
    - [ ] Test that `scm_branch` on a WF can be updated
    - [ ] Test that an empty `scm_branch` on a WF is not used
