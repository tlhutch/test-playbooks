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
    --github-cfg=config/credentials.yml \
    --base-url='https://ec2-01-234-56-789.compute-1.amazonaws.com' \
    --ansible-inventory=playbooks/ec2.ini \
    --ansible-host-pattern=ec2-01-234-56-789.compute-1.amazonaws.com \
    tests/api
```

## Running UI Tests

Ensure the admin user exists with the expected password:

```shell
$ docker exec tools_tower_1 tower-manage createsuperuser --noinput --username admin --email a@b.com
$ docker exec tools_tower_1 tower-manage update_password --username admin --password fo0m4nchU
```

Then run the test service:

```shell
$ ansible-vault decrypt --vault-password-file="${VAULT_FILE}" config/credentials.vault --output=config/credentials.yml
$ docker-compose -f tools/docker/ui/docker-compose.yml run test_tower_ui
```

### Development with towerkit

A local checkout of [towerkit](https://github.com/ansible/towerkit) may be mounted from the host to the `/towerkit` directory inside the container.

### Debugging

You can watch the tests as they are running:

```shell
$ open vnc://localhost:secret@localhost:5901
```

**Note** If using `docker-machine`, replace `localhost` with the output of `docker-machine ip`
