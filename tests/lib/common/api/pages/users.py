import base


class User_Page(base.Base):
    # FIXME - it would be nice for base_url to always return self.json.url.
    base_url = '/api/v1/users/{id}/'
    username = property(base.json_getter('username'), base.json_setter('username'))
    first_name = property(base.json_getter('first_name'), base.json_setter('first_name'))
    last_name = property(base.json_getter('last_name'), base.json_setter('last_name'))
    is_superuser = property(base.json_getter('is_superuser'), base.json_setter('is_superuser'))
    email = property(base.json_getter('email'), base.json_setter('email'))

    def get_related(self, name, **kwargs):
        assert name in self.json['related']
        if name == 'credentials':
            from credentials import Credentials_Page
            related = Credentials_Page(self.testsetup, base_url=self.json['related'][name])
        elif name == 'permissions':
            from permissions import Permissions_Page
            related = Permissions_Page(self.testsetup, base_url=self.json['related'][name])
        elif name in ('organizations', 'admin_of_organizations'):
            from organizations import Organizations_Page
            related = Organizations_Page(self.testsetup, base_url=self.json['related'][name])
        else:
            raise NotImplementedError
        return related.get(**kwargs)


class Users_Page(User_Page, base.Base_List):
    base_url = '/api/v1/users/'


class Me_Page(Users_Page):
    base_url = '/api/v1/me/'
