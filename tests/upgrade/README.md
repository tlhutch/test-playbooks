# Data integrity testing
There are a few situations in which we want to test that an action (like upgrade) does not degrade the integrity of
data loaded in tower.

To load data into a tower:

```
py.test -c config/load.cfg --base-url=$TOWER_HOST
```

To validate that a tower loaded with data has expected data and the objects operate as expected (jobs can run, etc),
invoke pytest like this:

```
py.test -c config/verify.cfg --base-url=$TOWER_HOST
```

To update the data file used, see the `config/load.cfg` and `config/verfiy.cfg` files.

# Use cases:

- Backup/Restore
   - Run tests that load data into tower before backup
   - Preform Backup
   - Launch new tower
   - Restore data from backup
   - Run verification tests

- Upgrade
  - Load data into tower with the previous version's data file + load method (pre-3.6.0 this was a script)
  - Upgrade tower to current version
  - Verify with modern verification tests as shown above

Because we want to be able to use the old data and tooling to load old towers, we are currently married to this dataset
or a subset of it.
