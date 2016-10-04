import pytest

from qe.utils import SimpleNamespace

from qe.factories import (
    CredentialFactory,
    GroupFactory,
    HostFactory,
    InventoryFactory,
    InventoryScriptFactory,
    JobTemplateFactory,
    OrganizationFactory,
    ProjectFactory,
    UserFactory,
    TeamFactory,
    LabelFactory,
    WorkflowJobTemplateNodeFactory,
    WorkflowJobTemplateFactory,
)


class FactoryFixture(object):
    """This class is used within the factory fixture definitions below to wrap
    up the request fixture with a factory class so we don't need to explicitly
    bring the request fixture into every test that needs to use a factory.
    """
    def __init__(self, request, page_factory):
        self.request = request
        self._factory = page_factory

    def __call__(self, **kwargs):
        return self._factory(request=self.request, **kwargs)

    def payload(self, **kwargs):
        return self._factory.payload(request=self.request, **kwargs)


def factory_namespace(request):
    return \
        SimpleNamespace(
            credential=FactoryFixture(request, CredentialFactory),
            group=FactoryFixture(request, GroupFactory),
            host=FactoryFixture(request, HostFactory),
            inventory=FactoryFixture(request, InventoryFactory),
            inventory_script=FactoryFixture(request, InventoryScriptFactory),
            job_template=FactoryFixture(request, JobTemplateFactory),
            organization=FactoryFixture(request, OrganizationFactory),
            project=FactoryFixture(request, ProjectFactory),
            user=FactoryFixture(request, UserFactory),
            team=FactoryFixture(request, TeamFactory),
            label=FactoryFixture(request, LabelFactory),
            workflow_job_template_node=FactoryFixture(request, WorkflowJobTemplateNodeFactory),
            workflow_job_template=FactoryFixture(request, WorkflowJobTemplateFactory),
        )


@pytest.fixture
def factories(request):
    """Inject a function-scoped factory namespace into your test context
    """
    return factory_namespace(request)


@pytest.fixture(scope='module')
def module_factories(module_install_enterprise_license, request):
    """Inject a module-scoped factory namespace into your test context
    """
    return factory_namespace(request)
