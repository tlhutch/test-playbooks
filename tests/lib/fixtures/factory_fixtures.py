import pytest

from common.api.page_factory import factory_fixture
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
)


# register factory fixtures
credential_factory = factory_fixture(CredentialFactory)
group_factory = factory_fixture(GroupFactory)
host_factory = factory_fixture(HostFactory)
inventory_factory = factory_fixture(InventoryFactory)
job_template_factory = factory_fixture(JobTemplateFactory)
organization_factory = factory_fixture(OrganizationFactory)
project_factory = factory_fixture(ProjectFactory)
user_factory = factory_fixture(UserFactory)


@pytest.fixture
def factories(
    credential_factory,
    group_factory,
    host_factory,
    inventory_factory,
    job_template_factory,
    organization_factory,
    project_factory,
    user_factory
):
    """Inject a map of of all factories into your test context
    """
    return \
        SimpleNamespace(
            credential=credential_factory,
            group=group_factory,
            host=host_factory,
            inventory=inventory_factory,
            job_template=job_template_factory,
            organization=organization_factory,
            project=project_factory,
            user=user_factory
        )
