from common.api import resources
import base


class Credential(base.Base):

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

base.register_page(resources.v1_credential, Credential)


class Credentials(Credential, base.BaseList):

    pass

base.register_page([resources.v1_credentials,
                    resources.v1_related_credentials], Credentials)

# backwards compatibility
Credential_Page = Credential
Credentials_Page = Credentials
