## FIPS Regression Testing

Note migrated from tower-onboarding-docs `getting_started.md`.

Corresponds to migration notes in AWX:

https://github.com/ansible/awx/blob/devel/requirements/README.md

For search purposes, the name of this file is how_to_test_FIPS.md in knowledge base.

To run tests against a FIPS enabled instance of Tower,
go to run a YOLO job and for `AWX_USE_FIPS` select yes.

The full test suite should be ran in this mode every time that Django is upgraded.
This should also be checked against major RHEL versions.
