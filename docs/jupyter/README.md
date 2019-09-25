# Introduction to awxkit (with Jupyter)

## What is Jupyter?

[Jupyter](http://jupyter.org/):

* .. runs locally as a server
* .. providing a web console where you can edit notebooks
* .. which contain both Python (or other languages) and markdown

Jupyter, in short, provides interactive notebooks where you can run code that is embedded in text.

## How do I set up my environment to use the Jupyter notebooks here?

1. Create / activate a virtual environment
1. `pip install git+ssh://git@github.com/ansible/awx.git#egg=awxkit&subdirectory=awxkit`
1. `pip install jupyter`

Finally, make sure you have a copy of the awxkit notebooks:
`git clone git@github.com:ansible/tower-qa.git`


## Referencing a running AWX instance

In order to use the Jupyter notebooks, you will need to have a running AWX instance. Once you have deployed an instance, add the following to your shell's rc file:

` export AWXKIT_BASE_URL="https://towerurl"`

*Note: Make sure that the url uses `https` instead of `http`. (AWX redirects http to https and awxkit currently doesn't follow the redirection. It will instead tell you that authentication failed).*

Reload your shell's rc file (e.g. `source ~/.bashrc`) so the new environment variable takes effect.

## Loading tower-qa credentials (optional)

The [tower-qa](https://github.com/ansible/tower-qa) repo comes with an encrypted credentials file - `credentials.vault` - that includes the QE team's default credentials for authenticating with AWX, as well as live credentials that can be sourced when creating some AWX resources. Configuring awxkit to use the credentials file is optional, but you may find that you are unable to create some AWX resources (particularly cloud credentials and notifications) without making the credentials file available.

Use the following steps to get the tower-qa credentials file and make it available to awxkit.

1. Ensure that ansible is available
    1. If ansible is not installed on your system, you can add it to your virtual environment with `pip install ansible`
1. `git clone git@github.com:ansible/tower-qa.git`
1. `cd tower-qa/config`
1. `ansible-vault decrypt credentials.vault --output=credentials.yml`
1. In your shell's rc file (e.g. `~/.bashrc`) add:
    1. `export AWXKIT_CREDENTIAL_FILE="/path/to/tower-qa/config/credentials.yml"`
2. Reload your shell's rc file

## Authenticating with AWX

* If you have the tower-qa credentials.yml file in place, then the AWX QE team's default AWX credentials will be used to authenticate with the AWX server.
* If you do not have the credentials file in place, you will need to set the AWX username and password in your shell's rc file (making sure to source the file afterwards so the environment variables take effect):
    * export AWXKIT_USER="my_user"
    * export AWXKIT_USER_PASSWORD="my_password"

## How do I start the Jupyter server?

1. `cd` to awxkit checkout, then `cd` to the jupyter sub-directory
    1. Note: it's important to set this as your current working directory before starting Jupyter because Jupyter's server will use the current working directory as the root folder
1. Run `jupyter notebook`
    1. If running inside a Vagrant vm, use: `jupyter notebook --port <open port> --no-browser --ip=0.0.0.0`
    2. You will also need to make sure that Vagrant is [forwarding](https://www.vagrantup.com/docs/networking/forwarded_ports.html) the open port
1. After Jupiter starts up, it should print a URL that you can follow to access Jupyter
1. The opening page of Jupyter should show the list of awxkit notebooks
1. By default, jupyter notebooks are configured to talk to https://127.0.0.1:8043, if you want use a different awx/tower server, invoke jupyter in an environment with `AWXKIT_BASE_URL` set to your desired host
