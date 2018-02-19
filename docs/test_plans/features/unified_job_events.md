# Unified Job Template Websocket Events - Test Plan

### Feature Summary
Tower 3.3.0 brings the pub/sub job event model to all unified job templates, as well as improving general API and UI performance.  This document attempts to overview the automated testing requirements for the verification and final validation of this new feature.

### Related information
* [Feature request - event-based ujt](https://github.com/ansible/awx/issues/200)
* [Pexpect API performance issue](https://github.com/ansible/awx/issues/417)
* [Feature request - strategy support](https://github.com/ansible/awx/issues/288)
* [Event emissions for all ujt - PR](https://github.com/ansible/awx/pull/833)
* [Pexpect performance fix](https://github.com/pexpect/pexpect/pull/464)

### Test case prerequisites
* [ ] Towerkit WS client subscription updates

### Test suites and cases
* [ ] API
    * [ ] Websocket event pub/sub
        * [ ] Project update
        * [ ] Inventory update
        * [ ] System job
    * [ ] Serial directive job event test additions
        * [ ] linear strategy
        * [ ] free strategy
    * [ ] Large inventory update timing test
* [ ] UI (manual testing anticipated)
    * [ ] Eventized job output adoptions
        * [ ] Project update - successful/failed
        * [ ] Inventory update - successful/failed
        * [ ] System job - successful/failed
    * [ ] Performance job event display 
    * [ ] Serial event display - linear/free 
