import json
import sys

import pytest

from common.api.page_factory import model_fixture
from common.exceptions import LicenseExceeded_Exception as Forbidden_Exception  # TODO: Fix this
from common.tower.license import generate_license

from common.factories import (
    OrganizationFactory,
    ProjectFactory,
    InventoryFactory,
    CredentialFactory,
    JobTemplateFactory
)

pytestmark = [
    pytest.mark.nondestructive,
    pytest.mark.rbac,
    pytest.mark.usefixtures('install_enterprise_license',)
]


@pytest.fixture(scope='module')
def install_enterprise_license(request, authtoken, api_config_pg):
    license_info = generate_license(
        instance_count=sys.maxint,
        days=365,
        license_type='enterprise')
    api_config_pg.post(license_info)
    request.addfinalizer(api_config_pg.delete)

# register some model fixtures just for this module
rbac_organization = model_fixture(
    OrganizationFactory, scope='module', name='rbac_organization')
rbac_project = model_fixture(
    ProjectFactory,
    scope='module',
    name='rbac_project',
    related_organization__name='rbac_organization')
rbac_inventory = model_fixture(
    InventoryFactory,
    scope='module',
    name='rbac_inventory',
    related_organization__name='rbac_organization')
rbac_ssh_credential = model_fixture(
    CredentialFactory,
    scope='module',
    name='rbac_ssh_credential')
rbac_job_template = model_fixture(
    JobTemplateFactory,
    scope='function',
    playbook='ping.yml',
    related_project__name='rbac_project',
    related_inventory__name='rbac_inventory')


@pytest.mark.parametrize(
    'param_role_manager', [
        {
            'rbac_organization': ['member'],
            'rbac_job_template': ['admin', 'execute'],
            'rbac_project': [],
            'rbac_inventory': ['use'],
            'rbac_ssh_credential': ['use'],
        },
        {
            'rbac_organization': ['member'],
            'rbac_job_template': ['admin', 'execute'],
            'rbac_project': ['use'],
            'rbac_inventory': [],
            'rbac_ssh_credential': ['use'],
        },
        {
            'rbac_organization': ['member'],
            'rbac_job_template': ['admin', 'execute'],
            'rbac_project': ['use'],
            'rbac_inventory': ['use'],
            'rbac_ssh_credential': [],
        },
        {
            'rbac_organization': ['member'],
            'rbac_job_template': [],
            'rbac_project': ['use'],
            'rbac_inventory': ['use'],
            'rbac_ssh_credential': ['use'],
        },
    ],
    indirect=True,
    ids=lambda d: json.dumps(d, indent=4)
)
def test_modify_job_template_inventory_without_permission(
    param_role_manager,
    rbac_job_template,
    credential_factory,
    inventory_factory,
    project_factory
):
    """A job template admin cannot change the job template's project
    inventory, or credential unless they have usage permissions on
    all three resources and are admins of the job template
    """
    other_inventory = inventory_factory(
        related_organization__name='rbac_organization')
    other_project = project_factory(
        related_organization__name='rbac_organization')
    other_credential = credential_factory()

    param_role_manager.add_role(other_inventory, 'use')
    param_role_manager.add_role(other_project, 'use')
    param_role_manager.add_role(other_credential, 'use')

    with param_role_manager.auth_user():
        with pytest.raises(Forbidden_Exception):
            rbac_job_template.patch(inventory=other_inventory.id)
        with pytest.raises(Forbidden_Exception):
            rbac_job_template.patch(project=other_project.id)
        with pytest.raises(Forbidden_Exception):
            rbac_job_template.patch(credential=other_credential.id)


@pytest.mark.github(
    'https://github.com/ansible/ansible-tower/issues/1969')
@pytest.mark.parametrize(
    'param_role_manager', [
        {
            'rbac_organization': ['admin'],
            'rbac_project': [],
            'rbac_job_template': [],
        },
    ],
    indirect=True,
    ids=lambda d: json.dumps(d, indent=4)
)
def test_read_orphaned_job_with_permission(param_role_manager, rbac_job_template):
    """If a job template is removed, organization admins should still be able
    to see details of past job runs for that job template.
    """
    orphan = rbac_job_template.launch().wait_until_completed()
    rbac_job_template.delete()
    with param_role_manager.auth_user():
        assert orphan.get()


@pytest.mark.parametrize(
    'param_role_manager', [
        {
            'rbac_organization': ['member'],
            'rbac_job_template': ['admin'],
        },
        {
            'rbac_organization': ['member'],
            'rbac_job_template': ['execute'],
        },
    ],
    indirect=True,
    ids=lambda d: json.dumps(d, indent=4)
)
def test_read_orphaned_job_without_permission(param_role_manager, rbac_job_template):
    """If a job template is removed, users with job template admin and execute
    roles should no longer be able to see details of past job runs for that
    job template.
    """
    orphan = rbac_job_template.launch().wait_until_completed()
    rbac_job_template.delete()
    with param_role_manager.auth_user():
        with pytest.raises(Forbidden_Exception):
            orphan.get()
