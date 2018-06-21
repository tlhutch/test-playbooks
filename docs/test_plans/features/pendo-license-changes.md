# Pendo License Changes - Test Plan

### Feature Summary
Tower 3.3.0 introduces a data tracking toggle on first install. This feature testplan captures that new functionality as well as a general regression plan.

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
        * [ ] Basic Functionality
        * [ ] RBAC
        * [ ] Activity Stream
        * [ ] Activity Stream - RBAC
    * [ ] Token CRUD
        * [ ] Basic Functionality
        * [ ] RBAC
        * [ ] Activity Stream
        * [ ] Activity Stream - RBAC
    * [ ] Token usage
        * [ ] OAuth2 functionality - /api/o/...
        * [ ] Application Token
        * [ ] Personal Access Token
        * [ ] Token revocations
        * [ ] Token expiration
        * [ ] Token introspection
        * [ ] Token introspection - RBAC
        * [ ] Activity Stream for API usage
    * [ ] Token scopes
    * [ ] Session adoption
        * [ ] Sessions basic functionality
            * [ ] API access - implicit in integration testing
            * [ ] WS client
            * [ ] Session expiration
            * [ ] Maximum concurrent sessions
            * [ ] Password changes
        * [ ] Basic Auth regression tests
        * [ ] Provisioning callbacks
        * [ ] authtoken obsolesence
* [ ] UI (manual testing anticipated)
    * [ ] Application CRUD
    * [ ] Token CRUD 
