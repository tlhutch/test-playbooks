from towerkit.config import config
import towerkit.exceptions as exc
import fauxfactory
import pytest

from tests.api import APITest


@pytest.fixture(scope="function")
def some_team(request, authtoken, organization):
    payload = dict(name="some_team: %s" % fauxfactory.gen_utf8(),
                   organization=organization.id)
    obj = organization.get_related('teams').post(payload)
    request.addfinalizer(obj.silent_delete)
    return obj


@pytest.fixture(scope="function")
def some_team_credential(request, authtoken, some_team):
    """Create ssh credential"""
    payload = dict(name="credential-%s" % fauxfactory.gen_utf8(),
                   description="machine credential for team:%s" % some_team.name,
                   kind='ssh',
                   team=some_team.id,
                   username=config.credentials['ssh']['username'],
                   password=config.credentials['ssh']['password'],)
    obj = some_team.get_related('credentials').post(payload)
    request.addfinalizer(obj.silent_delete)
    return obj


def team_payload(**kwargs):
    payload = kwargs
    if 'name' not in kwargs:
        payload['name'] = fauxfactory.gen_utf8()
    if 'description' not in kwargs:
        payload['description'] = fauxfactory.gen_utf8()
    return payload


@pytest.mark.usefixtures('authtoken', 'install_enterprise_license_unlimited')
class Test_Teams(APITest):

    def test_duplicate_teams_disallowed_by_organization(self, factories):
        team = factories.team()

        with pytest.raises(exc.Duplicate) as e:
            factories.team(name=team.name, organization=team.ds.organization)
        assert e.value[1]['__all__'] == ['Team with this Organization and Name already exists.']

    def test_privileged_user_can_create_team(self, request, api_teams_pg, privileged_user, user_password, organization):
        """Verify that a privileged user can create teams."""
        with self.current_user(privileged_user.username, user_password):
            obj = api_teams_pg.post(team_payload(organization=organization.id))
            request.addfinalizer(obj.delete)

    def test_unprivileged_user_cannot_create_team(self, api_teams_pg, unprivileged_user, user_password, organization):
        """Verify that a normal unprivileged user cannot create teams."""
        with self.current_user(unprivileged_user.username, user_password):
            with pytest.raises(exc.Forbidden):
                api_teams_pg.post(team_payload(organization=organization.id))

    def test_non_superuser_cannot_create_team_in_another_organization(self, api_teams_pg, non_superuser, user_password, organization,
                                                                      install_enterprise_license_unlimited, another_organization):
        """Verify that only an organization admin can only create teams within
        their organization.
        """
        with self.current_user(non_superuser.username, user_password):
            with pytest.raises(exc.Forbidden):
                api_teams_pg.post(team_payload(organization=another_organization.id))

    def test_organization_cascade_delete(self, team):
        """Verifies that teams get cascade deleted along with their organization."""
        team.get_related("organization").delete()
        with pytest.raises(exc.NotFound):
            team.get()

    def test_org_user_can_see_all_teams_in_org(self, v2, factories, org_user):
        org = org_user.related.organizations.get().results.pop()

        teams_inside_org = []
        for _ in range(3):
            teams_inside_org.append(factories.team(organization=org))

        teams_outside_org = []
        for _ in range(3):
            teams_outside_org.append(factories.team())

        with self.current_user(org_user):
            visible_teams = v2.teams.get().results
            assert set([t.id for t in visible_teams]) == set([t.id for t in teams_inside_org])

    @pytest.mark.parametrize('org_admins_can_see_all_users', [True, False],
                             ids=['ORG_ADMINS_CAN_SEE_ALL_USERS_is_true', 'ORG_ADMINS_CAN_SEE_ALL_USERS_is_false'])
    @pytest.mark.serial
    def test_org_admin_can_see_all_teams_in_org(self, request, v2, factories, org_admin, update_setting_pg,
                                                api_settings_system_pg, org_admins_can_see_all_users):
        update_setting_pg(api_settings_system_pg, dict(ORG_ADMINS_CAN_SEE_ALL_USERS=org_admins_can_see_all_users))

        org = org_admin.related.organizations.get().results.pop()
        teams_inside_org = []
        for _ in range(3):
            teams_inside_org.append(factories.team(organization=org))
        teams_outside_org = []
        for _ in range(3):
            teams_outside_org.append(factories.team())

        with self.current_user(org_admin):
            visible_teams = v2.teams.get().results
            if org_admins_can_see_all_users:
                assert set([t.id for t in visible_teams]) >= set([t.id for t in teams_inside_org])
            else:
                assert set([t.id for t in visible_teams]) == set([t.id for t in teams_inside_org])

    @pytest.mark.parametrize('user', ['anonymous_user', 'another_org_user'])
    def test_non_org_users_cannot_see_team_in_org(self, request, v2, factories, user):
        non_organization_user = request.getfixturevalue(user)
        factories.team()
        with self.current_user(non_organization_user):
            assert v2.teams.get().count == 0

    def test_org_user_can_assign_permissions_to_team(self, factories, org_user):
        org = org_user.related.organizations.get().results.pop()
        team_inside_org = factories.team(organization=org)
        team_outside_org = factories.team()

        jt = factories.job_template()
        jt.set_object_roles(org_user, 'admin')
        with self.current_user(org_user):
            jt.set_object_roles(team_inside_org, 'read')

            with pytest.raises(exc.Forbidden):
                jt.set_object_roles(team_outside_org, 'read')

    @pytest.mark.parametrize('org_admins_can_see_all_users', [True, False],
                             ids=['ORG_ADMINS_CAN_SEE_ALL_USERS_is_true', 'ORG_ADMINS_CAN_SEE_ALL_USERS_is_false'])
    @pytest.mark.serial
    def test_org_admin_can_assign_permissions_to_team(self, request, v2, factories, org_admin, update_setting_pg,
                                                      api_settings_system_pg, org_admins_can_see_all_users):
        update_setting_pg(api_settings_system_pg, dict(ORG_ADMINS_CAN_SEE_ALL_USERS=org_admins_can_see_all_users))

        org = org_admin.related.organizations.get().results.pop()
        team_inside_org = factories.team(organization=org)
        team_outside_org = factories.team()

        jt = factories.job_template()
        jt.set_object_roles(org_admin, 'admin')
        with self.current_user(org_admin):
            jt.set_object_roles(team_inside_org, 'read')

            if org_admins_can_see_all_users:
                jt.set_object_roles(team_outside_org, 'read')
            else:
                with pytest.raises(exc.Forbidden):
                    jt.set_object_roles(team_outside_org, 'read')

    @pytest.mark.parametrize('user', ['anonymous_user', 'another_org_user'])
    def test_non_org_users_cannot_assign_permissions_to_team(self, request, factories, user):
        non_organization_user = request.getfixturevalue(user)
        team = factories.team()
        jt = factories.job_template()
        jt.set_object_roles(non_organization_user, 'admin')
        with self.current_user(non_organization_user):
            with pytest.raises(exc.Forbidden):
                jt.set_object_roles(team, 'read')
