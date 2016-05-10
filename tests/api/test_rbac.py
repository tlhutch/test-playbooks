from contextlib import contextmanager

import fauxfactory
import pytest

from common.api.pages import *
from common.exceptions import LicenseExceeded_Exception as Forbidden_Exception # TODO: Fix this
from common.exceptions import NoContent_Exception

pytestmark = [pytest.mark.nondestructive, pytest.mark.rbac]

@pytest.fixture
def auth_user(testsetup, api_authtoken_url, default_password):
    """Inject a context manager for user authtoken switching on api models
    """
    @contextmanager
    def _auth_user(username, password=default_password):
        try:
            prev_auth = testsetup.api.session.auth
            data = {'username': username, 'password': password}
            response = testsetup.api.post(api_authtoken_url, data)
            testsetup.api.login(token=response.json()['token'])
            yield
        finally:
            testsetup.api.session.auth = prev_auth
    return _auth_user

@pytest.fixture
def user_factory(request, testsetup, default_password, org_factory):
    def _user(name, password=default_password, su=False, org=None):
        users = Users_Page(testsetup)
        try:
            user = users.get(username=name).results[0]
        except IndexError:
            data = {'username': name, 'password': password, 'is_superuser': su}
            if org:
                data['organization'] = org_factory(org).get().id
            user = users.post(data)
        request.addfinalizer(user.silent_delete)
        return user
    return _user

@pytest.fixture
def org_factory(request, testsetup, authtoken):
    def _org(name, description=None):
        orgs = Organizations_Page(testsetup)
        try:
            org = orgs.get(name=name).results[0]
        except IndexError:
            org = orgs.post({'name': name, 'description': description})
        request.addfinalizer(org.silent_delete)
        return org
    return _org

@pytest.fixture
def project_factory(request, testsetup, auth_user, org_factory):
    def _project(name, org=None):
        projects = Projects_Page(testsetup)
        try:
            project = projects.get(name=name).results[0]
        except IndexError:
            data = {}
            data['name'] = name
            data['scm_type'] = 'git'
            data['scm_url'] = 'https://github.com/jlaska/ansible-playbooks.git'
            if org:
                data['organization'] = org_factory(org).get().id
            project = projects.post(data)
        request.addfinalizer(project.silent_delete)
        return project
    return _project

# This fixture is temporary and represents role lookup + add capabilities
# not yet implemented in the page models. I'll solve this problem last.
@pytest.fixture
def add_role(request, testsetup, user_factory):
    def _add_role(model, role_name, user):
        if isinstance(user, str):
            user = user_factory(user)
        if not role_name.endswith('_role'):
            role_name += '_role'
        role_url = model.get().json.summary_fields.roles[role_name].url
        role = Role_Page(testsetup, base_url=role_url)
        with pytest.raises(NoContent_Exception):
            role.get().get_related('users').post({'id': user.get().id})
    return _add_role

##############################################################################

@pytest.mark.usefixtures('authtoken', 'install_enterprise_license')
def test_access_ex1(auth_user, add_role, user_factory, org_factory, project_factory):
    # make some orgs
    red = org_factory('red', description='Reliable Excavation & Demolition')
    blu = org_factory('blu', description='Builders League United')
    red_project = project_factory('red_project', org='red')
    blu_project = project_factory('blu_project', org='blu')
    # make users and roles
    red_org_admin = user_factory('red_org_admin')
    red_org_member = user_factory('red_org_member')
    add_role(red, 'admin', red_org_admin)
    add_role(blu, 'member', red_org_member)
    # check some access
    with auth_user('red_org_admin'):
        # an org admin can run project updates on projects in their org
        assert red_project.get_related('update').can_update
        # but not on projects outside of their org
        with pytest.raises(Forbidden_Exception):
            blu_project.get_related('update').can_update

@pytest.mark.usefixtures('authtoken', 'install_enterprise_license')
def test_access_ex2(auth_user, add_role, project_factory):
    # add_role and factories are 'get or create' with respect to
    # resource dependencies. You don't need to bring factory fixtures
    # into your text context unless you plan on explicitly interacting
    # with their endpoint.
    green_project = project_factory('green_project', org='green')
    other_project = project_factory('other_project', org='green')
    add_role(green_project, 'admin', 'green_project_admin')
    add_role(green_project, 'member','green_project_member')

    with auth_user('green_project_member'):
        # project members can run project updates
        assert green_project.get_related('update').can_update
        # and see who their project admins are
        access_list = green_project.get_related('access_list')
        assert access_list.get(username="green_project_admin")
        # but they can't see projects they aren't members of
        with pytest.raises(Forbidden_Exception):
            other_project.get()
        # nor can they see the organization their project belongs to
        with pytest.raises(Forbidden_Exception):
            green_project.get_related('organization')
