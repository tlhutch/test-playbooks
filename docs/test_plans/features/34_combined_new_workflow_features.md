
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
    - [x] Workflow that has WFs and SJT as nodes
    - [x] Workflow has WF level inventory set (or prompt on launch)
    - [x] Create a dense portion of the graph where all possible connections are made (this flexes the logic that decides what the next node to run is)
    - [x] ^ will imply the creation of convergence nodes
    - [x] Use a combination of Always, Success, Failure relations with parents

The test will make the following assertions:
    - [x] Each node should link to the spawned WFJ because each is either a SJT or WFJT
    - [x] Each SJT should then have as many nodes as slices
    - [x] Each node should then link to a regular job
    - [x] WFJs from the WFJT nodes should have as many nodes as the test writer put in the WFJT
    - [x] Each node should link to a job
    - [x] Inventory SHOULD descend to:
        - [x] Jobs spawned from WFJ from SJT that have prompt on launch
        - [x] WFJTs that have prompt on launch
    - [x] Inventory SHOULD NOT descend to ANY level of:
        - [x] Anything that does not have Prompt on Launch
    - [x] Create scenarios where some portions of graph should not run and assert that correct nodes get marked “Do Not Run”
    - [x] This implies that later nodes should have some parents that are “do not run” as well as viable triggering parents.
    - [x] Assert that all jobs finish or get marked Do Not Run
    - [x] Assert that WF job completes
