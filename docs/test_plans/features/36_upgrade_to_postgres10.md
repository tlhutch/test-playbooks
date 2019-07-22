# Upgrade to PostgreSQL 10

## Owner

Primary: Yanis Guenane (@Sprezy)
Secondary: Mathew Wilson (@one-t)


## Summary

Bump the version of PostgreSQL we are using from 9.6 to 10 to be able to benefit from new features.
This includes `scram-sha-256` hash algorightm for passwords.


## Related Information

- [AWX Ticket](https://github.com/ansible/awx/issues/3778)
- [AWX PR](https://github.com/ansible/awx/pull/4058)
- [tower-packaging PR](https://github.com/ansible/tower-packaging/pull/361)


## Verification Criteria

### Installer Verification Criteria

- [ ] Installation proceeds as expected
  * [ ] RHEL7 non-FIPS
  * [ ] RHEL7 FIPS
  * [ ] RHEL8
  * [ ] OpenShift

- [ ] Upgrade proceeds as expected
  * [ ] RHEL7 non-FIPS
  * [ ] RHEL7 FIPS
  * [ ] RHEL8
  * [ ] OpenShift

In all the scenario above, the following should be verifiedL

* [ ] `pg_hba.conf`, `postgresql.conf` and the actual inner implementation are set for `scram-sha-256`
* [ ] If `pg_hashed_password` is set in the inventory file, the installer should fail via a Preflight Check
* [ ] In an upgrade scenario, password used for 3.5 install in md5 are still valid to log as `scram-sha-356` hashing algorithm is used
* [ ] (optional) Have the installer clean after itself
* [ ] Re-running installer or upgrade twice does not provide weird behavior

### API Verification Criteria

- [ ] Full test suite is passing in a *non-FIPS* environment
- [ ] Full test suite is passing in *FIPS* environment

### UI Verification Criteria

- N/A
