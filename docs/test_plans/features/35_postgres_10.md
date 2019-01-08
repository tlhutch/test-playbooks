# PostgreSQL 10

## Feature Summary

Starting from Tower 3.5, Tower will rely on PostgreSQL 10.

## Related Information

  * [AWX Ticket](https://github.com/ansible/awx/issues/374)
  * [9 to 10 Upgrade Notes](https://www.postgresql.org/docs/10/release-10.html#idm46046834255504)


## Test case prequisites

  * Add support for PostgreSQL 10 in `ansible/tower-packaging`


## Acceptance criteria

  * [ ] Documentation update
    * [ ] Mention the upgrade to PostgreSQL 10 in the Doc
    * [ ] Mention that PostgreSQL 10 will be installed in the installer node in parallel of current version and data will be migrated - This requires to have at least the extra database size available on disk
    * [ ] Mention cleaning of previous PG install is on them

  * [ ] Tower Packaging
    * [ ] Fresh install works properly and install PG 10
    * [ ] Upgrade works properly (from `3.2.${latest}`, `3.3.${latest}`, `3.4.${latest}`)

  * [ ] Tower-QA: Test suite must pass

  * [ ] (bonus) `ansible/ansible`: Update `postgresql_user` to accept md5 hashed password and other available hash mechanism
