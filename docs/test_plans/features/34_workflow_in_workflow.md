# Workflow in Workflow

## Feature Summary

Tower 3.4.0 introduces the ability for one to include worflows within workflows.
Currently workflows support: Job Templates, Project Sync and Inventory Sync.
It should now support Workflow Job Templates (worflow_job).

This document attempts to overview the automated testing requirements for the verification and final validation of this new feature.


## Related Information

  * [Feature Request](https://github.com/ansible/awx/issues/2252)
  * [Initial PR](https://github.com/ansible/awx/pull/2352)
  * [Integration Tests](https://github.com/ansible/tower-qa/pull/2222)


## Test Plan

  * [ ] API
    * [ ] Ensure a Worflow Job Templates can be embedded in another Worflow Job Templates
    * [ ] Ensure recursion at any deep level can be detected and the worflow should fail properly
    * [ ] Ensure proper variable scoping is respected
  * [ ] [UI](https://docs.google.com/document/d/1VaBHxIzvqCH03pD2xkvB-PrP8e96oGeJBFpXdi6Q93Q/edit) 
