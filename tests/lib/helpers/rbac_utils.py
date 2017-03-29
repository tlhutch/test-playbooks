import logging
import httplib
import os

import towerkit.exceptions
from towerkit.api.pages.users import User_Page
from towerkit.api.pages.teams import Team_Page
from towerkit.yaml_file import load_file
import pytest


log = logging.getLogger(__name__)


# load expected values for summary_fields user_capabilities
user_capabilities = load_file(os.path.join(os.path.dirname(__file__), 'user_capabilities.yml'))


# -----------------------------------------------------------------------------
# RBAC Utilities
# -----------------------------------------------------------------------------

def get_role(model, role_name):
    """Lookup and return a return a role page model by its role name.
    :param model: A resource api page model with related roles endpoint
    :role_name: The name of the role (case insensitive)
    Usage::
        >>> # get the description of the Use role for an inventory
        >>> bar_inventory = factories.inventory()
        >>> role_page = get_role(bar_inventory, 'Use')
        >>> role_page.description
        u'Can use the inventory in a job template'
    """
    search_name = role_name.lower()
    for role in model.object_roles:
        if role.name.lower() == search_name:
            return role
    msg = "Role '{0}' not found for {1}".format(role_name, type(model))
    raise ValueError(msg)


def set_roles(agent, model, role_names, endpoint='related_users', disassociate=False):
    """Associate a list of roles to a user/team for a given api page model
    :param agent: The api page model for a user/team
    :param model: A resource api page model with related roles endpoint
    :param role_names: A case insensitive list of role names
    :param endpoint: The endpoint to use when making the role association.
        - 'related_users': use the related users endpoint of the role
        - 'related_roles': use the related roles endpoint of the user
    :param disassociate: A boolean indicating whether to associate or
        disassociate the role with the user
    Usage::
        >>> # create a user that is an organization admin with use and
        >>> # update roles on a test inventory
        >>> foo_organization = factories.organization(name='foo')
        >>> bar_inventory = factories.inventory(name='bar')
        >>> test_user = factories.user()
        >>> set_roles(test_user, foo_organization, ['admin'])
        >>> set_roles(test_user, bar_inventory, ['use', 'update'])
    """
    object_roles = [get_role(model, name) for name in role_names]
    for role in object_roles:
        if endpoint == 'related_users':
            payload = {'id': agent.id}
            if isinstance(agent, User_Page):
                endpoint_model = role.get_related('users')
            elif isinstance(agent, Team_Page):
                endpoint_model = role.get_related('teams')
            else:
                raise ValueError("Unhandled type for agent - %s." % endpoint_model)
        elif endpoint == 'related_roles':
            payload = {'id': role.id}
            endpoint_model = agent.get_related('roles')
        else:
            raise RuntimeError('Invalid role association endpoint')
        if disassociate:
            payload['disassociate'] = disassociate
        with pytest.raises(towerkit.exceptions.NoContent):
            endpoint_model.post(payload)


# -----------------------------------------------------------------------------
# Integrated Assertion Helpers
# -----------------------------------------------------------------------------

def check_role_association(user, model, role_name):
    # check the related users endpoint of the role for user
    role = get_role(model, role_name)
    results = role.get_related('users').get(username=user.username)
    if results.count != 1:
        msg = 'Unable to verify {0} {1} role association'
        pytest.fail(msg.format(type(model), role_name))


def check_role_disassociation(user, model, role_name):
    # check the related users endpoint of the role for absence of user
    role = get_role(model, role_name)
    results = role.get_related('users').get(username=user.username)
    if results.count != 0:
        msg = 'Unable to verify {0} {1} role disassociation'
        pytest.fail(msg.format(type(model), role_name))


def check_request(model, method, code, data=None):
    """Make an HTTP request and check the response payload against the provided
    http response code
    """
    method = method.lower()
    api = model.api
    url = model.base_url.format(**model.json)

    if method in ('get', 'head', 'options', 'delete'):
        if data:
            log.warning('Unused {0} request data provided'.format(method))
        response = getattr(api, method)(url)
    else:
        response = getattr(api, method)(url, data)
    if response.status_code != code:
        msg = 'Unexpected {0} request response code: {1} != {2}'
        pytest.fail(msg.format(method, response.status_code, code))


def assert_response_raised(tower_object, response=httplib.OK, methods=('put', 'patch', 'delete')):
    """Check PUT, PATCH, and DELETE against a Tower resource."""
    exc_dict = {
        httplib.OK: None,
        httplib.NOT_FOUND: towerkit.exceptions.NotFound,
        httplib.FORBIDDEN: towerkit.exceptions.Forbidden,
    }
    exc = exc_dict[response]
    for method in methods:
        if exc is None:
            getattr(tower_object, method)()
        else:
            with pytest.raises(exc):
                getattr(tower_object, method)()


def check_read_access(tower_object, expected_forbidden=[], unprivileged=False):
    """Check GET against a Tower resource."""
    # for test scenarios involving unprivileged users
    if unprivileged:
        with pytest.raises(towerkit.exceptions.Forbidden):
            tower_object.get()
    # for test scenarios involving privileged users
    else:
        tower_object.get()
        for related in tower_object.related:
            if related in expected_forbidden:
                with pytest.raises(towerkit.exceptions.Forbidden):
                    tower_object.get_related(related)
            else:
                tower_object.get_related(related)


# -----------------------------------------------------------------------------
# Helper functions
# -----------------------------------------------------------------------------

def get_resource_roles(resource):
    """Helper function that returns a list containing a Tower resource's role names."""
    return [role.replace("_role", "").replace("adhoc", "ad hoc") for role in resource.summary_fields.object_roles.keys()]


def get_nt_endpoints(notifiable_resource):
    """Helper function that returns the notification template endpoints of a
    notifiable Tower resource.
    """
    nt_any_pg = notifiable_resource.get_related('notification_templates_any')
    nt_success_pg = notifiable_resource.get_related('notification_templates_success')
    nt_error_pg = notifiable_resource.get_related('notification_templates_error')
    if notifiable_resource.type == 'organization':
        nt_pg = notifiable_resource.get_related('notification_templates')
        return [nt_pg, nt_any_pg, nt_success_pg, nt_error_pg]
    else:
        return [nt_any_pg, nt_success_pg, nt_error_pg]


def set_read_role(user_pg, notifiable_resource):
    """Helper function that grants a user the read_role of a notifiable_resource."""
    if notifiable_resource.type == 'inventory_source':
        inventory_pg = notifiable_resource.get_related('inventory')
        set_roles(user_pg, inventory_pg, ['read'])
    else:
        set_roles(user_pg, notifiable_resource, ['read'])


def check_user_capabilities(resource, role):
    """Helper function used in checking the values of summary_fields flag, 'user_capabilities'"""
    assert resource.summary_fields['user_capabilities'] == user_capabilities[resource.type][role], \
        "Unexpected response for 'user_capabilities' when testing against a[n] %s resource with a user with %s permissions." \
        % (resource.type, role)
    # if given an inventory, additionally check child groups and hosts
    # child groups/hosts should have the same value for 'user_capabilities' as their inventory
    if resource.type == 'inventory':
        groups_pg = resource.get_related('groups')
        for group in groups_pg.results:
            assert group.summary_fields['user_capabilities'] == user_capabilities['group'][role], \
                "Unexpected response for 'user_capabilities' when testing groups with a user with inventory-%s." % role
        hosts_pg = resource.get_related('hosts')
        for host in hosts_pg.results:
            assert host.summary_fields['user_capabilities'] == user_capabilities['host'][role], \
                "Unexpected response for 'user_capabilities' when testing hosts with a user with inventory-%s." % role
