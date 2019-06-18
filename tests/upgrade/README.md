# Data integity testing

To load data into a tower:

```
py.test -c config/api.cfg --base-url=$TOWER_HOST --resource-file=scripts/resource_loading/data_latest_verification.yml tests/upgrade/test_load_tower.py
```

To validate that a tower loaded with data has expected data and the objects operate as expected (jobs can run, etc),
invoke pytest like this:

```
py.test -c config/api.cfg --base-url=$TOWER_HOST --resource-file=scripts/resource_loading/data_latest_loading.yml tests/upgrade/test_resources_present.py
```

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
