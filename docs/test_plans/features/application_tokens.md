# Tower Applications and Access Tokens - Test Plan

### Feature Summary
Tower 3.3.0 introduces the notion of authorized applications for delegated API access, and other improvements to Tower authentication - session adoption and authtoken obsolescence.  This document attempts to overview the automated testing requirements for the verification and final validation of this new feature.

### Related information
* [Feature request](https://github.com/ansible/awx/issues/21)
* [Initial PR](https://github.com/ansible/awx/pull/904)
* [Updated awx changes](https://github.com/rooftopcellist/awx/commit/e13469f03ab7933fefa015780b2f9e68f335d0ee) 
* [RFC 6749 - OAuth2](https://tools.ietf.org/html/rfc6749)
* [Docs PR](https://github.com/ansible/product-docs/pull/308)

### Test case prerequisites
* [x] Towerkit REST client session adoption
* [x] Towerkit WS client session adoption
* [x] Towerkit Application objects
* [ ] Towerkit Application schemas
* [x] Towerkit Token objects
* [ ] Towerkit Token schemas

### Test suites and cases
* [ ] API
    * [ ] Application CRUD 
        * [x] Basic Functionality
        * [ ] RBAC
        * [x] Activity Stream
        * [ ] Activity Stream - RBAC
    * [ ] Token CRUD
        * [x] Basic Functionality
        * [ ] RBAC
        * [x] Activity Stream
        * [ ] Activity Stream - RBAC
    * [ ] Token usage
        * [x] OAuth2 functionality - /api/o/...
        * [x] Application Token
        * [x] Personal Access Token
        * [ ] Refreshing Tokens
        * [x] Token revocations
        * [x] Token expiration
        * [ ] Activity Stream for API usage
    * [ ] Token scopes
    * [ ] Session adoption
        * [ ] Sessions basic functionality
            * [ ] API access - implicit in integration testing
            * [ ] WS client
            * [ ] Session expiration
            * [ ] Maximum concurrent sessions
            * [ ] Password changes
        * [x] Basic Auth regression tests
        * [x] Provisioning callbacks
        * [x] authtoken obsolesence
* [ ] UI (manual testing anticipated)
    * [ ] Application CRUD
    * [ ] Token CRUD 
