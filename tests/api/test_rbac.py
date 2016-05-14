from contextlib import contextmanager
import os

from Crypto.PublicKey import RSA
import factory
import fauxfactory
import pytest

from common.exceptions import LicenseExceeded_Exception as Forbidden_Exception # TODO: Fix this
from common.exceptions import NoContent_Exception
from common.api.pages import *

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
            obj = cls._get_or_create(model_class, testsetup, **kwargs)
        else:
            obj = model_class(testsetup).post(kwargs)
        request.addfinalizer(obj.silent_delete)
        return obj


def factory_fixture(page_factory, **fixture_defaults):
    @pytest.fixture
    def _factory(request):
        def _model(**kwargs):
            kwargs = dict(fixture_defaults.items() + kwargs.items())
            return page_factory(request=request, **kwargs).get()
        return _model
    return _factory

##############################################################################

class OrgFactory(PageFactory):
    class Meta:
        model = Organizations_Page
        inline_args = ('request',)
        get_or_create = ('name',)

    name = 'Default'
    description = factory.LazyFunction(fauxfactory.gen_utf8)


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
    is_superuser = False
    first_name = factory.LazyFunction(fauxfactory.gen_utf8)
    last_name = factory.LazyFunction(fauxfactory.gen_utf8)
    email = factory.LazyFunction(fauxfactory.gen_email)
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


class InventoryFactory(PageFactory):
    class Meta:
        model = Inventories_Page
        inline_args = ('request',)
        get_or_create = ('name',)
        exclude = ('related_org',)

    related_org = factory.SubFactory(
        OrgFactory, request=factory.SelfAttribute('..request'))

    name = factory.Sequence(lambda n: 'inventory_{}'.format(n))
    description = factory.LazyFunction(fauxfactory.gen_utf8)
    organization = factory.SelfAttribute('related_org.id')


class GroupFactory(PageFactory):
    class Meta:
        model = Groups_Page
        inline_args = ('request',)
        get_or_create = ('name',)
        exclude = ('related_inventory',)

    related_inventory = factory.SubFactory(
        InventoryFactory, request=factory.SelfAttribute('..request'))

    name = factory.Sequence(lambda n: 'group_{}'.format(n))
    description = factory.LazyFunction(fauxfactory.gen_utf8)
    inventory = factory.SelfAttribute('related_inventory.id')


class CredentialFactory(PageFactory):
    class Meta:
        model = Credentials_Page
        inline_args = ('request',)
        get_or_create = ('name',)
        exclude = ('owner',)

    owner = factory.SubFactory(
        UserFactory, request=factory.SelfAttribute('..request'))

    name = factory.Sequence(lambda n: 'credential_{}'.format(n))
    description = factory.LazyFunction(fauxfactory.gen_utf8)
    user = factory.SelfAttribute('owner.id')
    username = factory.SelfAttribute('owner.username')
    kind = 'ssh'

    @factory.LazyAttribute
    def ssh_key_data(self):
        if self.kind == 'ssh':
            return RSA.generate(2048, os.urandom).exportKey('PEM')


# register factory fixtures
org_factory = factory_fixture(OrgFactory)
user_factory = factory_fixture(UserFactory)
project_factory = factory_fixture(ProjectFactory)
credential_factory = factory_fixture(CredentialFactory)
inventory_factory = factory_fixture(InventoryFactory)
group_factory = factory_fixture(GroupFactory)

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
def add_role(request, user_factory):
    def _add_role(model, role_name, user):
        testsetup = request.getfuncargvalue('testsetup')
        if isinstance(user, str):
            user = user_factory(username=user)
        role_name = role_name.lower()
        roles_url = model.get().json.related.roles
        results = Roles_Page(testsetup, base_url=roles_url).get().json.results
        try:
            role = next(r for r in results if r.name.lower() == role_name)
        except StopIteration:
            raise ValueError("Role '{0}' not found for {1}".format(
                role_name, type(model)))
        role_page = Role_Page(testsetup, base_url=role.url)
        with pytest.raises(NoContent_Exception):
            role_page.get().get_related('users').post({'id': user.get().id})
    return _add_role

##############################################################################
@pytest.mark.philly
@pytest.mark.usefixtures('authtoken', 'install_enterprise_license')
def test_blah(api_inventories_pg, inventory, org_factory, inventory_factory, group_factory):
    import pdb; pdb.set_trace()
    inventory_factory()


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
@pytest.mark.parametrize('role', ['admin', 'member'])
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
    n = 11
    assert api_users_pg.get(last_name='mac').count == 0
    assert api_organizations_pg.get(name='philly').count == 0
    for _ in xrange(n):
        user_factory(last_name='mac', related_org__name='philly')
    assert api_users_pg.get(last_name='mac').count == n
    assert api_organizations_pg.get(name='philly').count == 1
