# Running Tests in Docker

## Examples

## Running your very own py.test command
```shell
$ docker run -v $(pwd):/tower-qa gcr.io/ansible-tower-engineering/tower-qe py.test
```

## Running API tests
```shell
$ ansible-vault decrypt --vault-password-file="${VAULT_FILE}" tools/docker/credentials.yml
$ docker run -v $(pwd):/tower-qa gcr.io/ansible-tower-engineering/tower-qe py.test \
    --api-credentials=tools/docker/credentials.yml \
    --github-cfg=tools/docker/credentials.yml \
    --base-url='https://ec2-01-234-56-789.compute-1.amazonaws.com' \
    --ansible-inventory=playbooks/ec2.ini \
    --ansible-host-pattern=ec2-01-234-56-789.compute-1.amazonaws.com \
    tests/api
```

## Running UI tests

```shell
$ export PYTEST_ADDOPTS="--base-url='https://ec2.tower.com' --ansible-inventory=playbooks/inventory.log --ansible-host-pattern=tower"
$ ansible-vault decrypt --vault-password-file="${VAULT_FILE}" tools/docker/credentials.yml
$ docker-compose -f tools/docker/ui/docker-compose.yml run ui_headless
```

### Debugging

You can watch the tests as they are running:

```shell
$ open vnc://localhost:secret@localhost:5901
```

**Note** If using `docker-machine`, replace `localhost` with the output of `docker-machine ip`
