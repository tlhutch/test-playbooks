import re

from towerkit.config import config
import towerkit.exceptions as exc
import fauxfactory
import pytest

from tests.api import APITest


@pytest.mark.api
@pytest.mark.destructive
@pytest.mark.usefixtures('authtoken', 'install_enterprise_license_unlimited')
class TestCredentials(APITest):

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
    def test_v2_ssh_credential_valid_payload_field_integrity(self, factories, v2, input_fields):
        cred_type = v2.credential_types.get(managed_by_tower=True, kind='ssh').results.pop()
        kwargs = {'name': fauxfactory.gen_utf8(), 'description': fauxfactory.gen_utf8()}
        credential = factories.credential(credential_type=cred_type, inputs=input_fields, **kwargs)

        def validate_fields():
            for field in ('name', 'description'):
                assert credential[field] == kwargs[field]
            for field in ('username', 'become_method', 'become_username'):
                assert credential.inputs[field] == input_fields[field]

        validate_fields()
        credential.put()
        validate_fields()

    def test_team_credentials_are_organization_credentials(self, factories, v2):
        """confirm that a team credential's organization is sourced from the team"""
        team_factory = factories.team
        cred_factory = factories.credential

        team = team_factory()
        credential = cred_factory(team=team, organization=None)

        owner_organizations = [item for item in credential.summary_fields.owners if item.get("type") == "organization"]
        assert owner_organizations

        owner_teams = [item for item in credential.summary_fields.owners if item.get("type") == "team"]
        assert owner_teams

        assert owner_organizations[0].get("id") == team.organization

    def test_duplicate_credential_creation(self, request, factories, v2):
        """Confirms that duplicate credentials are allowed when an organization isn't shared (user only)
        and disallowed when one is (including one sourced from a team)
        """
        org1 = factories.organization()
        org2 = factories.organization()
        team = factories.team(organization=org1)
        user1 = factories.user(organization=org1)
        user2 = factories.user(organization=org2)
        # Successfully create two credentials with same name but different user and without an organization
        name = 'duplicate_user_cred_{}'.format(fauxfactory.gen_utf8())
        for user in [user1, user2]:
            factories.credential(user=user, name=name)

        # attempt to create duplicate organization credentials
        name = 'duplicate_org_cred_{}'.format(fauxfactory.gen_utf8())
        factories.credential(name=name, organization=org2)
        with pytest.raises(exc.Duplicate):
            factories.credential(name=name, organization=org2)

        # attempt to create duplicate team (thus organization) credentials
        name = 'duplicate_team_cred_{}'.format(fauxfactory.gen_utf8())
        factories.credential(name=name, team=team)
        with pytest.raises(exc.Duplicate):
            factories.credential(name=name, team=team)

    def test_credential_v2_with_missing_required_field_fails_job_prestart_check(self, request, factories, v2):
        """Confirms that a credential with a missing required field causes the
        job prestart check to fail.
        """
        payload = factories.credential.payload(kind='openstack_v3')
        del payload.inputs['project'] # required for openstack
        cred = v2.credentials.post(payload)
        request.addfinalizer(cred.silent_delete)

        jt = factories.job_template()
        jt.add_credential(cred)
        job = jt.launch().wait_until_completed()

        assert job.status == 'failed'
        assert 'Job cannot start' in job.job_explanation
        assert 'does not provide one or more required fields (project)' in job.job_explanation
        assert 'Task failed pre-start check' in job.job_explanation

    def test_invalid_ssh_key_data_creation_attempt(self, request, factories):

        with pytest.raises(exc.BadRequest) as e:
            factories.credential(kind='ssh', ssh_key_data='NotAnRSAKey')

        error = e.value.msg.get('inputs', e.value.msg)
        assert error == {'ssh_key_data': ['Invalid certificate or key: NotAnRSAKey...']}

    @pytest.mark.parametrize("kind, ssh_key_unlock", [
        ("ssh", "passphrase"),
        ("ssh", "ASK"),
        ("net", "passphrase"),
        ("net", "ASK")
    ], ids=["ssh-passphrase", "ssh-ASK", "net-passphrase", "net-ASK"])
    def test_ssh_key_unlock_with_unencrypted_key_data(self, v2, factories, kind, ssh_key_unlock):
        """Credentials with unencrypted key data should reject both passphrases and passphrase-ASK."""
        user = factories.user()
        payload = factories.credential.payload(kind=kind, user=user, ssh_key_unlock=ssh_key_unlock)

        with pytest.raises(exc.BadRequest) as e:
            v2.credentials.post(payload)
        assert e.value.msg['inputs'] == {'ssh_key_unlock': ['should not be set when SSH key is not encrypted.']}

    @pytest.mark.parametrize('cred_args, scm_url',
                             [[dict(password=''), 'git@github.com:/ansible/tower-qa.git'],
                              [dict(password='', ssh_key_data=config.credentials.scm.encrypted.ssh_key_data,
                                    ssh_key_unlock=config.credentials.scm.encrypted.ssh_key_unlock),
                              'git@github.com:/ansible/tower-qa.git']],
                             ids=['by unencrypted key', 'by encrypted key'])
    def test_scm_credential_with_private_github_repo(self, factories, cred_args, scm_url):
        scm_cred = factories.credential(kind='scm', **cred_args)
        project = factories.project(scm_url=scm_url, credential=scm_cred)
        project.assert_successful()
        assert len(project.related.playbooks.get().json)

    @pytest.mark.parametrize('cred_type', ['Machine', 'Vault'])
    def test_changing_credential_types_only_allowed_for_unused_credentials(self, factories, v2, cred_type):
        cred = factories.credential(kind='insights')
        insights_type_id = cred.credential_type

        cred_type_id = v2.credential_types.get(name=cred_type).results.pop().id
        if cred_type == 'Machine':
            payload = dict(credential_type=cred_type_id)
        else:
            payload = dict(credential_type=cred_type_id, inputs=dict(vault_password='fake'))
        cred.patch(**payload)
        assert cred.credential_type == cred_type_id

        project = factories.project()
        if cred_type == 'Machine':
            factories.job_template(project=project, credential=cred)
        else:
            factories.job_template(project=project, vault_credential=cred.id)

        with pytest.raises(exc.BadRequest) as e:
            cred.credential_type = insights_type_id
        assert "You cannot change the credential type of the credential" in e.value[1]['credential_type'][0]
        assert cred.credential_type == cred_type_id

    def test_changing_extra_credential_types_only_allowed_for_unused_credentials(self, factories, v2):
        cred = factories.credential(kind='aws')
        aws_type_id = cred.credential_type

        jt = factories.job_template()
        jt.add_extra_credential(cred)

        machine_type_id = v2.credential_types.get(name='Machine').results.pop().id

        with pytest.raises(exc.BadRequest) as e:
            cred.credential_type = machine_type_id
        assert "You cannot change the credential type of the credential" in e.value[1]['credential_type'][0]
        assert cred.credential_type == aws_type_id

    def test_confirm_boto_exception_in_ec2_inv_sync_without_credential(self, factories):
        inv_source = factories.inventory_source(source='ec2')
        assert not inv_source.credential
        update = inv_source.update().wait_until_completed()
        assert update.failed
        assert ('NoAuthHandlerFound' in update.result_stdout) or ('Insufficient boto credentials found' in update.result_stdout)

    @pytest.mark.mp_group(group="get_pg_dump", strategy="serial")
    def test_confirm_no_plaintext_secrets_in_db(self, skip_if_cluster, v2, factories, get_pg_dump):
        cred_payloads = [factories.credential.payload(kind=k) for k in ('aws', 'azure_rm', 'gce', 'net', 'ssh')]
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

    @pytest.mark.mp_group(group="get_pg_dump", strategy="serial")
    def test_confirm_desired_encryption_schemes_in_db(self, skip_if_cluster, v2, factories, get_pg_dump):
        for kind in ('aws', 'azure_rm', 'gce', 'net', 'ssh'):
            factories.credential(kind=kind)

        encrypted_content_pat = re.compile(r'\$encrypted\$[a-zA-Z0-9$]*=*')
        encrypted_content = encrypted_content_pat.findall(get_pg_dump())
        assert encrypted_content

        def is_of_desired_form(encrypted_string):
            return any([encrypted_string.startswith(pref) for pref in ('$encrypted$UTF8$AESCBC$', '$encrypted$AESCBC$')]) \
                   or encrypted_string == '$encrypted$'

        for item in encrypted_content:
            assert is_of_desired_form(item)
