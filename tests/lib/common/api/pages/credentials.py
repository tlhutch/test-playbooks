import base


class Credential_Page(base.Base):
    # FIXME - it would be nice for base_url to always return self.json.url.
    base_url = '/api/v1/credentials/{id}/'
    name = property(base.json_getter('name'), base.json_setter('name'))
    type = property(base.json_getter('type'), base.json_setter('type'))
    description = property(base.json_getter('description'), base.json_setter('description'))
    kind = property(base.json_getter('kind'), base.json_setter('kind'))
    user = property(base.json_getter('user'), base.json_setter('user'))
    team = property(base.json_getter('team'), base.json_setter('team'))
    password = property(base.json_getter('password'), base.json_setter('password'))
    become_method = property(base.json_getter('become_method'), base.json_setter('become_method'))
    become_username = property(base.json_getter('become_username'), base.json_setter('become_username'))
    become_password = property(base.json_getter('become_password'), base.json_setter('become_password'))
    ssh_key_unlock = property(base.json_getter('ssh_key_unlock'), base.json_setter('ssh_key_unlock'))
    vault_password = property(base.json_getter('vault_password'), base.json_setter('vault_password'))

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


class Credentials_Page(Credential_Page, base.Base_List):
    base_url = '/api/v1/credentials/'
