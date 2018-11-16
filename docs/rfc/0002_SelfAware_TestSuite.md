# Make tower-qa test suite self aware of what it should test based on platform capabilities

## Metadata

  * Author: Yanis Guenane  <yguenane@redhat.com>
  * Tags: CI,tower-qa
  * Status: In Review

## Rationale

Today in our test suite we have many markers that restrict test run based on the platform capabilities.

Example: If we are in a cluster do run this test, if we are not on Openshift do not run this test, etc... .
The issue with this pattern is that the user running the test needs to be aware of those markers and not
forget to specify them when running the test suite.

As of today, we have 6 markers:

  * requires_cluster
  * requires_traditional_cluster
  * requires_openshift_cluster
  * requires_single_instance
  * skip_docker
  * skip_openshift

The idea behind this RFC is to remove all those markers and make `ansible/tower-qa` smart enough to be self-aware
of the platform's capabilities it is running test against.

Simply put, tower-qa should know when to run a test and when to skip it based on the platform it is testing.
This leads to the user running test not having to worry about passing the proper parameters.

This pattern is been used with the FIPS integration. tower-qa will detect if FIPS is enabled on the platform
it is testing[1] and then run test accordingly[2]. Same pattern can beused for existing markers.

## Scope of the change

  * Creating a fixture detecting the specific capability for each of the current marker
  * Updating all the current marked tests with the aforementioned listed markers and have they use the `skip_*` fixture
  * Updating `config/api.cfg`, `config/docker.cfg` and `config/openshift.cfg` to remove the old markers


[1] https://github.com/ansible/tower-qa/blob/0add0438ec828d7dfa5b91f2b7c5021b42e77066/tests/lib/fixtures/utils.py#L152-L160
[2] https://github.com/ansible/tower-qa/blob/0add0438ec828d7dfa5b91f2b7c5021b42e77066/tests/api/settings/test_radius.py#L11
