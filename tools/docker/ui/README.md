
## Running with SauceLabs

```shell
export SAUCELABS_USERNAME=shanemcd
export SAUCELABS_API_KEY=ytqOJraG3T29zIwYge0StAksUbmaKg
export PYTEST_ADDOPTS='-m ui -k not test_pagination'

docker-compose -f tools/docker/ui/docker-compose.yml build --no-cache
docker-compose -f tools/docker/ui/docker-compose.yml run pytest_sauce './playbooks/inventory.log' primary MAC chrome
```
