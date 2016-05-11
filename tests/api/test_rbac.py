from contextlib import contextmanager

import factory
import fauxfactory
import pytest
from pytest_factoryboy import register

from common.api.pages import *
from common.exceptions import LicenseExceeded_Exception as Forbidden_Exception # TODO: Fix this
from common.exceptions import NoContent_Exception

pytestmark = [pytest.mark.nondestructive, pytest.mark.rbac]


class PageFactoryOptions(factory.base.FactoryOptions):

    def _build_default_options(self):
        options = super(PageFactoryOptions, self)._build_default_options()
        options.append(factory.base.OptionDefault(
            'page_get_or_create', (), inherit=True))
        return options


class PageFactory(factory.Factory):
    """Base Factory for Tower API Page Model Objects
    """
    _options_class = PageFactoryOptions

    @classmethod
    def _get_or_create(cls, model_class, *args, **kwargs):
        """Create an instance of the model through its associated
        rest api endpoint if it doesn't already exist
        """
        key_fields = {}
        for field in cls._meta.page_get_or_create:
            if field not in kwargs:
                raise factory.errors.FactoryError(
                    "page_get_or_create - "
                    "Unable to find initialization value for '{0}' "
                    "in factory {1}".format(field, cls.__name__))
            key_fields[field] = kwargs[field]
        try:
            obj = model_class.get(**key_fields).results.pop()
        except IndexError:
            obj = model_class.post(kwargs)
        return obj

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        """Create data and post to the associated endpoint
        """
        if cls._meta.page_get_or_create:
            return cls._get_or_create(model_class, *args, **kwargs)
        return model_class.post(kwargs)


class OrganizationFactory(PageFactory):
    class Meta:
        model = Organizations_Page
        page_get_or_create = ('name',)
    name = factory.Sequence(lambda n: 'org_{}'.format(n))
    description = fauxfactory.gen_utf8()


class UserFactory(PageFactory):
    class Meta:
        model = Users_Page
        page_get_or_create = ('username',)
    username = factory.Sequence(lambda n: 'user_{}'.format(n))
    organization = factory.SubFactory(OrganizationFactory)
    password = 'fo0m4nchU'
    is_superuser = False
    first_name = fauxfactory.gen_utf8()
    last_name = fauxfactory.gen_utf8()
    email = fauxfactory.gen_email()


class ProjectFactory(PageFactory):
    class Meta:
        model = Projects_Page
        page_get_or_create = ('name',)
    name = factory.Sequence(lambda n: 'project_{}'.format(n))
    organization = factory.SubFactory(OrganizationFactory)
    scm_type = 'git'

    @factory.LazyAttribute
    def scm_url(self):
        if self.scm_type == 'git':
            return 'https://github.com/jlaska/ansible-playbooks.git'
        elif self.scm_type == 'hg':
            return 'https://bitbucket.org/jlaska/ansible-helloworld'


register(OrganizationFactory, 'org_factory')
register(UserFactory, 'user_factory')
register(ProjectFactory, 'project_factory')

##############################################################################

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

# This fixture is temporary and represents role lookup + add capabilities
# not yet implemented in the page models. I'll solve this problem last.
@pytest.fixture
def add_role(request, testsetup, user_factory):
    def _add_role(model, role_name, user):
        if isinstance(user, str):
            user = user_factory(username=user)
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
    import pdb; pdb.set_trace()
    # make some orgs
    red = org_factory(name='red', description='Reliable Excavation & Demolition')
    blu = org_factory(name='blu', description='Builders League United')
    red_project = project_factory(name='red_project', organization__name='red')
    blu_project = project_factory(name='blu_project', organization__name='blu')
    # make users and roles
    red_org_admin = user_factory(username='red_org_admin')
    red_org_member = user_factory(username='red_org_member')
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
    # add_role and factories are 'get or create' with respect to resource
    # dependencies. You don't need to bring factory fixtures into your
    # test context unless you need to explicitly interact with the endpoint.
    green_project = project_factory(name='green_project', organization__name='green')
    other_project = project_factory(name='other_project', organization__name='green')
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
