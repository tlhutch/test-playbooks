
# 3.4 Integration of all new Workflow Features

3.4 introduces the following changes to workflows:

- WFs in WFs
    - Have runtime constraint that WFs can be nested to arbitrary depth BUT cycle detection happens at RUNTIME not template node add time.
    - Variables will not be accepted unless there is a survey or prompt
- WF level inventory
- WF level inventory prompt
- Convergence nodes allowed (multiparent)
- Always nodes allowed in conjunction with success + failure
- Job Templates with slices set > 1 are launched as WFJs:
    - All prompts apply to jobs in the WFJ
    - Each slice becomes a root node (no parents/children) in the WFJ + each have single job associated with them.
    - The child jobs link to their parent WFJ

# Test Plan
Create a test workflow that exercises these new features all together to evidence viablity of shipping all changes together.

This workflow will have the following attributes:
    - [ ] Workflow that has WFs and SJT as nodes
    - [ ] Workflow has WF level inventory set (or prompt on launch)
    - [ ] Create links that make as many nodes as possible
    - [ ] convergence nodes
    - [ ] Each convergence node should Always, Success, Failure relations with parents

The test will make the following assertions:
    - [ ] Each node should link to the spawned WFJ because each is either a SJT or WFJT
    - [ ] Each SJT should then have as many nodes as slices
    - [ ] Each node should then link to a regular job
    - [ ] WFJs from the WFJT nodes should have as many nodes as the test writer put in the WFJT
    - [ ] Each node should link to a job
    - [ ] Inventory SHOULD descend to:
        - [ ] Jobs spawned from WFJ from SJT that have prompt on launch
        - [ ] WFJTs that have prompt on launch
    - [ ] Inventory SHOULD NOT descend to ANY level of:
        - [ ] Anything that does not have Prompt on Launch
        - [ ] Nodes should not start until all “joblets” of parent nodes have completed
    - [ ] Create scenarios where some portions of graph should not run and assert that correct nodes get marked “Do Not Run”
    - [ ] This implies that later nodes should have some parents that are “do not run” as well as viable triggering parents.
    - [ ] Assert that all jobs finish or get marked Do Not Run
    - [ ] Assert that WF job completes
