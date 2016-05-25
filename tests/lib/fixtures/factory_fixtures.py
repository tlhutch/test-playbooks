from common.api.page_factory import factory_fixture
from common.factories import (
    OrganizationFactory,
    UserFactory,
    CredentialFactory,
    InventoryFactory,
    GroupFactory,
    HostFactory,
    ProjectFactory,
    JobTemplateFactory,
)

# register factory fixtures
organization_factory = factory_fixture(OrganizationFactory)
user_factory = factory_fixture(UserFactory)
credential_factory = factory_fixture(CredentialFactory)
inventory_factory = factory_fixture(InventoryFactory)
group_factory = factory_fixture(GroupFactory)
host_factory = factory_fixture(HostFactory)
project_factory = factory_fixture(ProjectFactory)
job_template_factory = factory_fixture(JobTemplateFactory)
