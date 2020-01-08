
import re
import time
import dateutil
from copy import deepcopy
from uuid import uuid4

import pytest

from awxkit.api.client import Connection
from awxkit.api import get_registered_page
from awxkit.config import config as qe_config
from awxkit.utils import random_title
from awxkit import exceptions as exc

from tests.api import APITest


@pytest.mark.usefixtures('authtoken')
class TestApplications(APITest):

    def test_options_validity(self, v2):
        options = v2.applications.options()
        post = options.actions.POST

        agt = post.authorization_grant_type
        assert agt.label == 'Authorization Grant Type'
        assert agt.type == 'choice'
        expected_choices = {
            'authorization-code': 'Authorization code',
            'password': 'Resource owner password-based',
        }
        assert {c[0]: c[1] for c in agt.choices} == expected_choices
        assert agt.required is True

        client_type = post.client_type
        assert client_type.label == 'Client Type'
        assert client_type.type == 'choice'
        expected_choices = {'confidential': 'Confidential',
                            'public': 'Public'}
        assert {c[0]: c[1] for c in client_type.choices} == expected_choices
        assert client_type.required is True

        uris = post.redirect_uris
        assert uris.label == 'Redirect URIs'
        assert uris.type == 'string'
        assert uris.required is False

        skip = post.skip_authorization
        assert skip.label == 'Skip Authorization'
        assert skip.type == 'boolean'
        assert skip.default is False
        assert skip.required is False

        org = post.organization
        assert org.label == 'Organization'
        assert org.type == 'id'
        assert org.required is True

    @pytest.mark.parametrize('missing', ('authorization_grant_type', 'client_type', 'organization'))
    def test_application_creation_without_required_fields(self, v2, factories, missing):
        payload = factories.application.payload()
        del payload[missing]
        with pytest.raises(exc.BadRequest) as e:
            v2.applications.post(payload)
        assert e.value.msg in ({missing: ['This field is required.']}, {missing: ['This field cannot be blank.']})

    @pytest.mark.parametrize('client_type', ('confidential', 'public'))
    @pytest.mark.parametrize('agt', ('authorization-code', 'password'))
    def test_created_application_item_and_list_integrity(self, v2, factories, client_type, agt):
        redirect_uris = 'https://example.com'
        payload = factories.application.payload(authorization_grant_type=agt, client_type=client_type,
                                                redirect_uris=redirect_uris)
        name = payload.name
        description = payload.description
        organization = payload.organization
        app = v2.applications.post(payload)
        assert app.name == name
        assert app.description == description
        assert app.authorization_grant_type == agt
        assert app.client_type == client_type
        assert app.organization == organization
        assert app.redirect_uris == redirect_uris
        assert app.client_id
        client_id = app.client_id

        apps = v2.applications.get(id=app.id)
        assert apps.count == 1
        list_item = apps.results.pop()
        assert list_item.name == name
        assert list_item.description == description
        assert list_item.authorization_grant_type == agt
        assert list_item.client_type == client_type
        assert list_item.organization == organization
        assert list_item.redirect_uris == redirect_uris
        assert list_item.client_id == client_id

    def test_application_organization_name_unique(self, v2, factories):
        org = factories.organization()
        app = factories.application(
            organization=org,
            authorization_grant_type='password',
            client_type='public'
        )

        with pytest.raises(exc.Duplicate) as e:
            factories.application(
                name=app['name'],
                organization=app.ds.organization,
                authorization_grant_type='password',
                client_type='public'
            )
        assert e.value.msg == {'__all__': ['Application with this Name and Organization already exists.']}

    def test_patch_modified_application_integrity(self, v2, factories):
        org = factories.organization()
        app = factories.application(organization=org, authorization_grant_type='password',
                                    client_type='public')
        name = random_title(3)
        app.name = name
        assert app.get().name == name

        description = random_title(10)
        app.description = description
        assert app.get().description == description

        client_type = 'confidential'
        app.client_type = client_type
        assert app.get().client_type == client_type

        uris = 'http://example.com http://example.org'
        app.redirect_uris = uris
        assert app.get().redirect_uris == uris

    def test_put_modified_application_integrity(self, v2, factories):
        org = factories.organization()
        app = factories.application(organization=org, authorization_grant_type='password',
                                    client_type='public')
        app_body = deepcopy(app.json)
        app_body['name'] = random_title(3)
        app.put(app_body)
        assert app.get().name == app_body['name']

        app_body['description'] = random_title(10)
        app.put(app_body)
        assert app.get().description == app_body['description']

        app_body['client_type'] = 'confidential'
        app.put(app_body)
        assert app.get().client_type == app_body['client_type']

        app_body['redirect_uris'] = 'http://example.com http://example.org'
        app.put(app_body)
        assert app.get().redirect_uris == app_body['redirect_uris']

    def test_delete_application(self, v2, factories):
        org = factories.organization()
        app = factories.application(organization=org, authorization_grant_type='password',
                                    client_type='public')
        apps = v2.applications.get(id=app.id)
        assert apps.count == 1

        app.delete()
        apps = v2.applications.get(id=app.id)
        assert apps.count == 0

    @pytest.mark.parametrize('field', ('client_id', 'client_secret', 'authorization_grant_type'))
    def test_read_only_application_fields_have_forbidden_writes(self, factories, field):
        org = factories.organization()
        app = factories.application(organization=org, client_type='confidential')
        app = app.get()
        expected = app[field]
        setattr(app, field, 'SHOULD_BE_FORBIDDEN')
        modified_app = app.get()
        assert modified_app[field] != 'SHOULD_BE_FORBIDDEN'
        assert modified_app[field] == expected

    def test_application_creation_in_activity_stream(self, v2, factories, privileged_user, organization):
        def assert_stream_validity(app):
            activity_stream = app.related.activity_stream.get()
            assert activity_stream.count == 1
            entry = activity_stream.results.pop()
            assert entry.operation == 'create'
            assert entry.object1 == 'o_auth2_application'
            assert entry.related.actor == privileged_user.endpoint
            assert entry.changes.id == app.id

        with self.current_user(privileged_user):
            app = factories.application(organization=organization)
            assert_stream_validity(app)

        assert_stream_validity(app)

    def test_application_modification_in_activity_stream(self, v2, factories, privileged_user, organization):
        def assert_stream_validity(app, app_body, orig_body):
            activity_stream = app.related.activity_stream.get()
            assert activity_stream.count == 2
            entry = activity_stream.results.pop()
            assert entry.operation == 'update'
            assert entry.object1 == 'o_auth2_application'
            assert entry.related.actor == privileged_user.endpoint
            assert entry.changes.name == [body['name'] for body in (orig_body, app_body)]
            assert entry.changes.description == [body['description'] for body in (orig_body, app_body)]
            assert entry.changes.redirect_uris == [body['redirect_uris'] for body in (orig_body, app_body)]

        with self.current_user(privileged_user):
            app = factories.application(organization=organization)
            orig_body = app.json
            app_body = deepcopy(app.json)
            app_body['name'] = 'NewApplicationName'
            app_body['description'] = 'NewApplicationDescription'
            app_body['redirect_uris'] = 'http://example.com'
            app.put(app_body)
            assert_stream_validity(app, app_body, orig_body)

        assert_stream_validity(app, app_body, orig_body)

    def test_application_deletion_in_activity_stream(self, v2, factories, privileged_user, organization):
        with self.current_user(privileged_user):
            app = factories.application(organization=organization)
            app.delete()

        entries = v2.activity_stream.get(actor=privileged_user.id)
        assert entries.count == 2
        entry = entries.results[-1]
        assert entry.operation == 'delete'
        assert entry.object1 == 'o_auth2_application'
        assert entry.changes.name == app.name
        assert entry.changes.description == app.description

    def test_org_admins_cannot_read_or_modify_applications_in_other_orgs(self, v2, factories):
        org1, org2 = [factories.organization() for _ in range(2)]
        app = factories.application(organization=org1)
        org2_admin = factories.user(organization=org2)
        org2.set_object_roles(org2_admin, 'Admin')

        with self.current_user(org2_admin):
            with pytest.raises(exc.Forbidden):
                app.get()

            with pytest.raises(exc.Forbidden):
                app.put()

            with pytest.raises(exc.Forbidden):
                app.patch(description='This should not work')
            assert app.description != 'This should not work'

            with pytest.raises(exc.Forbidden):
                app.delete()
        app.get()

    def test_org_admins_can_manage_applications_in_their_org(self, v2, factories):
        org = factories.organization()
        app = factories.application(organization=org)
        org_admin = factories.user(organization=org)
        org.set_object_roles(org_admin, 'Admin')

        with self.current_user(org_admin):
            app.get()
            app.put()
            app.patch(description='This should work')
            assert app.description == 'This should work'
            app.delete()
            with pytest.raises(exc.NotFound):
                app.get()

    def test_non_admin_users_cannot_modify_applications(self, v2, factories):
        org = factories.organization()
        app = factories.application(organization=org)
        org_user = factories.user(organization=org)

        with self.current_user(org_user):
            app.get()

            with pytest.raises(exc.Forbidden):
                app.put()

            with pytest.raises(exc.Forbidden):
                app.patch(description='This should not work')
            assert app.description != 'This should not work'

            with pytest.raises(exc.Forbidden):
                app.delete()
        app.get()

    def test_app_in_activity_stream_for_org_users(self, v2, factories):
        org = factories.organization()
        app = factories.application(organization=org)
        org_user = factories.user(organization=org)

        with self.current_user(org_user):
            assert app.related.activity_stream.get().count == 1

    def test_app_not_in_activity_stream_for_non_org_users(self, v2, factories):
        org1, org2 = [factories.organization() for _ in range(2)]
        app = factories.application(organization=org1)
        org2_user = factories.user(organization=org2)
        activity_stream_entry = app.related.activity_stream.get().results.pop()

        with self.current_user(org2_user):
            assert v2.activity_stream.get(id=activity_stream_entry.id).count == 0


@pytest.mark.usefixtures('authtoken')
class TestApplicationTokens(APITest):

    censored = '************'

    def test_options_validity(self, v2):
        options = v2.tokens.options()
        post = options.actions.POST
        get = options.actions.GET

        application = post.application
        assert application.label == 'Application'
        assert application.type == 'id'
        assert application.required is False

        scope = post.scope
        assert scope.label == 'Scope'
        assert scope.type == 'string'
        assert scope.required is False
        assert scope.default == 'write'

        expires = get.expires
        assert expires.label == 'Expires'
        assert expires.type == 'datetime'

    def test_created_token_item_and_list_integrity(self, v2, factories):
        payload = factories.access_token.payload(oauth_2_application=True)
        application = payload.ds.oauth_2_application.id
        description = payload.description
        scope = payload.scope
        access_token = v2.tokens.post(payload)
        me_id = v2.me.get().results[0].id
        assert access_token.description == description
        assert access_token.scope == scope
        assert access_token.application == application
        assert access_token.user == me_id
        assert access_token.token
        assert access_token.refresh_token
        assert access_token.created
        assert access_token.expires

        items = v2.tokens.get(id=access_token.id)
        assert items.count == 1
        list_item = items.results.pop()
        assert list_item.description == description
        assert list_item.scope == scope
        assert list_item.application == application
        assert list_item.user == me_id
        assert list_item.token == self.censored
        assert list_item.refresh_token == self.censored

        assert access_token.get().token == self.censored
        assert access_token.refresh_token == self.censored

    def test_patch_modified_token_integrity(self, v2, factories):
        token = factories.access_token(oauth_2_application=False)
        description = random_title(10)
        token.description = description
        assert token.get().description == description
        token.scope = 'read'
        assert token.get().scope == 'read'

    def test_put_modified_token_integrity(self, v2, factories):
        token = factories.access_token(oauth_2_application=False)
        token_body = deepcopy(token.json)
        token_body['description'] = random_title(10)
        token_body['scope'] = 'read'
        token.put(token_body)
        assert token.get().description == token_body['description']
        assert token.scope == 'read'

    @pytest.mark.parametrize('with_self', [True, False])
    def test_delete_token(self, v2, factories, with_self):
        token = factories.access_token(oauth_2_application=False)
        tokens = v2.tokens.get(id=token.id)
        assert tokens.count == 1

        conn = Connection(qe_config.base_url)
        conn.login(token=token.token, auth_type='Bearer')
        if with_self:
            # Test that we can then delete the token with itself
            # See https://github.com/ansible/awx/issues/5478
            resp = conn.delete(
                '/api/v2/tokens/{}'.format(token.id),
            )
            assert resp.status_code == 204
        else:
            token.delete()
        
        resp = conn.get('/api/v2/me/')
        assert resp.status_code == 401

        tokens = v2.tokens.get(id=token.id)
        assert tokens.count == 0

    def test_deleted_application_also_deletes_tokens(self, v2, factories):
        payload = factories.access_token.payload(oauth_2_application=True)
        application = payload.ds.oauth_2_application
        token = v2.tokens.post(payload)

        tokens = v2.tokens.get(id=token.id)
        assert tokens.count == 1

        application.delete()
        tokens = v2.tokens.get(id=token.id)
        assert tokens.count == 0

    def test_token_creation_in_activity_stream(self, v2, factories, privileged_user, organization):
        def assert_stream_validity(token):
            activity_stream = token.related.activity_stream.get()
            assert activity_stream.count == 1
            entry = activity_stream.results.pop()
            assert entry.operation == 'create'
            assert entry.object1 == 'o_auth2_access_token'
            assert entry.related.actor == privileged_user.endpoint
            assert entry.changes.id == token.id

        with self.current_user(privileged_user):
            token = factories.access_token(oauth_2_application=None)
            assert_stream_validity(token)

        assert_stream_validity(token)

        with self.current_user(privileged_user):
            app = factories.application(organization=organization)
            token = factories.access_token(oauth_2_application=app)
            assert_stream_validity(token)

        assert_stream_validity(token)

    def test_token_modification_in_activity_stream(self, v2, factories, privileged_user, organization):
        def assert_stream_validity(app, app_body, orig_body):
            activity_stream = app.related.activity_stream.get()
            assert activity_stream.count == 2
            entry = activity_stream.results.pop()
            assert entry.operation == 'update'
            assert entry.object1 == 'o_auth2_access_token'
            assert entry.related.actor == privileged_user.endpoint
            assert entry.changes.description == [body['description'] for body in (orig_body, app_body)]
            assert entry.changes.scope == [body['scope'] for body in (orig_body, app_body)]

        with self.current_user(privileged_user):
            token = factories.access_token(oauth_2_application=None)
            orig_body = token.json
            token_body = deepcopy(token.json)
            token_body['description'] = 'NewTokenDescription'
            token_body['scope'] = 'read'
            token.put(token_body)
            assert_stream_validity(token, token_body, orig_body)

        assert_stream_validity(token, token_body, orig_body)

        with self.current_user(privileged_user):
            app = factories.application(organization=organization)
            token = factories.access_token(oauth_2_application=app)
            orig_body = token.json
            token_body = deepcopy(token.json)
            token_body['description'] = 'NewTokenDescription'
            token_body['scope'] = 'read'
            token.put(token_body)
            assert_stream_validity(token, token_body, orig_body)

        assert_stream_validity(token, token_body, orig_body)

    def test_user_access_token_login_reflects_user(self, v2, factories):
        user = factories.user()
        with self.current_user(user):
            token = factories.access_token(organization=None)
        with self.current_user(token):
            me = v2.me.get().results[0]
            assert me.username == user.username

    @pytest.mark.parametrize('ct', ('confidential', 'public'))
    @pytest.mark.parametrize('agt', ('authorization-code', 'password'))
    def test_user_application_token_login_reflects_user(self, v2, factories, ct, agt):
        org = factories.organization()
        user = factories.user(organization=org)
        app = factories.application(organization=org, client_type=ct, authorization_grant_type=agt,
                                    redirect_uris='https://example.com')
        with self.current_user(user):
            token = factories.access_token(oauth_2_application=app)

        assert token.refresh_token is not None
        assert v2.me.get().results[0].username != user.username
        with self.current_user(token):
            me = v2.me.get().results[0]
            assert me.username == user.username

    @pytest.mark.parametrize('ct', ('confidential', 'public'))
    @pytest.mark.parametrize('agt', ('authorization-code', 'password'))
    def test_users_cannot_read_other_user_tokens(self, v2, factories, ct, agt):
        org = factories.organization()
        user1, user2 = [factories.user(organization=org) for _ in range(2)]
        app = factories.application(organization=org, client_type=ct, authorization_grant_type=agt,
                                    redirect_uris='https://example.com')
        with self.current_user(user1):
            token = factories.access_token(oauth_2_application=app)

        with self.current_user(user2):
            user1_token = v2.tokens.get(id=token.id)
            with pytest.raises(exc.Forbidden):
                token.get()
            assert v2.applications.get(id=app.id).results.pop().related.tokens.get().count == 0
        assert user1_token.count == 0

    @pytest.mark.parametrize('ct', ('confidential', 'public'))
    @pytest.mark.parametrize('agt', ('authorization-code', 'password'))
    def test_users_cannot_modify_other_user_tokens(self, v2, factories, ct, agt):
        org = factories.organization()
        user1, user2 = [factories.user(organization=org) for _ in range(2)]
        app = factories.application(organization=org, client_type=ct, authorization_grant_type=agt,
                                    redirect_uris='https://example.com')
        with self.current_user(user1):
            token = factories.access_token(oauth_2_application=app)

        with self.current_user(user2):
            with pytest.raises(exc.Forbidden):
                token.patch(description='this should fail')
        assert token.get().description != 'this should fail'

        with self.current_user(user2):
            with pytest.raises(exc.Forbidden):
                token.put()

        with self.current_user(user2):
            with pytest.raises(exc.Forbidden):
                token.delete()
        assert token.get()

    def test_token_creation_not_in_activity_stream_for_non_org_users(self, v2, factories):
        org1, org2 = [factories.organization() for _ in range(2)]
        app = factories.application(organization=org1)
        org1_user = factories.user(organization=org1)
        org2_user = factories.user(organization=org2)
        with self.current_user(org1_user):
            token = factories.access_token(oauth_2_application=app)

        activity_stream_entry = token.related.activity_stream.get().results.pop()

        with self.current_user(org2_user):
            assert v2.activity_stream.get(id=activity_stream_entry.id).count == 0

    def test_token_creation_not_in_activity_stream_for_other_org_users(self, v2, factories):
        org = factories.organization()
        app = factories.application(organization=org)
        org_user1 = factories.user(organization=org)
        org_user2 = factories.user(organization=org)
        with self.current_user(org_user1):
            token = factories.access_token(oauth_2_application=app)
        activity_stream_entry = token.related.activity_stream.get().results.pop()
        with self.current_user(org_user2):
            assert v2.activity_stream.get(id=activity_stream_entry.id).count == 0

    def test_token_creation_in_activity_stream_for_org_admin(self, v2, factories):
        org = factories.organization()
        app = factories.application(organization=org)
        org_user = factories.user(organization=org)
        org_admin = factories.user(organization=org)
        org.set_object_roles(org_admin, 'Admin')
        with self.current_user(org_user):
            token = factories.access_token(oauth_2_application=app)
            assert token.related.activity_stream.get().count == 1

        with self.current_user(org_admin):
            assert token.related.activity_stream.get().count == 1

    @pytest.mark.serial
    @pytest.mark.ansible(host_pattern='tower[0]')  # target 1 normal instance
    def test_revoked_tokens_cleaned_up(self, ansible_runner, v2, factories):
        """Regression test for https://github.com/ansible/awx/issues/3825

        Once tokens have been revoked, all of them should be removed by the management
        command `awx-manage cleartokens`.
        """
        payload = factories.access_token.payload(oauth_2_application=True)
        application = payload.ds.oauth_2_application
        token = v2.tokens.post(payload)
        oauth2_token_name = token['token']
        refresh_token_name = token['refresh_token']

        contacted = ansible_runner.command('awx-manage revoke_oauth2_tokens')
        result = list(contacted.values())[0]
        stdout = result['stdout']
        stderr = result['stderr']
        regular_token_revoked = re.search(f"revoked.*{oauth2_token_name}", stdout)
        assert regular_token_revoked, f'Token not reported as revoked, stdout: {stdout}, stderr: {stderr}'
        assert result['rc'] == 0, f'Unexpected return code, stdout: {stdout}, stderr: {stderr}'

        contacted = ansible_runner.command('awx-manage revoke_oauth2_tokens --all')
        result = list(contacted.values())[0]
        stdout = result['stdout']
        stderr = result['stderr']
        refresh_token_revoked = re.search(f"revoked.*{refresh_token_name}", stdout)
        assert refresh_token_revoked, f'Token not reported as revoked, stdout: {stdout}, stderr: {stderr}'
        assert result['rc'] == 0, f'Unexpected return code, stdout: {stdout}, stderr: {stderr}'

        contacted = ansible_runner.command('awx-manage cleartokens')
        result = list(contacted.values())[0]
        stdout = result['stdout']
        stderr = result['stderr']
        assert result['rc'] == 0, f'Unexpected return code, stdout: {stdout}, stderr: {stderr}'

        assert application.related.tokens.get().count == 0

    @pytest.mark.serial
    @pytest.mark.ansible(host_pattern='tower[0]')  # target 1 normal instance
    def test_expired_tokens_cleaned_up(self, v2, update_setting_pg, ansible_runner, factories):
        auth_settings = v2.settings.get().get_endpoint('authentication')
        payload = {
            'OAUTH2_PROVIDER': {
                'ACCESS_TOKEN_EXPIRE_SECONDS': 1,
                'REFRESH_TOKEN_EXPIRE_SECONDS': 1
            }
        }
        update_setting_pg(auth_settings, payload)

        user = factories.user(organization=factories.organization())
        with self.current_user(user):
            token = user.related.personal_tokens.post()
            # the difference between the created and expiration dates
            # should be _just under_ one second
            assert (dateutil.parser.parse(token.expires) - dateutil.parser.parse(token.created)).seconds == 0
            time.sleep(3)
            assert user.related.personal_tokens.get().count == 1

        contacted = ansible_runner.command('awx-manage cleartokens')
        result = list(contacted.values())[0]
        stdout = result['stdout']
        stderr = result['stderr']
        assert result['rc'] == 0, f'Unexpected return code, stdout: {stdout}, stderr: {stderr}'

        with self.current_user(user):
            assert user.related.personal_tokens.get().count == 0


class TestTokenAuthenticationBase(APITest):

    def get_page(self, token, endpoint):
        conn = Connection(qe_config.base_url)
        conn.login(token=token, auth_type="Bearer")
        return get_registered_page(endpoint)(conn, endpoint=endpoint).get()

    def me(self, token):
        return self.get_page(token, '/api/v2/me/')


@pytest.mark.usefixtures('authtoken')
class TestTokenAuthentication(TestTokenAuthenticationBase):

    def test_authenticate_with_invalid_access_token(self, v2, factories):
        with pytest.raises(exc.Unauthorized) as e:
            self.me(str(uuid4()))
            assert 'Authentication credentials were not provided. To establish a login session, visit /api/login/.' in str(e.value)

    def test_authenticate_with_access_token(self, v2, factories):
        org = factories.organization()
        user = factories.user(organization=org)
        app = factories.application(organization=org,
                                    client_type='confidential',
                                    authorization_grant_type='password',
                                    redirect_uris='https://example.com')
        with self.current_user(user):
            token = factories.access_token(oauth_2_application=app)

        res = self.me(token.token)
        assert res.results.pop().username == user.username

    def test_authenticate_with_personal_access_token(self, v2, factories):
        user = factories.user(organization=factories.organization())
        with self.current_user(user):
            token = user.related.personal_tokens.post()
        res = self.me(token.token)
        assert res.results.pop().username == user.username

    @pytest.mark.yolo
    def test_access_token_revocation(self, v2, factories):
        user = factories.user(organization=factories.organization())
        with self.current_user(user):
            token = user.related.personal_tokens.post()

        res = self.me(token.token)
        assert res.results.pop().username == user.username

        token.delete()
        with pytest.raises(exc.Unauthorized) as e:
            res = self.me(token.token)
            assert 'Authentication credentials were not provided. To establish a login session, visit /api/login/.' in str(e.value)

    @pytest.mark.serial
    def test_access_token_expiration(self, v2, update_setting_pg, factories):
        auth_settings = v2.settings.get().get_endpoint('authentication')
        payload = {
            'OAUTH2_PROVIDER': {
                'ACCESS_TOKEN_EXPIRE_SECONDS': 1
            }
        }
        update_setting_pg(auth_settings, payload)

        user = factories.user(organization=factories.organization())
        with self.current_user(user):
            token = user.related.personal_tokens.post()
            # the difference between the created and expiration dates
            # should be _just under_ one second
            assert (dateutil.parser.parse(token.expires) - dateutil.parser.parse(token.created)).seconds == 0
            time.sleep(3)

        with pytest.raises(exc.Unauthorized) as e:
            self.me(token.token)
            assert 'Authentication credentials were not provided. To establish a login session, visit /api/login/.' in str(e.value)

    @pytest.mark.parametrize('scope, forbidden', [
        ('read', True),
        ('write', False)
    ])
    def test_read_scope_cannot_create(self, v2, factories, scope, forbidden):
        user = factories.user(organization=factories.organization())
        token = v2.tokens.post({'scope': scope})

        username = random_title(3, non_ascii=False)
        page = self.get_page(token.token, v2.users.endpoint)
        if forbidden:
            with pytest.raises(exc.Forbidden):
                page.post({'username': username, 'password': 'secret'})
        else:
            user = page.post({'username': username, 'password': 'secret'})
            assert user.get().username == username
            user.delete()

    @pytest.mark.parametrize('scope, forbidden', [
        ('read', True),
        ('write', False)
    ])
    def test_read_scope_cannot_edit(self, v2, factories, scope, forbidden):
        user = factories.user(organization=factories.organization())
        token = v2.tokens.post({'scope': scope})

        page = self.get_page(token.token, user.endpoint)
        assert page.get().id == user.id

        if forbidden:
            with pytest.raises(exc.Forbidden):
                page.patch(first_name='Goofus')
        else:
            page.patch(first_name='Gallant')
            assert page.get().first_name == 'Gallant'

    @pytest.mark.parametrize('scope, forbidden', [
        ('read', True),
        ('write', False)
    ])
    def test_read_scope_cannot_delete(self, v2, factories, scope, forbidden):
        user = factories.user(organization=factories.organization())
        token = v2.tokens.post({'scope': scope})

        page = self.get_page(token.token, user.endpoint)
        assert page.get().id == user.id

        if forbidden:
            with pytest.raises(exc.Forbidden):
                page.delete()
        else:
            page.delete()
            with pytest.raises(exc.NotFound):
                page.get()

    @pytest.mark.parametrize('scope, forbidden', [
        ('read', True),
        ('write', False)
    ])
    def test_read_scope_cannot_launch(self, v2, job_template_ping, scope, forbidden):
        token = v2.tokens.post({'scope': scope})
        page = self.get_page(token.token, job_template_ping.related.launch.endpoint)
        assert job_template_ping.related.jobs.get().count == 0

        if forbidden:
            with pytest.raises(exc.Forbidden):
                page.post()
            assert job_template_ping.related.jobs.get().count == 0
        else:
            page.post()
            assert job_template_ping.related.jobs.get().count == 1

    @pytest.mark.parametrize('scope, forbidden', [
        ('read', True),
        ('write', False)
    ])
    def test_read_scope_cannot_attach_detach(self, v2, factories, scope, forbidden):
        token = v2.tokens.post({'scope': scope})
        jt = factories.job_template()
        page = self.get_page(token.token, jt.related.credentials.endpoint)
        assert page.count == 1
        credential_pk = page.get().results.pop().id

        if forbidden:
            with pytest.raises(exc.Forbidden):
                page.post({'disassociate': True, 'id': credential_pk})
            assert page.get().count == 1
            with pytest.raises(exc.Forbidden):
                page.post({'associate': True, 'id': credential_pk})
            assert page.get().count == 1
        else:
            with pytest.raises(exc.NoContent):
                page.post({'disassociate': True, 'id': credential_pk})
                assert page.get().count == 0
            with pytest.raises(exc.NoContent):
                page.post({'associate': True, 'id': credential_pk})
                assert page.get().count == 1

    @pytest.mark.parametrize('scope, forbidden', [
        ('read', True),
        ('write', False)
    ])
    def test_read_scope_cannot_copy(self, v2, factories, scope, forbidden):
        token = v2.tokens.post({'scope': scope})
        jt = factories.job_template()
        page = self.get_page(token.token, jt.get_related('copy').endpoint)

        if forbidden:
            with pytest.raises(exc.Forbidden):
                page.post({'name': 'My OAuth2 Copy'})
        else:
            page.post({'name': 'My OAuth2 Copy'})


@pytest.mark.usefixtures('authtoken')
class TestTokenUsage(TestTokenAuthenticationBase):
    """
    Used to test Tower operations while using token auth
    """
    @pytest.mark.parametrize('ct', ('confidential', 'public'))
    @pytest.mark.parametrize('agt', ('authorization-code', 'password'))
    def test_password_can_be_changed_while_using_authtoken(self, factories, v2, agt, ct):
        org = factories.organization()
        user = factories.user(organization=org)
        app = factories.application(organization=org,
                                    client_type=ct,
                                    authorization_grant_type=agt,
                                    redirect_uris='https://example.com')
        with self.current_user(user):
            token = factories.access_token(oauth_2_application=app)

        with self.current_user(token):
            user.patch(password='NEW_PASSWORD')

        with self.current_user(user.username, 'NEW_PASSWORD'):
            res = v2.me.get().results.pop()
        assert res.username == user.username


@pytest.mark.usefixtures('authtoken')
class TestDjangoOAuthToolkitTokenManagement(TestTokenAuthenticationBase):
    """
    Used to test the `/api/o/` endpoint
    """

    @pytest.mark.parametrize('scope', ['read', 'write'])
    @pytest.mark.parametrize('password_is_correct, expected_status', [
        (True, 200),
        (False, 400)  # used to be 401 https://github.com/oauthlib/oauthlib/issues/264
    ])
    def test_token_creation(self, factories, scope, password_is_correct, expected_status):
        app = factories.application(organization=factories.organization(),
                                    client_type='confidential',
                                    authorization_grant_type='password',
                                    redirect_uris='https://example.com')
        conn = Connection(qe_config.base_url)
        conn.session.auth = (app.client_id, app.client_secret)
        username = qe_config.credentials.users.admin.username
        if password_is_correct:
            password = qe_config.credentials.users.admin.password
        else:
            password = str(uuid4())
        resp = conn.post(
            '/api/o/token/',
            headers={'Content-Type': 'application/x-www-form-urlencoded'},
            data={
                'username': username,
                'password': password,
                'grant_type': 'password',
                'scope': scope
            }
        )
        assert resp.status_code == expected_status

        if expected_status == 200:
            json = resp.json()
            assert json['access_token']
            assert json['refresh_token']
            assert json['token_type'] == 'Bearer'
            assert json['scope'] == scope
            token = resp.json()['access_token']
            res = self.me(token)
            assert res.results.pop().username == username
        else:
            assert 'Invalid credentials given.' in str(resp.content)

    @pytest.mark.parametrize('scope', ['read', 'write'])
    def test_token_revocation(self, factories, scope):
        app = factories.application(organization=factories.organization(),
                                    client_type='confidential',
                                    authorization_grant_type='password',
                                    redirect_uris='https://example.com')

        # Create a token and ensure it works
        conn = Connection(qe_config.base_url)
        username = qe_config.credentials.users.admin.username
        conn.session.auth = (app.client_id, app.client_secret)
        resp = conn.post(
            '/api/o/token/',
            headers={'Content-Type': 'application/x-www-form-urlencoded'},
            data={
                'username': username,
                'password': qe_config.credentials.users.admin.password,
                'grant_type': 'password',
                'scope': scope,
            }
        )
        token = resp.json()['access_token']
        refresh_token = resp.json()['refresh_token']
        res = self.me(token)
        assert res.results.pop().username == username

        # Revoke the access token
        resp = conn.post(
            '/api/o/revoke_token/',
            headers={'Content-Type': 'application/x-www-form-urlencoded'},
            data={'token': token}
        )
        assert resp.status_code == 200

        # Assert that the token no longer works
        with pytest.raises(exc.Unauthorized) as e:
            self.me(token)
            assert 'Authentication credentials were not provided. To establish a login session, visit /api/login/.' in str(e.value)

        # Revoke the refresh token
        resp = conn.post(
            '/api/o/revoke_token/',
            headers={'Content-Type': 'application/x-www-form-urlencoded'},
            data={'token': refresh_token}
        )
        assert resp.status_code == 200

    @pytest.mark.yolo
    @pytest.mark.parametrize('scope', ['read', 'write'])
    def test_refresh_token(self, factories, scope):
        app = factories.application(organization=factories.organization(),
                                    client_type='confidential',
                                    authorization_grant_type='password',
                                    redirect_uris='https://example.com')

        # Create a token and ensure it works
        conn = Connection(qe_config.base_url)
        username = qe_config.credentials.users.admin.username
        conn.session.auth = (app.client_id, app.client_secret)
        resp = conn.post(
            '/api/o/token/',
            headers={'Content-Type': 'application/x-www-form-urlencoded'},
            data={
                'username': username,
                'password': qe_config.credentials.users.admin.password,
                'grant_type': 'password',
                'scope': scope,
            }
        )
        assert resp.json()['scope'] == scope
        old_token = resp.json()['access_token']
        refresh_token = resp.json()['refresh_token']
        res = self.me(old_token)
        assert res.results.pop().username == username

        # refresh to get a new access token
        resp = conn.post(
            '/api/o/token/',
            headers={'Content-Type': 'application/x-www-form-urlencoded'},
            data={
                'refresh_token': refresh_token,
                'grant_type': 'refresh_token',
                'client_id': app.client_id,
                'client_secret': app.client_secret
            }
        )
        assert resp.status_code == 200
        assert resp.json()['scope'] == scope
        new_token = resp.json()['access_token']
        assert old_token != new_token

        # assert that the old token no longer works
        with pytest.raises(exc.Unauthorized) as e:
            self.me(old_token)
            assert 'Authentication credentials were not provided. To establish a login session, visit /api/login/.' in str(e.value)

        # assert that the _new_ token _does_ work
        res = self.me(new_token)
        assert res.results.pop().username == username
