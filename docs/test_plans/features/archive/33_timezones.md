# Time Zone Improvements - Test Plan

### Feature Summary
Tower 3.3.0 corrects and improves upon a number of scheduling and time zone bugs/edge cases, while providing a schedule preview utility endpoint.  This document attempts to overview the automated testing requirements for the verification and final validation of this new feature.

### Related information
* [Feature request](https://github.com/ansible/ansible-tower/issues/823)
* [Initial PR - API](https://github.com/ansible/awx/pull/1024)
* [Recommended time zone presentation](https://pganssle.github.io/pybay-2017-timezones-talk/#/)

### Test case prerequisites
* [.] Towerkit RRule TZID support - Not feasible overall, impractical in general: https://github.com/dateutil/dateutil/issues/637#issuecomment-372845042

### Test suites and cases
* [x] API
    * [x] Existing schedule suite refactor and expansion for all unified job templates
    * [x] Functional TZID RRule support
    * [x] Functional TZID invalid input handling
    * [x] Schedule preview endpoint functionality
    * [x] Schedule preview invalid input handling
* [ ] UI (manual testing anticipated)
    * [ ] Schedule CRUD
    * [ ] Edge case schedule creation
