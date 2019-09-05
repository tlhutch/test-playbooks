import functools
import os
import stat

from awxkit import config
import pytest


# https://github.com/ansible/ansible/blob/faaa669764faba8f2a1b4292afc3bc494e4a1932/lib/ansible/config/base.yml#L221
COLLECTIONS_SHARE_FOLDER = '/usr/share/ansible/collections'


def _run_uninstall_tower_modules_collection(ansible_adhoc):
    collection_install_path = os.path.join(COLLECTIONS_SHARE_FOLDER, 'ansible_collections', 'chrismeyersfsu')
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
        contacted = ansible_adhoc.shell(
            'ansible-galaxy collection install chrismeyersfsu.tower_modules -p {}'.format(
                COLLECTIONS_SHARE_FOLDER
            )
        )
        for result in contacted.values():
            assert result.get('rc', None) == 0, result
        contacted = ansible_adhoc.file(
            dest=COLLECTIONS_SHARE_FOLDER,
            mode=stat.S_IRUSR | stat.S_IXUSR | stat.S_IWUSR | stat.S_IRGRP | stat.S_IXGRP | stat.S_IROTH | stat.S_IXOTH,
            recurse=True
        )
        for result in contacted.values():
            assert result.get('mode', None) == '0755', result
    except AssertionError as e:
        pytest.fail(
            'Failed to install chrismeyersfsu.ansible_content_example\n{}'.format(e)
        )
