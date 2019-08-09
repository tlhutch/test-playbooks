## Dependencies

You will need:

* `docker`
* `gcloud`
  * (quickstart for linux)[https://cloud.google.com/sdk/docs/quickstart-linux]
* python 3.6 (for devel and future versions)

## Tower Integration Tests

In order to run integration tests you'll need a working Tower or AWX install to
run tests against. The following steps describe building and configuring the
Tower dev containers and running tests against them.

> Note: tower-qa currently works with Python 3.6. Release branches <
> release_3.5.x use Python 2.7, if you are checking out those branches, ensure
> you use the right Python version.

To run tests you'll need an appropriate config file and inventory, tower-qa ships with several useful examples.

```
git clone git@github.com:ansible/tower.git
git clone git@github.com:ansible/tower-qa.git
cd tower
# Note: if you want anything other than devel you'll need to checkout the right tower branch and set the compose tag in order to get the right local_settings.py
cp awx/settings/local_settings.py.docker_compose awx/settings/local_settings.py

gcloud auth login
gcloud config set project ansible-tower-engineering
export COMPOSE_TAG=devel
export GCLOUD_AUTH=`gcloud auth print-access-token`
export IMAGE_REPOSITORY_AUTH=$GCLOUD_AUTH
gcloud auth configure-docker
docker pull gcr.io/ansible-tower-engineering/awx_devel:devel
make docker-compose
make ui-devel
```

Alternatively, you can achieve everything in the second block all at once:
```
cp awx/settings/local_settings.py.docker_compose awx/settings/local_settings.py && gcloud config set project ansible-tower-engineering && make ui-devel && IMAGE_REPOSITORY_AUTH=`gcloud auth print-access-token` make docker-compose COMPOSE_TAG=release_3.3.1
```

### Set up Tower-License module

```
# First create a superuser by running the following command
docker exec -it tools_awx_1 bash -c "awx-manage createsuperuser --noinput --username admin --email admin@example.com; awx-manage update_password --username admin --password XXXX; awx-manage create_preload_data"

# Or access the dev container
docker exec -it tools_awx_1 bash

# And run these commands
awx-manage createsuperuser --noinput --username admin --email admin@example.com
awx-manage update_password --username admin --password XXXX
awx-manage create_preload_data
exit

# Back to your machine terminal, clone license repo (need local ssh keys)
cd tower                      # or 'awx' -- the root directory of your cloned repo
git clone git@github.com:ansible/tower-license.git

# Then install the tower-license module in the awx venv
# It is necessary to provide the user id so you will have permission to write
# to /venv/awx
docker exec --user=0 -it tools_awx_1 bash -c "source /venv/awx/bin/activate; pip install awx_devel/tower-license/"

# Or access the dev container by providing the user id
docker exec --user=0 -it tools_awx_1 bash

# And run below commands
source /venv/awx/bin/activate
pip install awx_devel/tower-license/
exit
```

> Note: when cloning the tower-license repo, you can do so in the container, but will need to use a
[GitHub OAuth key](https://help.github.com/articles/creating-a-personal-access-token-for-the-command-line/)
because your local ssh credentials will not be accessible from inside the container.



### Run Integration Tests

Note: It is reccomended you run Python 3.6.6 if possible to match what is
running on Jenkins.  There are some notable differences between Python 3.6 and
Python 3.7, which is the default python on Fedora 29+. You can install multiple
Python versions on Fedora, see [the
docs](https://developer.fedoraproject.org/tech/languages/python/multiple-pythons.html)
for more information.

```
# navigate to tower-qa on your local file system
exit
cd ../tower-qa

# Tweak the location of the virtualenv to taste
python3.6 -m venv ~/venvs/tower-qa
source ~/venvs/tower-qa/bin/activate
pip install -r requirements.txt
ansible-vault decrypt config/credentials.vault --output=config/credentials.yml    # you will need the vault password
py.test -c config/docker.cfg
```

> Note: if running tests against a production instance, use:
py.test -c config/api.cfg --base-url='https://<tower-host\>'


### Using with local Towerkit

If you intend to make modifications to towerkit as well, you should pip install tkit with the `-e`
so that you changes are picked up automatically.
```
cd ~/
git clone git@github.com:ansible/awx.git
# make sure you are in the tower-qa venv, then install tkit
source ~/venv/tower-qa/bin/activate
pip install -e ~/awx/awxkit/
```

### Rebuilding Fresh Images

Gcloud caches images locally, plus stopping the main awx container (and even a `make docker-clean`) won't remove your current postgres container. To start fresh images, potentially with a new version of awx/tower, requires you to remove all your existing images and refresh your local cache. The following steps, inside your local tower clone directory, achieve this:

```
make clean
make docker-clean
docker rm -f $(docker ps -aq)
docker rmi -f $(docker images -aq)
gcloud docker -- pull gcr.io/ansible-tower-engineering/awx_devel:devel
```

> Note: this will delete _all_ containers and images, not just those related to AWX/Tower.

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

# ignore pytest warnings by adding this flag:
--disable-pytest-warnings

# run linter
flake8

# Setting Environment Variables (add before the invocation of pytest on the same command)
TOWERKIT_PREVENT_TEARDOWN=1  # bypass teardown
```

# Jupyter

There are some example jupyter notebooks of interacting with tower via towerkit/awxkit in docs/jupyter.
