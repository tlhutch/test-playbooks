import logging
import http.client
import os

import awxkit.exceptions
from awxkit.yaml_file import load_file
import pytest


log = logging.getLogger(__name__)


# load expected values for summary_fields user_capabilities
user_capabilities = load_file(os.path.join(os.path.dirname(__file__), 'user_capabilities.yml'))


# -----------------------------------------------------------------------------
# Integrated Assertion Helpers
# -----------------------------------------------------------------------------

def check_role_association(user, model, role_name):
    # check the related users endpoint of the role for user
    role = model.get_object_role(role_name, by_name=True)
    results = role.get_related('users').get(username=user.username)
    if results.count != 1:
        msg = 'Unable to verify {0} {1} role association'
        pytest.fail(msg.format(type(model), role_name))


def check_role_disassociation(user, model, role_name):
    # check the related users endpoint of the role for absence of user
    role = model.get_object_role(role_name, by_name=True)
    results = role.get_related('users').get(username=user.username)
    if results.count != 0:
        msg = 'Unable to verify {0} {1} role disassociation'
        pytest.fail(msg.format(type(model), role_name))


def check_request(model, method, code, data=None):
    """Make an HTTP request and check the response payload against the provided
    http response code
    """
    method = method.lower()
    connection_method = getattr(model.connection, method)

    if method in ('get', 'head', 'options', 'delete'):
        if data:
            log.warning('Unused {0} request data provided'.format(method))
        response = connection_method(model.endpoint)
    else:
        response = connection_method(model.endpoint, data)
    if response.status_code != code:
        msg = 'Unexpected {0} request response code: {1} != {2}'
        pytest.fail(msg.format(method, response.status_code, code))


def assert_response_raised(tower_object, response=http.client.OK, methods=('put', 'patch', 'delete')):
    """Check PUT, PATCH, and DELETE against a Tower resource."""
    exc_dict = {
        http.client.OK: None,
        http.client.NOT_FOUND: awxkit.exceptions.NotFound,
        http.client.FORBIDDEN: awxkit.exceptions.Forbidden,
    }
    exc = exc_dict[response]
    for method in methods:
        if exc is None:
            if method == 'delete':
                tower_object.delete()
                if hasattr(tower_object, 'wait_until_deleted'):
                    tower_object.wait_until_deleted()
            else:
                getattr(tower_object, method)()
        else:
            with pytest.raises(exc):
                getattr(tower_object, method)()


def check_read_access(tower_object, expected_forbidden=[], unprivileged=False):
    """Check GET against a Tower resource."""
    # for test scenarios involving unprivileged users
    if unprivileged:
        with pytest.raises(awxkit.exceptions.Forbidden):
            tower_object.get()
    # for test scenarios involving privileged users
    else:
        tower_object.get()
        for related in tower_object.related:
            if related in expected_forbidden:
                with pytest.raises(awxkit.exceptions.Forbidden):
                    tower_object.get_related(related)
            else:
                tower_object.get_related(related)


# -----------------------------------------------------------------------------
# Helper functions
# -----------------------------------------------------------------------------

def get_resource_roles(resource):
    """Helper function that returns a list containing a Tower resource's role names."""
    return [role.replace("_role", "").replace("_", " ").replace("adhoc", "ad hoc") for role in [role.name.lower() for role in resource.summary_fields.object_roles.values()]]


def get_nt_endpoints(notifiable_resource):
    """Helper function that returns the notification template endpoints of a
    notifiable Tower resource.
    """
    if notifiable_resource.type == "organization":
        return ['notification_templates', 'notification_templates_started', 'notification_templates_success', 'notification_templates_error']
    else:
        return ['notification_templates_started', 'notification_templates_success', 'notification_templates_error']


def check_user_capabilities(resource, role):
    """Helper function used in checking the values of summary_fields flag, 'user_capabilities'"""
    assert resource.summary_fields['user_capabilities'] == user_capabilities[resource.type][role], \
        "Unexpected response for 'user_capabilities' when testing against a[n] %s resource with a user with %s permissions." \
        % (resource.type, role)
    # if given an inventory, additionally check child groups and hosts
    # child groups/hosts should have the same value for 'user_capabilities' as their inventory
    if resource.type == 'inventory':
        groups = resource.get_related('groups')
        for group in groups.results:
            assert group.summary_fields['user_capabilities'] == user_capabilities['group'][role], \
                "Unexpected response for 'user_capabilities' when testing groups with a user with inventory-{0}.".format(role)
        hosts = resource.get_related('hosts')
        for host in hosts.results:
            assert host.summary_fields['user_capabilities'] == user_capabilities['host'][role], \
                "Unexpected response for 'user_capabilities' when testing hosts with a user with inventory-{0}.".format(role)
        inv_sources = resource.get_related('inventory_sources')
        for inv_source in inv_sources.results:
            assert inv_source.summary_fields['user_capabilities'] == user_capabilities['inventory_source'][role], \
                "Unexpected response for 'user_capabilities' when testing inv_source with a user with inventory-{0}.".format(role)
