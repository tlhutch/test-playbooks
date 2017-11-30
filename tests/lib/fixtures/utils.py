from base64 import b64decode
import os
import logging

import fauxfactory
import pytest


@pytest.fixture
def subrequest(request):
    # https://github.com/pytest-dev/pytest/issues/2495
    # To ensure that teardowns occur roughly in registered order
    # do not use the request fixture directly as all its finalizer calls
    # will occur in same block
    return request


@pytest.fixture(scope='class')
def class_subrequest(request):
    return request


@pytest.fixture
def get_pg_dump(request, ansible_runner, skip_docker):

    def _pg_dump():
        inv_path = os.environ.get('TQA_INVENTORY_FILE_PATH', '/tmp/setup/inventory')
        dump_filename = 'pg_{}.txt'.format(fauxfactory.gen_alphanumeric())
        contacted = ansible_runner.shell("""PGPASSWORD=`grep {} -e "pg_password=.*" """
                                         """| sed \'s/pg_password="//\' | sed \'s/"//\'` """
                                         """pg_dump -U awx -d awx -f {} -w""".format(inv_path, dump_filename))
        for res in contacted.values():
            assert res.get('changed') and not res.get('failed')

        user = ansible_runner.options['user'] \
               or ansible_runner.inventory_manager.get_host(ansible_runner.options['host_pattern']).get_vars()['ansible_user']
        pg_dump_path = '/home/{0}/{1}'.format(user, dump_filename)
        request.addfinalizer(lambda: ansible_runner.file(path=pg_dump_path, state='absent'))

        # Don't log the dumped db.
        pa_logger = logging.getLogger('pytest_ansible')
        prev_level = pa_logger.level
        pa_logger.setLevel('INFO')
        restored = [False]

        def restore_log_level():
            if not restored[0]:
                pa_logger.setLevel(prev_level)
                restored[0] = True

        request.addfinalizer(restore_log_level)

        contacted = ansible_runner.slurp(src=pg_dump_path)
        restore_log_level()

        res = contacted.values().pop()

        assert not res.get('failed') and res['content']
        return b64decode(res['content'])

    return _pg_dump


@pytest.fixture(scope='class')
def is_docker(ansible_module_cls):
    try:
        manager = ansible_module_cls.inventory_manager
        groups_dict = manager.get_group_dict() if hasattr(manager, 'get_group_dict') else manager.get_groups_dict()
        tower_hosts = groups_dict.get('tower')
        return manager.get_host(tower_hosts[0]).get_vars().get('ansible_connection') == 'docker'
    except (TypeError, IndexError):
        return False


docker_skip_msg = "Test doesn't support dev container"


@pytest.fixture(scope='class')
def skip_docker(is_docker):
    if is_docker:
        pytest.skip(docker_skip_msg)


@pytest.fixture(autouse=True)
def _skip_docker(request, is_docker):
    if request.node.get_marker('skip_docker') and is_docker:
        pytest.skip(docker_skip_msg)
