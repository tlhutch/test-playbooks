## Running py.test commands using the tower-qe container image
```shell
docker run -v $(pwd):/tower-qa gcr.io/ansible-tower-engineering/tower-qe py.test
```

## Running headless ui tests
```shell
export PYTEST_ADDOPTS="--base-url='https://ec2.tower.com' --ansible-inventory=playbooks/inventory.log --ansible-host-pattern=tower"
docker-compose -f tools/docker/ui/docker-compose.yml run ui_headless
```
