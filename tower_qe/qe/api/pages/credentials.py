import os

from Crypto.PublicKey import RSA
import fauxfactory

from qe.api.pages import Organization, User, Team
from qe.utils import update_payload
from qe.api import resources
from qe.config import config

import base


class Credential(base.Base):

    dependencies = [Organization]

    @property
    def expected_passwords_needed_to_start(self):
        '''Return a list of expected passwords needed to start a job using this credential.'''
        passwords = []
        for field in ('password', 'become_password', 'ssh_key_unlock', 'vault_password'):
            if getattr(self, field) == 'ASK':
                if field == 'password':
                    passwords.append('ssh_password')
                else:
                    passwords.append(field)
        return passwords

    def create(self, kind='ssh', name='', description='', user=None, team=None, organization=None, **kw):
        """creates a new credential owned by either a user, team, and/or organization.  If you'd like to have
           `create()` establish a new user, team, or (default) organization specify w/ True.
           Defaults to new organization.
           ```qe.api.Credential().create(user=True)```
           ```qe.api.Credential().create(user=True, team=Team)```
        """
        if not any((user, team, organization)):
            organization = Organization

        if organization:  # conditional dependency so we expose what we create/consume
            self.create_and_update_dependencies(organization)

        payload = dict(kind=kind, name=name or 'Credential - {}'.format(fauxfactory.gen_alphanumeric()),
                       description=description or fauxfactory.gen_utf8())

        def id_or_instance(obj, cls):
            if isinstance(obj, str) or (not isinstance(obj, bool) and isinstance(obj, int)):
                return obj
            elif isinstance(obj, cls):
                return obj.id
            else:
                return cls(self.testsetup).create().id

        if user:
            payload['user'] = id_or_instance(user, User)
        if team:
            payload['team'] = id_or_instance(team, Team)
        if organization:
            payload['organization'] = self.dependency_store[Organization].id

        config_cred_key = "network" if kind == 'net' else kind
        payload['username'] = kw.get('username', config.credentials[config_cred_key].username)
        payload['password'] = kw.get('password', config.credentials[config_cred_key].password)

        if kind in ('ssh', 'net'):
            payload['ssh_key_data'] = kw.get('ssh_key_data', RSA.generate(2048, os.urandom).exportKey('PEM'))

        fields = ('ssh_key_unlock', 'vault_password', 'become_method', 'become_username', 'become_password')
        payload = update_payload(payload, fields, kw)

        return self.update_identity(Credentials(self.testsetup).post(payload))

base.register_page(resources.v1_credential, Credential)


class Credentials(base.BaseList, Credential):

    pass

base.register_page([resources.v1_credentials,
                    resources.v1_related_credentials], Credentials)

# backwards compatibility
Credential_Page = Credential
Credentials_Page = Credentials
