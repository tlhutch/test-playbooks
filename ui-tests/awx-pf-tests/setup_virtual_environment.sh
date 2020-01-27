#!/bin/bash

previous_flags=$- # save bash settings to revert afterwards

echo "This script will create a directory named \".pf\""
echo "and use it to set up a Python / Node virtual environment that you can use to"
echo "run tests. If the directory already exists, it will be overwritten."

read -r -p "Are you sure you want to continue? [y/N] " response
if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]

then

  # Create directory
	# Change this directory to whatever you like
  set -eu
	PF_VIRTUALENV_DIR="${HOME}/.pf"
	rm -rf "${PF_VIRTUALENV_DIR}"
	mkdir "${PF_VIRTUALENV_DIR}"

	# Create Python virtual environment
	python3 -m venv "${PF_VIRTUALENV_DIR}"/pf-virtualenv
	source "${PF_VIRTUALENV_DIR}"/pf-virtualenv/bin/activate

	# Install Python dependencies
	git clone https://github.com/ansible/awx.git "${PF_VIRTUALENV_DIR}"/awx
	pip install -e "${PF_VIRTUALENV_DIR}"/awx/awxkit[crypto] -r "${PF_VIRTUALENV_DIR}"/awx/awxkit/requirements.txt

	# Configure Node virtual environment, shared with the Python environment
	pip install nodeenv
	nodeenv -p
	npm install

	echo -e "Configuration of Python/Node virtual environment is complete."
	echo "The environment lives in \"${PF_VIRTUALENV_DIR}\"."
	echo "Run \"source ${PF_VIRTUALENV_DIR}/pf-virtualenv/bin/activate\" to start the virtual environment."
	echo "Run \"deactivate\" to exit the virtual environment."
  echo "Ensure that that CYPRESS_baseUrl, CYPRESS_AWX_E2E_USERNAME,"
  echo "and CYPRESS_AWX_E2E_PASSWORD are set as environment variables before running tests."

  # revert bash settings while keeping the same shell
  if [[ $previous_flags =~ e  ]]
  then set -e
  else set +e
  fi

  if [[ $previous_flags =~ u  ]]
  then set -u
  else set +u
  fi

  return

else
    return
fi
