from base64 import b64decode
import logging
import re
import os

from towerkit.config import config
import towerkit.exceptions as exc
import fauxfactory
import pytest

from tests.api import Base_Api_Test


@pytest.mark.api
@pytest.mark.skip_selenium
@pytest.mark.destructive
@pytest.mark.usefixtures('authtoken', 'install_enterprise_license_unlimited')
class TestCredentials(Base_Api_Test):

    def test_credential_creation_attempt_with_invalid_kind(self, v1, factories):
        payload = factories.credential.payload()
        payload['kind'] = 'invalid_kind'

        with pytest.raises(exc.BadRequest) as e:
            v1.credentials.post(payload)
        assert e.value.message == {'kind': ['"invalid_kind" is not a valid choice']}

    @pytest.mark.parametrize('fields', [dict(name=fauxfactory.gen_utf8(),
                                             description=fauxfactory.gen_utf8(),
                                             username=fauxfactory.gen_alphanumeric(),
                                             password=fauxfactory.gen_utf8(),
                                             ssh_key_data=config.credentials.ssh.ssh_key_data,
                                             ssh_key_unlock='',
                                             become_method="sudo",
                                             become_username=fauxfactory.gen_alphanumeric(),
                                             become_password=fauxfactory.gen_utf8()),
                                        dict(name=fauxfactory.gen_utf8(),
                                             description='',
                                             username=fauxfactory.gen_alphanumeric(),
                                             password=fauxfactory.gen_utf8(),
                                             ssh_key_data='',
                                             ssh_key_unlock='',
                                             become_method="sudo",
                                             become_username=fauxfactory.gen_alphanumeric(),
                                             become_password=fauxfactory.gen_utf8()),
                                        dict(name=fauxfactory.gen_utf8(),
                                             description='',
                                             username='',
                                             password='',
                                             ssh_key_data='',
                                             ssh_key_unlock='',
                                             become_method='',
                                             become_username='',
                                             become_password='')])
    def test_v1_ssh_credential_valid_payload_field_integrity(self, request, factories, v1, fields):
        payload = factories.credential.payload(kind='ssh', **fields)
        credential = v1.credentials.post(payload)
        request.addfinalizer(credential.silent_delete)

        def validate_fields():
            for field in ('name', 'description', 'username', 'become_method', 'become_username'):
                assert credential[field] == payload[field]

        validate_fields()
        credential.put()
        validate_fields()

    @pytest.mark.parametrize('input_fields', [dict(username=fauxfactory.gen_alphanumeric(),
                                                   password=fauxfactory.gen_utf8(),
                                                   ssh_key_data=config.credentials.ssh.ssh_key_data,
                                                   ssh_key_unlock='',
                                                   become_method="sudo",
                                                   become_username=fauxfactory.gen_alphanumeric(),
                                                   become_password=fauxfactory.gen_utf8()),
                                              dict(username=fauxfactory.gen_alphanumeric(),
                                                   password=fauxfactory.gen_utf8(),
                                                   ssh_key_data='',
                                                   ssh_key_unlock='',
                                                   become_method="sudo",
                                                   become_username=fauxfactory.gen_alphanumeric(),
                                                   become_password=fauxfactory.gen_utf8()),
                                              dict(username='',
                                                   password='',
                                                   ssh_key_data='',
                                                   ssh_key_unlock='',
                                                   become_method='',
                                                   become_username='',
                                                   become_password='')])
    def test_v2_ssh_credential_valid_payload_field_integrity(self, request, factories, v2, input_fields):
        cred_type = v2.credential_types.get(managed_by_tower=True, kind='ssh').results.pop()
        payload = factories.v2_credential.payload(name=fauxfactory.gen_utf8(),
                                                  description=fauxfactory.gen_utf8(),
                                                  credential_type=cred_type,
                                                  inputs=input_fields)
        credential = v2.credentials.post(payload)
        request.addfinalizer(credential.silent_delete)

        def validate_fields():
            for field in ('name', 'description'):
                assert credential[field] == payload[field]
            for field in ('username', 'become_method', 'become_username'):
                assert credential.inputs[field] == payload.inputs[field]

        validate_fields()
        credential.put()
        validate_fields()

    @pytest.mark.parametrize('v', ('v1', 'v2'))
    def test_team_credentials_are_organization_credentials(self, factories, v):
        """confirm that a team credential's organization is sourced from the team"""
        team_factory = getattr(factories, 'team' if v == 'v1' else 'v2_team')
        cred_factory = getattr(factories, 'credential' if v == 'v1' else 'v2_credential')

        team = team_factory()
        credential = cred_factory(team=team, organization=None)

        owner_organizations = [item for item in credential.summary_fields.owners if item.get("type") == "organization"]
        assert owner_organizations

        owner_teams = [item for item in credential.summary_fields.owners if item.get("type") == "team"]
        assert owner_teams

        assert owner_organizations[0].get("id") == team.organization

    @pytest.mark.parametrize('v', ('v1', 'v2'))
    def test_duplicate_credential_creation(self, request, factories, v):
        """Confirms that duplicate credentials are allowed when an organization isn't shared (user only)
        and disallowed when one is (including one sourced from a team)
        """
        version = request.getfixturevalue(v)
        user_factory = getattr(factories, 'user' if v == 'v1' else 'v2_user')
        team_factory = getattr(factories, 'team' if v == 'v1' else 'v2_team')
        cred_factory = getattr(factories, 'credential' if v == 'v1' else 'v2_credential')

        # Successfully create duplicate user credentials without an organization
        payload = cred_factory.payload(user=user_factory(), organization=None)
        for _ in range(2):
            cred = version.credentials.post(payload)
            request.addfinalizer(cred.silent_delete)

        # attempt to create duplicate organization credentials
        payload = cred_factory.payload()
        cred = version.credentials.post(payload)
        request.addfinalizer(cred.silent_delete)
        with pytest.raises(exc.Duplicate):
            version.credentials.post(payload)

        # attempt to create duplicate team (thus organization) credentials
        payload = cred_factory.payload(team=team_factory(), organization=None)
        cred = version.credentials.post(payload)
        request.addfinalizer(cred.silent_delete)
        with pytest.raises(exc.Duplicate):
            version.credentials.post(payload)

    @pytest.mark.parametrize("missing, expected_message",
                             [('project', {"project": ["required for OpenStack"]}),
                              ('password', {"password": ["required for OpenStack"]}),
                              ('username', {"username": ["required for OpenStack"]}),
                              ('host', {"host": ["required for OpenStack"]})],
                             ids=['project', 'password', 'username', 'host'])
    def test_invalid_v1_openstack_credential(self, factories, v1, missing, expected_message):
        """Confirms that attempted openstack credential creation fails if missing required field"""
        payload = factories.credential.payload(kind='openstack')
        del payload[missing]

        with pytest.raises(exc.BadRequest) as e:
            v1.credentials.post(payload)

        assert e.value.message == expected_message

    @pytest.fixture(scope='class')
    def openstack_credential_type(self, v2_class):
        return v2_class.credential_types.get(name__icontains='openstack', managed_by_tower=True).results.pop()

    @pytest.mark.parametrize("missing, expected_message",
                             [('project', {"project": ["required for OpenStack"]}),
                              ('password', {"password": ["required for OpenStack"]}),
                              ('username', {"username": ["required for OpenStack"]}),
                              ('host', {"host": ["required for OpenStack"]})],
                             ids=['project', 'password', 'username', 'host'])
    def test_invalid_v2_openstack_credential(self, factories, v2, openstack_credential_type, missing, expected_message):
        """Confirms that attempted openstack credential creation fails if missing required field"""
        payload = factories.v2_credential.payload(credential_type=openstack_credential_type)
        del payload.inputs[missing]

        with pytest.raises(exc.BadRequest) as e:
            v2.credentials.post(payload)

        assert e.value.message['inputs'] == expected_message

    @pytest.mark.parametrize('version', ('v1', 'v2'))
    def test_invalid_ssh_key_data_creation_attempt(self, request, factories, version):
        v = request.getfixturevalue(version)
        cred_factory = factories.credential if version == 'v1' else factories.v2_credential
        payload = cred_factory.payload(kind='ssh', ssh_key_data='NotAnRSAKey')

        with pytest.raises(exc.BadRequest) as e:
            v.credentials.post(payload)
        error = e.value.message.get('inputs', e.value.message)
        assert error == {'ssh_key_data': ['Invalid certificate or key: NotAnRSAKey...']}

    @pytest.mark.parametrize("kind, ssh_key_unlock", [
        ("ssh", "passphrase"),
        ("ssh", "ASK"),
        ("net", "passphrase"),
        ("net", "ASK")
    ], ids=["ssh-passphrase", "ssh-ASK", "net-passphrase", "net-ASK"])
    def test_ssh_key_unlock_with_unencrypted_key_data(self, v2, factories, kind, ssh_key_unlock):
        """Credentials with unencrypted key data should reject both passphrases and passphrase-ASK."""
        user = factories.v2_user()
        payload = factories.v2_credential.payload(kind=kind, user=user, ssh_key_unlock=ssh_key_unlock)

        with pytest.raises(exc.BadRequest) as e:
            v2.credentials.post(payload)
        assert e.value.message['inputs'] == {'ssh_key_unlock': ['should not be set when SSH key is not encrypted.']}

    @pytest.mark.parametrize('cred_args, scm_url',
                             [[dict(password=''), 'git@github.com:/ansible/tower-qa.git'],
                              [dict(password='', ssh_key_data=config.credentials.scm.encrypted.ssh_key_data,
                                    ssh_key_unlock=config.credentials.scm.encrypted.ssh_key_unlock),
                              'git@github.com:/ansible/tower-qa.git']],
                             ids=['by unencrypted key', 'by encrypted key'])
    def test_scm_credential_with_private_github_repo(self, factories, cred_args, scm_url):
        scm_cred = factories.v2_credential(kind='scm', **cred_args)
        project = factories.v2_project(scm_url=scm_url, credential=scm_cred)
        assert project.is_successful
        assert len(project.related.playbooks.get().json)

    def test_changing_credential_types_only_allowed_for_unused_credentials(self, factories, v2):
        cred = factories.v2_credential(kind='insights')
        insights_type_id = cred.credential_type

        machine_type_id = v2.credential_types.get(name='Machine').results.pop().id
        cred.credential_type = machine_type_id
        assert cred.credential_type == machine_type_id

        project = factories.v2_project()
        factories.v2_job_template(project=project, credential=cred)

        with pytest.raises(exc.BadRequest) as e:
            cred.credential_type = insights_type_id
        assert "You cannot change the credential type of the credential" in e.value[1]['credential_type'][0]

    def test_confirm_boto_exception_in_ec2_inv_sync_without_credential(self, factories):
        inv_source = factories.v2_inventory_source(source='ec2')
        assert not inv_source.credential
        update = inv_source.update().wait_until_completed()
        assert update.failed
        assert 'NoAuthHandlerFound' in update.result_stdout

    @pytest.fixture
    def get_pg_dump(self, request, ansible_runner, is_docker):
        if is_docker:
            pytest.skip('Test not compatible w/o access to db container.')

        def _pg_dump():
            inv_path = os.environ.get('TQA_INVENTORY_FILE_PATH', '/tmp/setup/inventory')
            contacted = ansible_runner.shell("""PGPASSWORD=`grep {} -e "pg_password=.*" """
                                             """| sed \'s/pg_password="//\' | sed \'s/"//\'` """
                                             """pg_dump -U awx -d awx -f pg.txt -w""".format(inv_path))
            for res in contacted.values():
                assert res.get('changed') and not res.get('failed')

            user = ansible_runner.options['user'] \
                   or ansible_runner.inventory_manager.get_vars(ansible_runner.options['host_pattern'])['ansible_user']
            pg_dump_path = '/home/{0}/pg.txt'.format(user)
            request.addfinalizer(lambda: ansible_runner.file(path=pg_dump_path, state='absent'))

            # Don't log the dumped db.
            pa_logger = logging.getLogger('pytest_ansible')
            prev_level = pa_logger.level
            pa_logger.setLevel('INFO')
            restored = [False]

            def restore_log_level():
                if not restored[0]:
                    pa_logger.setLevel(prev_level)
                    restored[0] = True

            request.addfinalizer(restore_log_level)

            contacted = ansible_runner.slurp(src=pg_dump_path)
            restore_log_level()

            res = contacted.values().pop()

            assert not res.get('failed') and res['content']
            return b64decode(res['content'])

        return _pg_dump

    @pytest.mark.requires_single_instance
    def test_confirm_no_plaintext_secrets_in_db(self, v2, factories, get_pg_dump):
        cred_payloads = [factories.v2_credential.payload(kind=k) for k in ('aws', 'azure_rm', 'gce', 'net', 'ssh')]
        secrets = set()
        for payload in cred_payloads:
            for field in ('password', 'ssh_key_data', 'authorize_password', 'become_password', 'secret'):
                if payload.inputs.get(field, False):
                    secrets.add(payload.inputs[field])
            v2.credentials.post(payload)

        pg_dump = get_pg_dump()

        undesired_locations = []
        for secret in secrets:
            try:
                undesired_locations.append(pg_dump.index(secret))
            except ValueError:
                pass

        if undesired_locations:
            locations = '\n'.join(pg_dump[location - 200:location + 200] for location in undesired_locations)
            pytest.fail('Found plaintext secret in db: {}'.format(locations))

    @pytest.mark.requires_single_instance
    def test_confirm_desired_encryption_schemes_in_db(self, v2, factories, get_pg_dump):
        for kind in ('aws', 'azure_rm', 'gce', 'net', 'ssh'):
            factories.v2_credential(kind=kind)

        encrypted_content_pat = re.compile('\$encrypted\$[a-zA-Z0-9$]*=*')
        encrypted_content = encrypted_content_pat.findall(get_pg_dump())
        assert encrypted_content

        def is_of_desired_form(encrypted_string):
            return any([encrypted_string.startswith(pref) for pref in ('$encrypted$UTF8$AESCBC$', '$encrypted$AESCBC$')]) \
                   or encrypted_string == '$encrypted$'

        for item in encrypted_content:
            assert is_of_desired_form(item)
