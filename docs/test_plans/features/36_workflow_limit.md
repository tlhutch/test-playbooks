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
    - [x] Test that `ask_limit_on_launch` on a WF can be updated
    - [x] Test that `limit` on a WF can be updated
- scm\_branch Prompt
    - [x] Test that a promptable WF passes the input down to a promptable JT
    - [x] Test that a promptable WF doesn't pass the input down to a non-promptable JT
    - [x] Test that `scm_branch` on a WF passes down to a promptable JT
    - [x] Test that `scm_branch` on a WF doesn't pass down to a non-promptable JT
    - [x] Test that `ask_scm_branch_on_launch` on a WF can be updated
    - [x] Test that `scm_branch` on a WF can be updated

## UI
    - [x] Test that the `scm_branch` field renders correctly. 
    - [x] Test that the `limit` field renders properly.
    - [x] Test that the correct resultant information shows on workflows and job detail pages. 
    - [x] Test that the prompting fields show and persist correctly with different combinations of prompting.
