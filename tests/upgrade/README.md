# Upgrade testing
**CURRENTLY WIP**

To validate that a tower loaded with data has expected data and the objects operate as expected (jobs can run, etc),
invoke pytest like this:

```
py.test -c config/api.cfg --base-url=$TOWER_HOST --resource-file=scripts/resource_loading/data_latest_verification.yml tests/upgrade/test_resources_present.py
```
