import json
import pytest
import common.utils
import common.exceptions
from tests.api import Base_Api_Test


@pytest.fixture(scope="function", params=['admin', 'org_admin'])
def privileged_user(request, admin_user, org_admin):
    if request.param == 'admin':
        return admin_user
    elif request.param == 'org_admin':
        return org_admin
    else:
        raise Exception("Unhandled fixture parameter: %s" % request.param)


@pytest.fixture(scope="function", params=['org_user', 'anonymous'])
def unprivileged_user(request, org_user, anonymous_user):
    if request.param == 'org_user':
        return org_user
    elif request.param == 'anonymous':
        return anonymous_user
    else:
        raise Exception("Unhandled fixture parameter: %s" % request.param)


@pytest.mark.skip_selenium
class Test_Config(Base_Api_Test):
    '''
    Verify the /config endpoint displays the expected information based on the current user
    '''
    pytestmark = pytest.mark.usefixtures('authtoken')

    def test_privileged_user(self, api_config_pg, privileged_user, user_password):
        '''Verify the project_local_paths and project_base_dir fields are present'''
        if privileged_user.username == 'admin':
            user_password = self.credentials['default']['password']

        with self.current_user(privileged_user.username, user_password):
            conf = api_config_pg.get()
            assert 'project_local_paths' in conf.json
            assert 'project_base_dir' in conf.json

    def test_unprivileged_user(self, api_config_pg, unprivileged_user, user_password):
        '''Verify the project_local_paths and project_base_dir fields are absent'''

        with self.current_user(unprivileged_user.username, user_password):
            conf = api_config_pg.get()
            assert 'project_local_paths' not in conf.json
            assert 'project_base_dir' not in conf.json
