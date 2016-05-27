import json
import sys

import pytest

from common.exceptions import LicenseExceeded_Exception as Forbidden_Exception  # TODO: Fix this
from common.exceptions import NoContent_Exception
from common.utils import random_utf8

pytestmark = [
    pytest.mark.nondestructive,
    pytest.mark.skip_selenium,
    pytest.mark.rbac,
    pytest.mark.usefixtures('authtoken', 'install_enterprise_license')
]

# 405 when attempting to associate a job template role to any user via POST
# request to user/:id/roles
TOWER_ISSUE_1882 = pytest.mark.github(
    'https://github.com/ansible/ansible-tower/issues/1882')
# Updating operational fields in a job template must be done by someone who
# has appropriate access to the resources being used #1981
TOWER_ISSUE_1981 = pytest.mark.github(
    'https://github.com/ansible/ansible-tower/issues/1981')
# Users should be able to copy job templates they have write/execute
# access to
TOWER_ISSUE_1958 = pytest.mark.github(
    'https://github.com/ansible/ansible-tower/issues/1958')


@TOWER_ISSUE_1981
@pytest.mark.parametrize('no_usage', ['project', 'credential', 'inventory'])
def test_usage_role_required_to_change_other_job_template_related_resources(
        factories, auth_user, add_roles, get_role_page, no_usage):
    """Verify that a user cannot change the related project, inventory,
    or credential of a job template unless they have usage permissions
    on all three resources and are admins of the job template
    """
    organization = factories.organization()
    related_data = {
        'project': factories.project(),
        'credential': factories.credential(),
        'inventory': factories.inventory()
    }
    patch_data = {
        'project': factories.project(),
        'credential': factories.credential(),
        'inventory': factories.inventory()
    }
    related_object_ids = {k: v.id for k,v in related_data.items()}
    job_template = factories.job_template(**related_object_ids)
    # make user an org member and a job template admin
    user = factories.user()
    add_roles(user, organization, ['member'])
    add_roles(user, job_template, ['admin'])
    # associate user with the usage role for all related resources except
    # the one this test run has been parametrized to skip
    for obj_name, obj in related_data.iteritems():
        if obj_name != no_usage:
            add_roles(user, obj, ['use'])
    # verify that attempts to patch related resources of the job template
    # as the test user yield a Forbidden Content Error
    for obj_name, obj in patch_data.iteritems():
        add_roles(user, obj, ['use'])
        with auth_user(user):
            with pytest.raises(Forbidden_Exception):
                job_template.patch(**{obj_name: obj.id})
    # grant usage permissions to the user for the restricted resource
    add_roles(user, related_data[no_usage], ['use'])
    # verify that related resources can now be changed
    for obj_name, obj in patch_data.iteritems():
        with auth_user(user):
            job_template.patch(**{obj_name: obj.id})


@TOWER_ISSUE_1958
@TOWER_ISSUE_1981
def test_makers_of_job_templates_are_added_to_admin_role(
        factories, auth_user, add_roles, get_role_page, api_job_templates_pg):
    """Verify that job template creators are added to the admin role of
    the created job template
    """
    user = factories.user()
    organization = factories.organization()
    credential = factories.credential()
    project = factories.project()
    inventory = factories.inventory()
    # make user an org member with use permissions on all items related
    # to the job template to be created
    add_roles(user, organization, ['member'])
    add_roles(user, credential, ['use'])
    add_roles(user, project, ['use'])
    add_roles(user, inventory, ['use'])
    # create a job template as the test user
    with auth_user(user):
        job_template = api_job_templates_pg.post({
            'name': random_utf8(),
            'description': random_utf8(),
            'job_type': 'run',
            'playbook': 'site.yml',
            'project': project.id,
            'inventory': inventory.id,
            'credential': credential.id,
        })
    # check the related users endpoint of the job template's admin
    # role for the test user
    admin_role = get_role_page(job_template, 'admin')
    results = admin_role.get_related('users').get(username=user.username)
    assert results.count == 1, (
        'Could not verify association of job template creator to the '
        'admin role of the created job template')


@pytest.mark.parametrize('association_method', [
    '[user_id->/role/:id/users]',
    '[role_id->/user/:id/roles]'
])
@pytest.mark.parametrize('resource_name', [
    'organization',
    'project',
    'inventory',
    'credential',
    'group',
    TOWER_ISSUE_1882('job_template'),
])
def test_role_association_and_disassociation(
        factories, resource_name, association_method, get_role_pages):
    user = factories.user()
    resource = getattr(factories, resource_name)()
    for role_name, role in get_role_pages(resource):
        if association_method == '[user_id->/role/:id/users]':
            data = {'id': user.id}
            endpoint = role.get_related('users')
        elif association_method == '[role_id->/user/:id/roles]':
            data = {'id': role.id}
            endpoint = user.get_related('roles')
        else:
            raise RuntimeError('Invalid test parametrization')
        with pytest.raises(NoContent_Exception):
            endpoint.post(data)
        # check the related users endpoint of the role for the test user
        results = role.get_related('users').get(username=user.username)
        assert results.count == 1, (
            'Could not verify {0} {1} role association'.format(
                resource_name, role_name))
        # attempt to disassociate the role from the user
        data['disassociate'] = True
        with pytest.raises(NoContent_Exception):
            endpoint.post(data)
        # check the related users endpoint of the role for the absence
        # of test user
        results = role.get_related('users').get(username=user.username)
        assert results.count == 0, (
            'Could not verify {0} {1} role disassociation'.format(
                resource_name, role_name))
