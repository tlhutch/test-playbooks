import json

import towerkit.exceptions
import fauxfactory
import pytest

from tests.api import Base_Api_Test


@pytest.mark.api
@pytest.mark.skip_selenium
@pytest.mark.destructive
class Test_Credential(Base_Api_Test):

    pytestmark = pytest.mark.usefixtures('authtoken', 'install_enterprise_license_unlimited')

    @pytest.mark.github("https://github.com/ansible/ansible-tower/issues/3303")
    def test_duplicate(self, request, factories, api_credentials_pg):
        """As of Tower-3.0, we allow for duplicate credentials when a value is supplied
        for user or team but not for organization.

        Note: in Tower-3.0.2, we effectively no longer have pure team credentials.
        Team credentials now act like organization credentials and have their value
        for organization inherited through their team.
        """
        user_pg = factories.user()
        team_pg = factories.team()

        # create duplicate user credentials
        payload = factories.credential.payload(user=user_pg, organization=None)[0]
        for _ in range(2):
            obj = api_credentials_pg.post(payload)
            request.addfinalizer(obj.silent_delete)

        # attempt to create duplicate team-organization credentials
        payload = factories.credential.payload(team=team_pg, organization=None)[0]
        obj = api_credentials_pg.post(payload)
        request.addfinalizer(obj.silent_delete)
        with pytest.raises(towerkit.exceptions.Duplicate):
            api_credentials_pg.post(payload)

        # attempt to create duplicate organization credentials
        payload = factories.credential.payload()[0]
        obj = api_credentials_pg.post(payload)
        request.addfinalizer(obj.silent_delete)
        with pytest.raises(towerkit.exceptions.Duplicate):
            api_credentials_pg.post(payload)

    def test_unicode(self, admin_user, api_credentials_pg):
        """Create an ssh credential where the password fields contain unicode."""
        payload = dict(name=fauxfactory.gen_utf8(),
                       description=fauxfactory.gen_utf8(),
                       kind='ssh',
                       user=admin_user.id,
                       username=fauxfactory.gen_alphanumeric(),
                       password=fauxfactory.gen_utf8(),
                       become_method="sudo",
                       become_username=fauxfactory.gen_alphanumeric(),
                       become_password=fauxfactory.gen_utf8())
        credential = api_credentials_pg.post(payload)
        credential.delete()

    def test_team_credentials_are_organization_credentials(self, factories):
        """Create a team credential and assert that the created credential
        is also an organization credential.

        Note: we use summary_fields here because of a number of issues regarding
        credential_pg JSON. Please update this test once #3304 and #3089 are resolved.
        """
        team = factories.team()
        credential = factories.credential(team=team, organization=None)

        # assert that our credential is both a team and organization credential
        owner_organizations = [item for item in credential.summary_fields.owners if item.get("type", None) == "organization"]
        owner_teams = [item for item in credential.summary_fields.owners if item.get("type", None) == "team"]
        assert(owner_organizations), "Expected to find an organization under 'owner' summary_fields."
        assert(owner_teams), "Expected to find a team under 'owner' summary_fields."

        # assert that our credential organization is our team organization
        assert owner_organizations[0].get("id", None) == team.organization, \
            "Credential organization and team organization do not align."

    @pytest.mark.parametrize("payload, expected_result", [
        (dict(password="foo", username="foo", host="foo"), {"project": ["Project name required for OpenStack credential."]}),
        (dict(project="foo", username="foo", host="foo"), {"password": ["Password or API key required for OpenStack credential."]}),
        (dict(project="foo", password="foo", host="foo"), {"username": ["Username required for OpenStack credential."]}),
        (dict(project="foo", password="foo", username="foo"), {"host": ["Host required for OpenStack credential."]}),
    ], ids=['project', 'password', 'username', 'host'])
    def test_post_invalid_openstack_credential(self, admin_user, api_credentials_pg, payload, expected_result):
        """Tests that if you post an OpenStack credential with missing params that
        the post fails.
        """
        # create payload
        payload.update(dict(name="openstack-credential-%s" % fauxfactory.gen_utf8(),
                       description="Openstack credential %s" % fauxfactory.gen_utf8(),
                       kind='openstack',
                       user=admin_user.id, ))

        # post payload and verify that exception raised
        exc_info = pytest.raises(towerkit.exceptions.BadRequest, api_credentials_pg.post, payload)
        result = exc_info.value[1]
        assert result == expected_result, "Unexpected response when posting a credential " \
            "with a missing param. %s" % json.dumps(result)
