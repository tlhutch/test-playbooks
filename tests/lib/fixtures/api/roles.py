import pytest

import towerkit.exceptions


@pytest.fixture
def set_test_roles(factories):
    """Helper fixture used in creating the roles used in our RBAC tests."""
    def func(user_pg, resource, agent, role):
        """:param user_pg: The api page model for a user
        :param resource: Test Tower resource (a job template for example)
        :param agent: Either "user" or "team"; used for test parametrization
        :param role: Test role to give to our user_pg
        Note: the organization of our team matters when we're testing
        credentials.
        """
        if agent == "user":
            resource.set_object_roles(user_pg, role)
        elif agent == "team":
            # create our team in our user organization if applicable
            organizations_pg = user_pg.get_related("organizations")
            if organizations_pg.results:
                team_pg = factories.team(organization=organizations_pg.results[0])
            else:
                team_pg = factories.team()
            team_pg.set_object_roles(user_pg, 'member')
            resource.set_object_roles(team_pg, role)
        else:
            raise ValueError("Unhandled 'agent' value.")
    return func


@pytest.fixture(scope="function", params=['organization', 'job_template', 'custom_inventory_source', 'project'])
def notifiable_resource(request):
    """Iterates through the Tower objects that support notifications."""
    return request.getfuncargvalue(request.param)


@pytest.fixture(scope="function", params=['organization', 'job_template', 'custom_inventory_source', 'project'])
def resource_with_notification(request, email_notification_template):
    """Tower resource with an associated email notification template."""
    resource = request.getfuncargvalue(request.param)

    # associate our email NT with all notification template endpoints
    payload = dict(id=email_notification_template.id)
    endpoints = ['notification_templates_any', 'notification_templates_success', 'notification_templates_error']
    for endpoint in endpoints:
        with pytest.raises(towerkit.exceptions.NoContent):
            resource.get_related(endpoint).post(payload)
    return resource
