# Tower 3.2.8 Release Test Plan

## Overview

* 3.2.8 issues available [here](https://github.com/ansible/tower/issues?q=is%3Aissue+milestone%3Arelease_3.2.8).

## Notes

* Single issue release
* No meaning full `ansible/tower-packaging` changes
* Tower [CHANGELOG](https://github.com/ansible/tower/compare/release_3.2.7...release_3.2.8) from 3.2.7
* Tower-packaging [CHANGELOG](https://github.com/ansible/tower-packaging/compare/release_3.2.7...release_3.2.8) from 3.2.7

Due to the really limited change introduced in this maintenance release only a manual test for the specific issue will be run.

## Resources

* Mat Wilson

## Test

1. [ ] Using `include_vars` with vaulted variables *does not* results in a hung callback
