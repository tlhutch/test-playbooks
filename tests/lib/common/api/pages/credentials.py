import base


class Credential_Page(base.Base):
    # FIXME - it would be nice for base_url to always return self.json.url.
    base_url = '/api/v1/credentials/{id}/'
    name = property(base.json_getter('name'), base.json_setter('name'))
    type = property(base.json_getter('type'), base.json_setter('type'))
    description = property(base.json_getter('description'), base.json_setter('description'))
    domain = property(base.json_getter('domain'), base.json_setter('domain'))
    kind = property(base.json_getter('kind'), base.json_setter('kind'))
    user = property(base.json_getter('user'), base.json_setter('user'))
    team = property(base.json_getter('team'), base.json_setter('team'))
    password = property(base.json_getter('password'), base.json_setter('password'))
    become_method = property(base.json_getter('become_method'), base.json_setter('become_method'))
    become_username = property(base.json_getter('become_username'), base.json_setter('become_username'))
    become_password = property(base.json_getter('become_password'), base.json_setter('become_password'))
    ssh_key_unlock = property(base.json_getter('ssh_key_unlock'), base.json_setter('ssh_key_unlock'))
    vault_password = property(base.json_getter('vault_password'), base.json_setter('vault_password'))
    summary_fields = property(base.json_getter('summary_fields'), base.json_setter('summary_fields'))

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

    def get_related(self, attr, **kwargs):
        assert attr in self.json['related'], \
            "No such related attribute '%s'" % attr
        if attr in ['created_by', 'modified_by', 'user']:
            from users import User_Page
            cls = User_Page
        elif attr == 'object_roles':
            from roles import Roles_Page
            cls = Roles_Page
        elif attr == 'access_list':
            from access_list import Access_List_Page
            cls = Access_List_Page
        elif attr == 'activity_stream':
            from activity_stream import Activity_Stream_Page
            cls = Activity_Stream_Page
        elif attr == 'owner_teams':
            from teams import Teams_Page
            cls = Teams_Page
        elif attr == 'owner_users':
            from users import Users_Page
            cls = Users_Page
        elif attr == 'organization':
            from organizations import Organization_Page
            cls = Organization_Page
        elif attr == 'user':
            from users import User_Page
            cls = User_Page
        elif attr == 'team':
            from teams import Team_Page
            cls = Team_Page
        else:
            raise NotImplementedError("No related class found for '%s'" % attr)

        return cls(self.testsetup, base_url=self.json['related'][attr]).get(**kwargs)


class Credentials_Page(Credential_Page, base.Base_List):
    base_url = '/api/v1/credentials/'
