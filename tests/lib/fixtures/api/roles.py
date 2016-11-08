import pytest

from towerkit.api.pages import Role_Page, Roles_Page, Team_Page, User_Page
from towerkit.exceptions import NoContent


@pytest.fixture(scope='session')
def get_role():
    def _get_role(model, role_name):
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
        url = model.get().json.related.object_roles
        for obj_role in Roles_Page(model.testsetup, base_url=url).get().json.results:
            role = Role_Page(model.testsetup, base_url=obj_role.url).get()
            if role.name.lower() == search_name:
                return role

        msg = "Role '{0}' not found for {1}".format(role_name, type(model))
        raise ValueError(msg)
    return _get_role


@pytest.fixture(scope='session')
def set_roles(get_role):
    def _set_roles(agent, model, role_names, endpoint='related_users', disassociate=False):
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
            with pytest.raises(NoContent):
                endpoint_model.post(payload)
    return _set_roles
