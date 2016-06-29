import pytest

from common.utils import SimpleNamespace

from common.factories import (
    CredentialFactory,
    GroupFactory,
    HostFactory,
    InventoryFactory,
    JobTemplateFactory,
    OrganizationFactory,
    ProjectFactory,
    UserFactory,
    TeamFactory,
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


@pytest.fixture
def factories(request):
    """Inject a map of of all factories into your test context
    """
    return \
        SimpleNamespace(
            credential=FactoryFixture(request, CredentialFactory),
            group=FactoryFixture(request, GroupFactory),
            host=FactoryFixture(request, HostFactory),
            inventory=FactoryFixture(request, InventoryFactory),
            job_template=FactoryFixture(request, JobTemplateFactory),
            organization=FactoryFixture(request, OrganizationFactory),
            project=FactoryFixture(request, ProjectFactory),
            user=FactoryFixture(request, UserFactory),
            team=FactoryFixture(request, TeamFactory)
        )
