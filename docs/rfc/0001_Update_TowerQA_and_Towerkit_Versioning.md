# Update ansible/tower-qa and ansible/towerkit versioning scheme

## Metadata

  * Author: Yanis Guenane  <yguenane@redhat.com>
  * Tags: Jenkins,CI,tower-qa,towerkit
  * Status: Accepted

## Rationale

Currently the product - Tower - and some tooling around the product namely `ansible/tower-qa` and `ansible/towerkit` implements different versioning patterns.

Main branch of tower is `devel` while main branch of the aforementionned tools is `master`.
Release branches of tower is `release_X.Y.Z` while release branches of the aforementionned tools are `release_X.Y`.

This leads to inconsistency in our CI system where, where a specific Tower branch ends up running `master` for `ansible/tower-qa` when it should not.

Concrete example:

If one triggers Nightly_Tower_Patch[1] with a specific `TOWER_PACKAGING_BRANCH`, it will:

  * Call Nightly_Tower with this TOWER/TOWER_PACKAGING branch
  * Call Build_Tower_RPM with the proper branch
  * Call Test_Tower_Install with `TOWERQA_GIT_BRANCH` being `origin/master` - as there is no correlation between the two jobs.

As time of this writing, current development version is `3.4`, and upcoming minor updates are `3.2.8` and `3.3.1`, running Nightly_Tower_Patch for `3.3.1` would test the install and hence the integration with the wrong branch of `ansible/tower-qa`.


## Scope of the change

  * Renaming default branch in both `ansible/tower-qa` and `ansible/towerkit` from `master` to `devel`
  * Ensuring the proper branches for ongoing release exists `release_3.2.8`, `release_3.3.1` and a mechanism is in place for when a new minor version is released
  * Updating every Jenkins jobs that relies on either of those projects and update default value from `origin/master` to `origin/devel`
    * Note: For downstream jobs, ensure it default to `${TOWER_BRANCH}/${TOWER_PACKAGING_BRANCH}` value
  * Cleaning job definition (in the shell build step) where the Branch of `ansible/tower-qa` is "figured" based on TOWER branch
  * Update knowledge base accordingly where it applies
  * Update any automatic process that relies on `origin/master` or `release_X.Y` branch


[1] http://jenkins.ansible.eng.rdu2.redhat.com/view/Tower/job/Nightly_Tower_Patch/configure
