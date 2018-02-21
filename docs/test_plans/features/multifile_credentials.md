# Multifile Credentials - Test Plan

### Feature Summary
Tower 3.3.0 expands on file-sourcing custom credential types by supporting an arbitrary amount of files to a single credential.  This document attempts to overview the automated testing requirements for the verification and final validation of this new feature.

### Related information
* [Feature request](https://github.com/ansible/awx/issues/349)
* [Initial PR](https://github.com/ansible/awx/pull/696)

### Test suites and cases
* [ ] API
    * [ ] Credential type with valid injectors
    * [ ] Credential type with invalid injectors
    * [ ] Custom credential's multiple files are functional
    * [ ] Custom credentials with partial/invalid arguments
    * [ ] No regressions in current credential suites
* [ ] UI (manual testing anticipated)
    * [ ] Same as API 
