# FIPS II

## Feature Summary

Starting with Tower 3.4, Tower can be installed on FIPS enabled servers.
Part of the 'process' for stating a tools support for FIPS is noting that your tool uses only FIPS-certified encryption.
The cheapest way to do that is to only use OS-provided encryption libraries. We currently bundle some directly.

## Related Information

  * [Tower Ticket](https://github.com/ansible/tower/issues/3094)


## Test case prequisite

  * [ ] Identify all the packages that needs to be installed from the system rather than being bundled. (Currently identified: `pycrypto`, `paramiko`).


## Acceptance criteria

  * [ ] FIPS Fresh Install does work - integration test suite passes
  * [ ] Non-FIPS Fresh Install does work - integration test suite passes
  * [ ] FIPS to FIPS upgrade works - integration test suite passes
  * [ ] Non-FIPS to Non-FIPS upgrade works - integration test suite passes
