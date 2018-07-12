import pytest

from tests.lib.helpers.rbac_utils import get_nt_endpoints


@pytest.fixture
def set_test_roles(factories):
    """Helper fixture used in creating the roles used in our RBAC tests."""
    def func(user, resource, agent, role, team=None, **kwargs):
        """:param user: The api page model for a user
        :param resource: Test Tower resource (a job template for example)
        :param agent: Either "user" or "team"; used for test parametrization
        :param role: Test role to give to our user
        Note: the organization of our team matters when we're testing
        credentials.
        """
        if agent == "user":
            resource.set_object_roles(user, role, **kwargs)
        elif agent == "team":
            if not team:
                # create our team in our user organization if applicable
                organizations = user.related.organizations.get()
                if organizations.results:
                    team = factories.team(organization=organizations.results[0])
                else:
                    team = factories.team()
            team.set_object_roles(user, 'member')
            resource.set_object_roles(team, role, **kwargs)
            return team
        else:
            raise ValueError("Unhandled 'agent' value.")
    return func


@pytest.fixture(scope="function", params=['organization', 'job_template', 'workflow_job_template', 'custom_inventory_source', 'project'])
def notifiable_resource(request, organization):
    """Iterates through the Tower objects that support notifications."""
    resource = request.getfuncargvalue(request.param)
    # provide organization for WFJT
    if resource.type == "workflow_job_template":
        resource.organization = organization.id
    return resource


@pytest.fixture
def resource_with_notification(notifiable_resource, email_notification_template):
    """Tower resource with an associated email notification template."""
    endpoints = get_nt_endpoints(notifiable_resource)
    for endpoint in endpoints:
        notifiable_resource.add_notification_template(email_notification_template, endpoint=endpoint)
    return notifiable_resource
