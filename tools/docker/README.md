# Tower Integration Tests in Docker

## Running API tests
```shell
# decrypt credentials
ansible-vault decrypt config/credentials.vault --output=config/credentials.yml

# remove .pyc files from disk before mounting the project dir into the container
./scripts/clean.sh

# run tests
docker run -v $(pwd):/tower-qa gcr.io/ansible-tower-engineering/tower-qe \
    py.test -c config/api.cfg --base-url='https://ec2-tower.com'
```

## Running UI Tests Against the [Tower Development Environment](https://github.com/ansible/ansible-tower/blob/devel/CONTRIBUTING.md)

```shell
# ensure the admin user exists with the expected password
docker exec tools_tower_1 awx-manage createsuperuser --noinput --username admin --email a@b.com
docker exec tools_tower_1 awx-manage update_password --username admin --password fo0m4nchU

# decrypt credentials
ansible-vault decrypt config/credentials.vault --output=config/credentials.yml

# remove .pyc files from disk before mounting the project dir into the container
./scripts/clean.sh

# run the test services
docker-compose -f tools/docker/ui/docker-compose.yml run test_tower_ui
```

### Development with towerkit

A local checkout of [towerkit](https://github.com/ansible/towerkit) may be mounted from the host to the `/towerkit` directory inside the container. Your changes will be reflected automatically.

### Debugging

You can watch the UI tests as they are running via VNC:

```shell
$ open vnc://localhost:secret@localhost:5901
```

**Note** If using `docker-machine`, replace `localhost` with the output of `docker-machine ip`

