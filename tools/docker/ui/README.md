## running your very own py.test command using the tower-qe container image:
```shell
docker run -v $(pwd):/tower-qa gcr.io/ansible-tower-engineering/tower-qe py.test
```

## example: running API tests
```shell
ansible-vault decrypt --vault-password-file="${VAULT_FILE}" tools/docker/ui/credentials.yml

docker run -v $(pwd):/tower-qa gcr.io/ansible-tower-engineering/tower-qe py.test \
    --api-credentials=tools/docker/ui/credentials.yml \
    --github-cfg=tools/docker/ui/credentials.yml \
    --base-url='https://ec2-01-234-56-789.compute-1.amazonaws.com' \
    --ansible-inventory=playbooks/ec2.ini \
    --ansible-host-pattern=ec2-01-234-56-789.compute-1.amazonaws.com \
    tests/api
```

## running headless UI tests:

```shell
export PYTEST_ADDOPTS="--base-url='https://ec2.tower.com' --ansible-inventory=playbooks/inventory.log --ansible-host-pattern=tower"
docker-compose -f tools/docker/ui/docker-compose.yml run ui_headless
```
