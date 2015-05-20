import os
import json
import pytest
import base64


# TODO - create some base method/class to abstract get/set on tower settings

@pytest.fixture(scope='session')
def tower_config_dir():
    return '/etc/tower'


@pytest.fixture(scope='session')
def tower_confd_dir(tower_config_dir):
    return os.path.join(tower_config_dir, 'conf.d')


@pytest.fixture(scope='session')
def tower_settings_path(request, tower_config_dir):
    return os.path.join(tower_config_dir, 'settings.py')


@pytest.fixture(scope="class")
def AWX_PROOT_ENABLED(request, ansible_runner, tower_settings_path):
    # update settings.py
    contacted = ansible_runner.lineinfile(
        state='present',
        dest=tower_settings_path,
        regexp='^\s*AWX_PROOT_ENABLED\s*=',
        line='AWX_PROOT_ENABLED = True'
    )

    # assert success
    for result in contacted.values():
        assert 'failed' not in result, \
            "Failure while setting AWX_PROOT_ENABLED\n%s" % json.dumps(result, indent=2)
        changed = 'changed' in result and result['changed']

    # if changes were necesary ...
    if changed:

        # restart ansible-tower
        contacted = ansible_runner.service(
            name='ansible-tower',
            state='restarted'
        )

        # assert success
        for result in contacted.values():
            assert 'failed' not in result, \
                "Failure restarting ansible-tower\n%s" % json.dumps(result, indent=2)

    def fin():
        # if changes were necesary ...
        if changed:
            # restore settings.py
            contacted = ansible_runner.lineinfile(
                state='absent',
                dest=tower_settings_path,
                regexp='^\s*AWX_PROOT_ENABLED\s*='
            )
            # assert success
            for result in contacted.values():
                assert 'failed' not in result, \
                    "Failure while removing AWX_PROOT_ENABLED\n%s" % json.dumps(result, indent=2)

        # if changes were necesary ...
        if changed:
            # restart ansible-tower
            contacted = ansible_runner.service(
                name='ansible-tower',
                state='restarted'
            )

            # assert success
            for result in contacted.values():
                assert 'failed' not in result, \
                    "Failure restarting ansible-tower\n%s" % json.dumps(result, indent=2)

    request.addfinalizer(fin)


@pytest.fixture(scope="class")
def ORG_ADMINS_CANNOT_SEE_ALL_USERS(request, ansible_runner, tower_settings_path):
    # update settings.py
    contacted = ansible_runner.lineinfile(
        state='present',
        dest=tower_settings_path,
        regexp='^\s*ORG_ADMINS_CAN_SEE_ALL_USERS\s*=',
        line='ORG_ADMINS_CAN_SEE_ALL_USERS = False'
    )

    # assert success
    for result in contacted.values():
        assert 'failed' not in result, \
            "Failure while setting ORG_ADMINS_CAN_SEE_ALL_USERS\n%s" % json.dumps(result, indent=2)
        changed = 'changed' in result and result['changed']

    # restart ansible-tower (if changes were necesary)
    if changed:
        contacted = ansible_runner.service(
            name='ansible-tower',
            state='restarted'
        )
        for result in contacted.values():
            assert 'failed' not in result, \
                "Failure restarting ansible-tower\n%s" % json.dumps(result, indent=2)

    def fin():
        # restore settings.py (if changes were necesary)
        if changed:
            contacted = ansible_runner.lineinfile(
                state='absent',
                dest=tower_settings_path,
                regexp='^\s*ORG_ADMINS_CAN_SEE_ALL_USERS\s*='
            )
            for result in contacted.values():
                assert 'failed' not in result, \
                    "Failure while removing ORG_ADMINS_CAN_SEE_ALL_USERS\n%s" % json.dumps(result, indent=2)

        # restart ansible-tower (if changes were necesary)
        if changed:
            contacted = ansible_runner.service(
                name='ansible-tower',
                state='restarted'
            )
            for result in contacted.values():
                assert 'failed' not in result, \
                    "Failure restarting ansible-tower\n%s" % json.dumps(result, indent=2)
    request.addfinalizer(fin)


@pytest.fixture(scope="function")
def AD_HOC_COMMANDS(request, ansible_runner, tower_confd_dir):
    '''Function-scoped fixture to add/update /etc/tower/conf.d/ad_hoc.py with AD_HOC_COMMANDS.
    '''
    # define ad_hoc.py config file
    ad_hoc_config_path = os.path.join(tower_confd_dir, 'ad_hoc.py')

    # support ad_hoc_commands override by way of a class variable
    fixture_args = getattr(request.function, 'fixture_args', {})
    if fixture_args:
        commands = fixture_args.kwargs.get('ad_hoc_commands', [])
    else:
        commands = []

    content = '''
AD_HOC_COMMANDS = %s
''' % commands

    # update ad_hoc.py
    contacted = ansible_runner.copy(
        backup=True,
        dest=ad_hoc_config_path,
        owner='awx',
        group='awx',
        mode='0640',
        content=content
    )

    # assert success
    for result in contacted.values():
        assert 'failed' not in result, \
            "Failure while setting AD_HOC_COMMANDS\n%s" % json.dumps(result, indent=2)
        changed = 'changed' in result and result['changed']
        backup_file = 'backup_file' in result and result['backup_file']

    # restart ansible-tower (if changes were necesary)
    if changed:
        contacted = ansible_runner.service(
            name='ansible-tower',
            state='restarted'
        )
        for result in contacted.values():
            assert 'failed' not in result, \
                "Failure restarting ansible-tower\n%s" % json.dumps(result, indent=2)

    def fin():
        # restore ad_hoc.py (if changes were necesary)
        if changed:
            # slurp contents of backup_file
            contacted = ansible_runner.slurp(src=backup_file)
            for result in contacted.values():
                assert 'failed' not in result, \
                    "Failure slurping backup file\n%s" % json.dumps(result, indent=2)

            # restore original ad_hoc.py
            contacted = ansible_runner.copy(
                dest=ad_hoc_config_path,
                owner='awx',
                group='awx',
                mode='0640',
                content=base64.b64decode(contacted.values()[0]['content'])
            )
            for result in contacted.values():
                assert 'failed' not in result, \
                    "Failure restoring backup ad_hoc.py config file\n%s" % json.dumps(result, indent=2)

            # delete the backup file
            contacted = ansible_runner.file(path=backup_file, state='absent')
            for result in contacted.values():
                assert 'failed' not in result, \
                    "Failure removing backgrup ad_hoc.py config file\n%s" % json.dumps(result, indent=2)

        # restart ansible-tower (if changes were necesary)
        if changed:
            contacted = ansible_runner.service(
                name='ansible-tower',
                state='restarted'
            )
            for result in contacted.values():
                assert 'failed' not in result, \
                    "Failure restarting ansible-tower\n%s" % json.dumps(result, indent=2)
    request.addfinalizer(fin)
