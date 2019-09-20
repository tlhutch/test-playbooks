import functools
import os
import stat
import re

from awxkit import config
import pytest


@pytest.fixture(scope='session')
def ansible_collections_path(is_docker):
    """Return the ansible collections path to use depending on the deployment.

    See https://github.com/ansible/ansible/blob/stable-2.9/lib/ansible/config/base.yml#L221.
    """
    if is_docker:
        return '/var/lib/awx/.ansible/collections'
    return '/usr/share/ansible/collections'


def _run_uninstall_tower_modules_collection(ansible_adhoc, collection_path):
    collection_install_path = os.path.join(collection_path, 'ansible_collections', 'chrismeyersfsu')
    ansible_adhoc.shell('rm -rf {}'.format(collection_install_path))


@pytest.fixture(scope='class')
def tower_modules_collection(request, session_ansible_adhoc, ansible_collections_path):
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
            _run_uninstall_tower_modules_collection, ansible_adhoc, ansible_collections_path)
        request.addfinalizer(uninstall_tower_modules_collection)

    try:
        contacted = ansible_adhoc.file(
            dest=ansible_collections_path,
            recurse=True,
            state='directory',
        )
        for result in contacted.values():
            assert result.get('state', None) == 'directory', result

        build_dir = os.path.join(ansible_collections_path, 'build')

        # TODO: get awx/tower fork and branch from YOLameters
        git_result = ansible_adhoc.git(
            repo='https://github.com/AlanCoding/awx.git',
            version='awx_modules_merge',
            depth=1,
            dest=build_dir,
            force=True
        )
        for result in git_result.values():
            assert (result.get('before') or result.get('after')), result

        # TODO: optionally build as awx or tower
        contacted = ansible_adhoc.shell((
            'ansible-playbook -i localhost, awx_collection/template_galaxy.yml '
            '-e package_name=awx -e namespace_name=awx -e package_version=0.0.1'
        ), chdir=build_dir)
        for result in contacted.values():
            assert result.get('rc', None) == 0, result

        contacted = ansible_adhoc.shell(
            'ansible-galaxy collection build --force',
            chdir=os.path.join(build_dir, 'awx_collection')
        )
        for result in contacted.values():
            assert result.get('rc', None) == 0, result
            stdout = result['stdout']
            assert 'Created collection' in stdout
            package_name = re.search(r'\b([a-z0-9\.-]*\.tar\.gz)\b', stdout).group(1)

        contacted = ansible_adhoc.shell(
            'ansible-galaxy collection install {} -p {} --force'.format(
                os.path.join(build_dir, 'awx_collection', package_name), ansible_collections_path
            )
        )
        for result in contacted.values():
            assert result.get('rc', None) == 0, result

        contacted = ansible_adhoc.file(
            dest=ansible_collections_path,
            mode=stat.S_IRUSR | stat.S_IXUSR | stat.S_IWUSR | stat.S_IRGRP | stat.S_IXGRP | stat.S_IROTH | stat.S_IXOTH,
            recurse=True,
            state='directory',
        )
        for result in contacted.values():
            assert result.get('mode', None) == '0755', result
    except AssertionError as e:
        pytest.fail(
            'Failed to install chrismeyersfsu.ansible_content_example\n{}'.format(e)
        )
