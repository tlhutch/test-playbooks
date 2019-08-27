import functools
import os

from awxkit import config
import pytest


def _run_install_tower_modules_collection(ansible_adhoc):
    result = ansible_adhoc.shell('echo $HOME')
    user_home_dir = result.values()[0]['stdout_lines'][0]
    collection_install_path = os.path.join(user_home_dir, 'collections', 'ansible_collections', 'chrismeyersfsu', 'tower_modules')
    ansible_adhoc.shell('curl -L -o /tmp/collection.tar.gz https://galaxy.ansible.com/download/chrismeyersfsu-tower_modules-0.0.1.tar.gz')
    ansible_adhoc.shell('mkdir -p {}'.format(collection_install_path))
    ansible_adhoc.shell('tar -xf /tmp/collection.tar.gz -C {}'.format(collection_install_path))


def _run_uninstall_tower_modules_collection(ansible_adhoc):
    result = ansible_adhoc.shell('echo $HOME')
    user_home_dir = result.values()[0]['stdout_lines'][0]
    collection_install_path = os.path.join(user_home_dir, 'collections', 'ansible_collections', 'chrismeyersfsu', 'ansible_content_example')
    ansible_adhoc.shell('rm -rf {}'.format(collection_install_path))


@pytest.fixture(scope='class')
def tower_modules_collection(request, is_docker, session_ansible_adhoc):
    '''
    Emulate ansible 2.9 ansible-galaxy collection install. This fixture exists
    because the aforementioned command doesn't yet exist. Thus, our emulation.
    '''
    # On cluster deployments target the `cluster_installer` group which is the
    # group that contains the host that the API calls will be made during
    # testing. This is important, specially for the manual project test,
    # because it needs that a local directory is present on the host's
    # filesystem that is receiving the API call. On the other hand, for
    # standalone deployments the target group should be `tower`
    try:
        ansible_adhoc = session_ansible_adhoc()['cluster_installer']
    except KeyError:
        ansible_adhoc = session_ansible_adhoc()['tower']

    if not config.prevent_teardown:
        uninstall_tower_modules_collection = functools.partial(
            _run_uninstall_tower_modules_collection, ansible_adhoc)
        request.addfinalizer(uninstall_tower_modules_collection)

    try:
        _run_install_tower_modules_collection(ansible_adhoc)
    except AssertionError as e:
        pytest.fail(
            'Failed to install chrismeyersfsu.ansible_content_example\n{}'.format(e)
        )
