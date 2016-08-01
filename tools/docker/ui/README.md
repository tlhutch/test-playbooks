## Running with SauceLabs for CI / Automation Servers

```shell
export SAUCELABS_USERNAME=shanemcd
export SAUCELABS_API_KEY=ytqOJraG3T29zIwYge0StAksUbmaKg
export PYTEST_ADDOPTS="--nocapturelog -m ui -k test_activity_stream"

docker-compose -f tools/docker/ui/docker-compose.yml build --no-cache
docker-compose -f tools/docker/ui/docker-compose.yml \
  run pytest_sauce [INVENTORY] [HOST_PATTERN] [PLATFORM] [BROWSER] tests/ui
```


## Running Locally

```shell
docker-compose -f tools/docker/ui/docker-compose.yml \
  run pytest_local [INVENTORY] [HOST_PATTERN] tests/ui
```

## Debugging

```shell
docker-compose -f tools/docker/ui/docker-compose.yml \
  run pytest_local_debug [INVENTORY] [HOST_PATTERN] tests/ui
open vnc://$(docker-machine ip):5900
```
