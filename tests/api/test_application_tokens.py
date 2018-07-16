from copy import deepcopy

from towerkit.utils import random_title
from towerkit import exceptions as exc
import pytest

from tests.api import APITest


@pytest.mark.usefixtures('authtoken', 'install_enterprise_license_unlimited')
class TestApplications(APITest):

    @pytest.mark.github('https://github.com/ansible/tower/issues/1289')
    def test_options_validity(self, v2):
        options = v2.applications.options()
        post = options.actions.POST

        agt = post.authorization_grant_type
        assert agt.label == 'Authorization grant type'
        assert agt.type == 'choice'
        expected_choices = {'authorization-code': 'Authorization code',
                            'implicit': 'Implicit',
                            'password': 'Resource owner password-based',
                            'client-credentials': 'Client credentials'}
        assert {c[0]: c[1] for c in agt.choices} == expected_choices
        assert agt.required is True

        client_type = post.client_type
        assert client_type.label == 'Client type'
        assert client_type.type == 'choice'
        expected_choices = {'confidential': 'Confidential',
                            'public': 'Public'}
        assert {c[0]: c[1] for c in client_type.choices} == expected_choices
        assert client_type.required is True

        uris = post.redirect_uris
        assert uris.label == 'Redirect uris'
        assert uris.type == 'string'
        assert uris.required is False

        skip = post.skip_authorization
        assert skip.label == 'Skip authorization'
        assert skip.type == 'boolean'
        assert skip.default is False
        assert skip.required is False

        org = post.organization
        assert org.label == 'Organization'
        assert org.type == 'field'
        assert org.required is True

    @pytest.mark.parametrize('missing', ('authorization_grant_type', 'client_type', 'organization'))
    def test_application_creation_without_required_fields(self, v2, factories, missing):
        payload = factories.application.payload()
        del payload[missing]
        with pytest.raises(exc.BadRequest) as e:
            v2.applications.post(payload)
        assert e.value.message in ({missing: ['This field is required.']}, {missing: ['This field cannot be blank.']})

    @pytest.mark.parametrize('client_type', ('confidential', 'public'))
    @pytest.mark.parametrize('agt', ('authorization-code', 'implicit', 'password', 'client-credentials'))
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

    def test_patch_modified_application_integrity(self, v2, factories):
        app = factories.application(organization=True, authorization_grant_type='password',
                                    client_Type='public')
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
        app = factories.application(organization=True, authorization_grant_type='password',
                                    client_Type='public')
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

    @pytest.mark.parametrize('field', ('client_id', 'client_secret', 'authorization_grant_type'))
    def test_read_only_application_fields_have_forbidden_writes(self, factories, field):
        app = factories.application(organization=True, client_type='confidential')
        expected = app[field]
        setattr(app, field, 'SHOULD_BE_FORBIDDEN')
        modified_app = app.get()
        assert modified_app[field] != 'SHOULD_BE_FORBIDDEN'
        assert modified_app[field] == expected

    @pytest.mark.github('https://github.com/ansible/tower/issues/1125')
    def test_application_creation_in_activity_stream(self, v2, factories, privileged_user, organization):
        def assert_stream_validity(app):
            activity_stream = app.related.activity_stream.get()
            assert activity_stream.count == 1
            entry = activity_stream.results.pop()
            assert entry.operation == 'create'
            assert entry.object1 == 'o_auth2_application'
            assert entry.related.actor == privileged_user.endpoint.replace('v1', 'v2')
            assert entry.changes.id == app.id

        with self.current_user(privileged_user):
            app = factories.application(organization=organization)
            assert_stream_validity(app)

        assert_stream_validity(app)

    @pytest.mark.github('https://github.com/ansible/tower/issues/1125')
    def test_application_modification_in_activity_stream(self, v2, factories, privileged_user, organization):
        def assert_stream_validity(app, app_body, orig_body):
            activity_stream = app.related.activity_stream.get()
            assert activity_stream.count == 2
            entry = activity_stream.results.pop()
            assert entry.operation == 'update'
            assert entry.object1 == 'o_auth2_application'
            assert entry.related.actor == privileged_user.endpoint.replace('v1', 'v2')
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


@pytest.mark.usefixtures('authtoken', 'install_enterprise_license_unlimited')
class TestApplicationTokens(APITest):

    censored = '************'

    @pytest.mark.github('https://github.com/ansible/tower/issues/1291')
    def test_options_validity(self, v2):
        options = v2.tokens.options()
        post = options.actions.POST
        get = options.actions.GET

        application = post.application
        assert application.label == 'Application'
        assert application.type == 'field'
        assert application.required is False

        scope = post.scope
        assert scope.label == 'Scope'
        assert scope.type == 'string'
        assert scope.required is False
        assert scope.default == 'write'

        expires = get.expires
        assert expires.label == 'Expires'
        assert expires.type == 'datetime'

    def test_token_creation_without_required_fields(self, v2, factories):
        payload = factories.access_token.payload()
        del payload['scope']
        with pytest.raises(exc.BadRequest) as e:
            v2.tokens.post(payload)
        assert e.value.message == {'scope': ['This field is required.']}

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

    @pytest.mark.github('https://github.com/ansible/tower/issues/1125')
    def test_token_creation_in_activity_stream(self, v2, factories, privileged_user, organization):
        def assert_stream_validity(token):
            activity_stream = token.related.activity_stream.get()
            assert activity_stream.count == 1
            entry = activity_stream.results.pop()
            assert entry.operation == 'create'
            assert entry.object1 == 'o_auth2_access_token'
            assert entry.related.actor == privileged_user.endpoint.replace('v1', 'v2')
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

    @pytest.mark.github('https://github.com/ansible/tower/issues/1125')
    def test_token_modification_in_activity_stream(self, v2, factories, privileged_user, organization):
        def assert_stream_validity(app, app_body, orig_body):
            activity_stream = app.related.activity_stream.get()
            assert activity_stream.count == 2
            entry = activity_stream.results.pop()
            assert entry.operation == 'update'
            assert entry.object1 == 'o_auth2_access_token'
            assert entry.related.actor == privileged_user.endpoint.replace('v1', 'v2')
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
        user = factories.v2_user()
        with self.current_user(user):
            token = factories.access_token(organization=None)
        with self.current_user(token):
            me = v2.me.get().results[0]
            assert me.username == user.username

    @pytest.mark.parametrize('ct', ('confidential', 'public'))
    @pytest.mark.parametrize('agt', ('authorization-code', 'implicit', 'password', 'client-credentials'))
    def test_user_application_token_login_reflects_user(self, v2, factories, ct, agt):
        org = factories.v2_organization()
        user = factories.v2_user(organization=org)
        app = factories.application(organization=org, client_type=ct, authorization_grant_type=agt,
                                    redirect_uris='https://example.com')
        with self.current_user(user):
            token = factories.access_token(oauth_2_application=app)
        assert v2.me.get().results[0].username != user.username
        with self.current_user(token):
            me = v2.me.get().results[0]
            assert me.username == user.username
