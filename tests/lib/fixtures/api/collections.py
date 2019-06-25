import functools
import os

from towerkit import config
import pytest


def _run_install_tower_modules_collection(ansible_adhoc, docker=False):
    result = ansible_adhoc()['tower'].shell('echo $HOME')
    user_home_dir = result.values()[0]['stdout_lines'][0]
    collection_install_path = os.path.join(user_home_dir, 'collections', 'ansible_collections', 'chrismeyersfsu', 'tower_modules')
    ansible_adhoc()['tower'].shell('curl -L -o /tmp/collection.tar.gz https://galaxy.ansible.com/download/chrismeyersfsu-tower_modules-0.0.1.tar.gz')
    ansible_adhoc()['tower'].shell('mkdir -p {}'.format(collection_install_path))
    ansible_adhoc()['tower'].shell('tar -xf /tmp/collection.tar.gz -C {}'.format(collection_install_path))


def _run_uninstall_tower_modules_collection(ansible_adhoc, docker=False):
    result = ansible_adhoc()['tower'].shell('echo $HOME')
    user_home_dir = result.values()[0]['stdout_lines'][0]
    collection_install_path = os.path.join(user_home_dir, 'collections', 'ansible_collections', 'chrismeyersfsu', 'ansible_content_example')
    ansible_adhoc()['tower'].shell('rm -rf {}'.format(collection_install_path))


@pytest.fixture(scope='class')
def tower_modules_collection(request, is_docker, session_ansible_adhoc):
    '''
    Emulate ansible 2.9 ansible-galaxy collection install. This fixture exists
    because the aforementioned command doesn't yet exist. Thus, our emulation.
    '''
    if not config.prevent_teardown:
        uninstall_tower_modules_collection_args = [
            session_ansible_adhoc,
            is_docker,
        ]
        uninstall_tower_modules_collection = functools.partial(_run_uninstall_tower_modules_collection, *uninstall_tower_modules_collection_args)
        request.addfinalizer(uninstall_tower_modules_collection)
    try:
        _run_install_tower_modules_collection(session_ansible_adhoc, is_docker)
    except AssertionError as e:
        pytest.fail(
            'Failed to install chrismeyersfsu.ansible_content_example\n{}'.format(e)
            )
