from contextlib import contextmanager

import factory
import fauxfactory
import pytest

from common.api.pages import *
from common.exceptions import LicenseExceeded_Exception as Forbidden_Exception # TODO: Fix this
from common.exceptions import NoContent_Exception

pytestmark = [pytest.mark.nondestructive, pytest.mark.rbac]


class PageFactoryOptions(factory.base.FactoryOptions):
    """Configuration for PageFactory
    """
    def _build_default_options(self):
        options = super(PageFactoryOptions, self)._build_default_options()
        options.append(factory.base.OptionDefault(
            'get_or_create', (), inherit=True))
        return options


class PageFactory(factory.Factory):
    """Tower API Page Model Base Factory
    """
    _options_class = PageFactoryOptions

    @classmethod
    def _get_or_create(cls, model_class, testsetup, **kwargs):
        """Create an instance of the model through its associated rest api
        endpoint if it doesn't already exist
        """
        model = model_class(testsetup)
        key_fields = {}
        for field in cls._meta.get_or_create:
            if field not in kwargs:
                raise factory.errors.FactoryError(
                    "{0} factory initialization value '{1}' not found".format(
                        cls.__name__, field))
            key_fields[field] = kwargs[field]
        try:
            obj = model.get(**key_fields).results.pop()
        except IndexError:
            obj = model.post(kwargs)
        return obj

    @classmethod
    def _create(cls, model_class, request, **kwargs):
        """Create data and post to the associated endpoint
        """
        testsetup = request.getfuncargvalue('testsetup')
        if cls._meta.get_or_create:
            return cls._get_or_create(model_class, testsetup, **kwargs)
        return model_class(testsetup).post(kwargs)


def factory_fixture(page_factory, **factory_defaults):
    @pytest.fixture
    def _factory(request):
        def _model(**kwargs):
            kwargs = dict(factory_defaults.items() + kwargs.items())
            obj = page_factory(request=request, **kwargs)
            request.addfinalizer(obj.silent_delete)
            return obj
        return _model
    return _factory

##############################################################################

class OrgFactory(PageFactory):
    class Meta:
        model = Organizations_Page
        inline_args = ('request',)
        get_or_create = ('name',)

    name = factory.Sequence(lambda n: 'org_{}'.format(n))
    description = fauxfactory.gen_utf8()


class UserFactory(PageFactory):
    class Meta:
        model = Users_Page
        inline_args = ('request',)
        get_or_create = ('username',)
        exclude = ('related_org',)

    related_org = factory.SubFactory(
        OrgFactory, request=factory.SelfAttribute('..request'))

    username = factory.Sequence(lambda n: 'user_{}'.format(n))
    password = 'fo0m4nchU'
    first_name = fauxfactory.gen_utf8()
    last_name = fauxfactory.gen_utf8()
    email = fauxfactory.gen_email()
    is_superuser = False
    organization = factory.SelfAttribute('related_org.id')


class ProjectFactory(PageFactory):
    class Meta:
        model = Projects_Page
        inline_args = ('request',)
        get_or_create = ('name',)
        exclude = ('related_org',)

    related_org = factory.SubFactory(
        OrgFactory, request=factory.SelfAttribute('..request'))

    name = factory.Sequence(lambda n: 'project_{}'.format(n))
    organization = factory.SelfAttribute('related_org.id')
    scm_type = 'git'

    @factory.LazyAttribute
    def scm_url(self):
        if self.scm_type == 'git':
            return 'https://github.com/jlaska/ansible-playbooks.git'
        elif self.scm_type == 'hg':
            return 'https://bitbucket.org/jlaska/ansible-helloworld'


# register factory fixtures
org_factory = factory_fixture(OrgFactory)
user_factory = factory_fixture(UserFactory)
project_factory = factory_fixture(ProjectFactory)
hg_project_factory = factory_fixture(ProjectFactory, scm_type="hg")

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
def test_factory_fixture_defaults(project_factory, hg_project_factory):
    project = project_factory(related_org__name='Default')
    hg_project = hg_project_factory(related_org__name='Default')
    assert 'github' in project.scm_url
    assert 'bitbucket' in hg_project.scm_url
    # you can override registered factory fixture defaults
    other_hg = hg_project_factory(scm_type='git', related_org__name='Default')
    assert 'github' in other_hg.scm_url


@pytest.mark.usefixtures('authtoken', 'install_enterprise_license')
def test_access_example_01(auth_user, add_role, user_factory, org_factory, project_factory):
    # make some orgs
    red = org_factory(name='red', description='Reliable Excavation & Demolition')
    blu = org_factory(name='blu', description='Builders League United')
    red_project = project_factory(name='red_project', related_org__name='red')
    blu_project = project_factory(name='blu_project', related_org__name='blu')
    # make users and roles
    red_org_admin = user_factory(username='red_org_admin', related_org__name='red')
    add_role(red, 'admin', red_org_admin)
    # check some access
    with auth_user('red_org_admin'):
        # an org admin can run project updates on projects in their org
        assert red_project.get_related('update').can_update
        # but not on projects outside of their org
        with pytest.raises(Forbidden_Exception):
            blu_project.get_related('update').can_update


@pytest.mark.usefixtures('authtoken', 'install_enterprise_license')
@pytest.mark.parametrize('role', ['admin', 'member', 'scm_update'])
def test_access_example_02(auth_user, add_role, project_factory, role):
    # add_role and factories are 'get or create' with respect to resource
    # dependencies. You don't need to bring factory fixtures into your
    # test context unless you need to explicitly interact with the endpoint.
    green_project = project_factory(name='green_project', related_org__name='green')
    other_project = project_factory(name='other_project', related_org__name='green')
    add_role(green_project, 'admin', 'green_project_admin')
    add_role(green_project, role, 'green_project_user')
    with auth_user('green_project_user'):
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


@pytest.mark.usefixtures('authtoken', 'install_enterprise_license')
def test_example_03(api_users_pg, api_organizations_pg, user_factory):
    n = 50
    assert api_users_pg.get(last_name='mac').count == 0
    assert api_organizations_pg.get(name='philly').count == 0
    for _ in range(n):
        user_factory(last_name='mac', related_org__name='philly')
    assert api_users_pg.get(last_name='mac').count == n
    assert api_organizations_pg.get(name='philly').count == 1
