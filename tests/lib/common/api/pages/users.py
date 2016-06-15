import base


class User_Page(base.Base):
    # FIXME - it would be nice for base_url to always return self.json.url.
    base_url = '/api/v1/users/{id}/'
    type = property(base.json_getter('type'), base.json_setter('type'))
    username = property(base.json_getter('username'), base.json_setter('username'))
    first_name = property(base.json_getter('first_name'), base.json_setter('first_name'))
    last_name = property(base.json_getter('last_name'), base.json_setter('last_name'))
    is_superuser = property(base.json_getter('is_superuser'), base.json_setter('is_superuser'))
    email = property(base.json_getter('email'), base.json_setter('email'))

    def get_related(self, attr, **kwargs):
        assert attr in self.json['related'], \
            "No such related attribute '%s'" % attr

        if attr == 'credentials':
            from credentials import Credentials_Page as cls
        elif attr in ('organizations', 'admin_of_organizations'):
            from organizations import Organizations_Page as cls
        elif attr == 'teams':
            from teams import Teams_Page as cls
        elif attr == 'access_list':
            from access_list import Access_List_Page as cls
        elif attr == 'roles':
            from roles import Roles_Page as cls
        elif attr == 'activity_stream':
            from activity_stream import Activity_Stream_Page as cls
        elif attr == 'projects':
            from projects import Projects_Page as cls
        else:
            raise NotImplementedError("No related class found for '%s'" % attr)

        return cls(self.testsetup, base_url=self.json['related'][attr]).get(**kwargs)


class Users_Page(User_Page, base.Base_List):
    base_url = '/api/v1/users/'


class Me_Page(Users_Page):
    base_url = '/api/v1/me/'
