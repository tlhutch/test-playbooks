## Tower Integration Tests

In order to run integration tests you'll need a working Tower or AWX install to run tests against. The following steps describe building and configuring the Tower dev containers and running tests against them.

To run tests you'll need an appropriate config file and inventory. tower-qa ships with several useful examples.

```
git clone https://github.com/ansible/tower
git clone https://github.com/ansible/tower-qa
cd tower
# Note: if you want anything other than devel you'll need to checkout the right tower branch as well as setting the compose tag in order to get the right local_settings.py
# Note: you may want to create a separate virtualenv for tower
cp awx/settings/local_settings.py.docker_compose awx/settings/local_settings.py
 
gcloud auth login
gcloud config set project ansible-tower-engineering
export COMPOSE_TAG=devel
export GCLOUD_AUTH=`gcloud auth print-access-token`
export IMAGE_REPOSITORY_AUTH=$GCLOUD_AUTH
gcloud docker -- pull gcr.io/ansible-tower-engineering/awx_devel:devel
make docker-compose
make ui-devel
 
docker exec -it tools_awx_1 bash
 
# Inside the dev container:

awx-manage createsuperuser --noinput --username admin --email admin@example.com
awx-manage update_password --username admin --password XXXX
awx-manage create_preload_data

# For tower rather than awx you need the tower-license installed
. /venv/awx/bin/activate
git clone https://github.com/ansible/tower-license
pip install tower-license/
 
cd ../tower-qa
# Tweak the location of the virtualenv to taste
virtualenv ~/venvs/tower-qa
pip install -r requirements.txt
ansible-vault decrypt config/credentials.vault --output=config/credentials.yml
py.test -c config/docker.cfg --base-url='https://localhost:8043'
```

### Rebuilding Fresh Images

Gcloud caches images locally, plus stopping the main awx container (and even a `make docker-clean`) won't remove your current postgres container. To start fresh images, potentially with a new version of awx/tower, requires you to remove all your existing images and refresh your local cache. The following steps, inside your local tower clone directory, achieve this:

```
make clean
make docker-clean
docker rm $(docker ps -q) -f
gcloud docker -- pull gcr.io/ansible-tower-engineering/awx_devel:devel
```

## Other Helpful Snippets

```bash
# install dependencies
pip install -r requirements.txt

# decrypt credentials
ansible-vault decrypt config/credentials.vault --output=config/credentials.yml

# run api tests
py.test -c config/api.cfg --base-url='https://ec2-tower.com'

# select a subset of tests, with debugger
py.test -c config/api.cfg --base-url='https://ec2-tower.com' -k "test_something" --pdb

# run linter
flake8
```
