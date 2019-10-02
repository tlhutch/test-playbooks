from awxkit.utils import PseudoNamespace
from awxkit.api import mixins, pages
import pytest

import logging

log = logging.getLogger(__name__)


def flattened_has_creates(*items):
    flattened = []
    for item in items:
        if isinstance(item, tuple):
            flattened.extend(flattened_has_creates(*item))
        elif isinstance(item, mixins.has_create.HasCreate):
            flattened.append(item)
    return flattened


class HasCreateFactory(object):

    model = None

    _to_teardown = set()

    @classmethod
    def register_teardown(cls, request, to_teardown):
        def teardown_and_clean():
            to_teardown.silent_cleanup()
            cls._to_teardown.remove(to_teardown)
        request.addfinalizer(teardown_and_clean)

    @classmethod
    def __call__(cls, request, *args, **kwargs):
        connection = request.getfixturevalue('current_connection')()

        provided_has_creates = mixins.has_create.all_instantiated_dependencies(*flattened_has_creates(*kwargs.items()))

        has_create = cls.model(connection).create(**kwargs)

        for resource in mixins.has_create.all_instantiated_dependencies(has_create):
            if resource not in provided_has_creates and resource not in cls._to_teardown:
                cls._to_teardown.add(resource)
                cls.register_teardown(request, resource)

        return has_create

    @classmethod
    def payload(cls, request, **kwargs):
        connection = request.getfixturevalue('connection')

        provided_has_creates = mixins.has_create.all_instantiated_dependencies(*flattened_has_creates(*kwargs.items()))

        payload = cls.model(connection).create_payload(**kwargs)

        resources = []
        if isinstance(payload, tuple):
            payload = payload[0]
        for resource_type in payload.ds:
            try:
                resource = payload.ds[resource_type]
            except AttributeError:
                continue
            else:
                resources.append(resource)

        for resource in mixins.has_create.all_instantiated_dependencies(*resources):
            if resource not in provided_has_creates and resource not in cls._to_teardown:
                cls._to_teardown.add(resource)
                cls.register_teardown(request, resource)

        return payload


class OrganizationFactory(HasCreateFactory):
    model = pages.Organization


class InstanceGroupFactory(HasCreateFactory):
    model = pages.InstanceGroup


class UserFactory(HasCreateFactory):
    model = pages.User


class WorkflowJobTemplateFactory(HasCreateFactory):
    model = pages.WorkflowJobTemplate


class CredentialFactory(HasCreateFactory):
    model = pages.Credential


class CredentialTypeFactory(HasCreateFactory):
    model = pages.CredentialType


class InventoryFactory(HasCreateFactory):
    model = pages.Inventory


class InventoryScriptFactory(HasCreateFactory):
    model = pages.InventoryScript


class InventorySourceFactory(HasCreateFactory):
    model = pages.InventorySource


class LabelFactory(HasCreateFactory):
    model = pages.Label


class NotificationTemplateFactory(HasCreateFactory):
    model = pages.NotificationTemplate


class ProjectFactory(HasCreateFactory):
    model = pages.Project


class TeamFactory(HasCreateFactory):
    model = pages.Team


class AdHocCommandFactory(HasCreateFactory):
    model = pages.AdHocCommand


class GroupFactory(HasCreateFactory):
    model = pages.Group


class HostFactory(HasCreateFactory):
    model = pages.Host


class JobTemplateFactory(HasCreateFactory):
    model = pages.JobTemplate


class WorkflowJobTemplateNodeFactory(HasCreateFactory):
    model = pages.WorkflowJobTemplateNode


class ApplicationFactory(HasCreateFactory):
    model = pages.OAuth2Application


class AccessTokenFactory(HasCreateFactory):
    model = pages.OAuth2AccessToken


class FactoryFixture(object):
    """This class is used within the factory fixture definitions below to wrap
    up the request fixture with a factory class so we don't need to explicitly
    bring the request fixture into every test that needs to use a factory.
    """

    def __init__(self, request, has_create_factory):
        self.request = request
        self._has_create_factory = has_create_factory()

    def __call__(self, **kwargs):
        return self._has_create_factory(request=self.request, **kwargs)

    def payload(self, **kwargs):
        return self._has_create_factory.payload(self.request, **kwargs)


def factory_namespace(request):
    return PseudoNamespace(
        access_token=FactoryFixture(request, AccessTokenFactory),
        ad_hoc_command=FactoryFixture(request, AdHocCommandFactory),
        application=FactoryFixture(request, ApplicationFactory),
        credential=FactoryFixture(request, CredentialFactory),
        credential_type=FactoryFixture(request, CredentialTypeFactory),
        group=FactoryFixture(request, GroupFactory),
        host=FactoryFixture(request, HostFactory),
        instance_group=FactoryFixture(request, InstanceGroupFactory),
        inventory=FactoryFixture(request, InventoryFactory),
        inventory_script=FactoryFixture(request, InventoryScriptFactory),
        inventory_source=FactoryFixture(request, InventorySourceFactory),
        job_template=FactoryFixture(request, JobTemplateFactory),
        label=FactoryFixture(request, LabelFactory),
        notification_template=FactoryFixture(request, NotificationTemplateFactory),
        organization=FactoryFixture(request, OrganizationFactory),
        project=FactoryFixture(request, ProjectFactory),
        team=FactoryFixture(request, TeamFactory),
        user=FactoryFixture(request, UserFactory),
        workflow_job_template=FactoryFixture(request, WorkflowJobTemplateFactory),
        workflow_job_template_node=FactoryFixture(request, WorkflowJobTemplateNodeFactory)
    )


@pytest.fixture
def factories(subrequest):
    """Inject a function-scoped factory namespace into your test context"""
    return factory_namespace(subrequest)


@pytest.fixture(scope='class')
def class_factories(class_subrequest):
    """Inject a class-scoped factory namespace into your test context"""
    return factory_namespace(class_subrequest)


@pytest.fixture(scope='session')
def session_factories(session_subrequest):
    """Inject a session-scoped factory namespace into your test context"""
    return factory_namespace(session_subrequest)
