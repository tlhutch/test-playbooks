# Invalid Items- Test Plan

### Feature Summary
Tower 3.3.0 introduces new invalid item warnings for resources with incomplete dependencies.  This document attempts to overview the automated testing requirements for the verification and final validation of this new feature.

### Related information
* [Feature request](https://github.com/ansible/awx/issues/276)
* [Initial PR - API](https://github.com/ansible/awx/pull/1095)

### Test suites and cases
* [ ] API
    * [ ] Job Templates
        * [ ] Deleted project
        * [ ] Deleted inventory (!ask_inventory_on_launch)
    * [ ] Schedules
        * [ ] Job template's deleted project
        * [ ] Job template's deleted inventory (!ask_inventory_on_launch)
        * [ ] Job template schedule's deleted inventory (ask_inventory_on_launch)
        * [ ] WFJTN's job template's deleted project
        * [ ] WFJTN's job template's deleted inventory (!ask_inventory_on_launch)
* [ ] UI (manual testing anticipated)
    * [ ] Same as API
