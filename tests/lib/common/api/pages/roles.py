import base


class Role_Page(base.Base):
    # FIXME - it would be nice for base_url to always return self.json.url.
    base_url = '/api/v1/roles/{id}/'
    type = property(base.json_getter('type'), base.json_setter('type'))
    created = property(base.json_getter('created'), base.json_setter('created'))
    modified = property(base.json_getter('modified'), base.json_setter('modified'))
    name = property(base.json_getter('name'), base.json_setter('name'))
    description = property(base.json_getter('description'), base.json_setter('description'))

    def get_related(self, attr, **kwargs):
        assert attr in self.json['related'], \
            "No such related attribute '%s'" % attr

        if attr == 'users':
            from users import Users_Page as cls
        elif attr == 'teams':
            from teams import Teams_Page as cls
        elif attr == 'user':
            from users import User_Page as cls
        else:
            raise NotImplementedError("No related class found for '%s'" % attr)

        return cls(self.testsetup, base_url=self.json['related'][attr]).get(**kwargs)


class Roles_Page(Role_Page, base.Base_List):
    base_url = '/api/v1/roles/'
