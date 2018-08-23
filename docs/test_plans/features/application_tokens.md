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
    * [x] Application CRUD
        * [x] Basic Functionality
        * [x] RBAC
        * [x] Activity Stream
        * [x] Activity Stream - RBAC
    * [x] Token CRUD
        * [x] Basic Functionality
        * [x] RBAC
        * [x] Activity Stream
        * [x] Activity Stream - RBAC
    * [x] Token usage
        * [x] OAuth2 functionality - /api/o/...
        * [x] Application Token
        * [x] Personal Access Token
        * [x] Refreshing Tokens
        * [x] Token revocations
        * [x] Token expiration
        * [x] Activity Stream for API usage
    * [x] Token scopes
    * [ ] Session adoption
        * [ ] Sessions basic functionality
            * [x] API access - implicit in integration testing
            * [ ] WS client
            * [ ] Session expiration
            * [x] Maximum concurrent sessions
            * [x] Password changes
        * [x] Basic Auth regression tests
        * [x] Provisioning callbacks
        * [x] authtoken obsolesence
* [ ] UI (https://docs.google.com/document/d/1uMSSYQdItLt9GKpq54LtBcbFKXE47qEIyJVTjpiiX_A/edit)
