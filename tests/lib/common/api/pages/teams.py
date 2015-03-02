import base
from users import Users_Page


class Team_Page(base.Base):
    # FIXME - it would be nice for base_url to always return self.json.url.
    base_url = '/api/v1/teams/{id}/'
    name = property(base.json_getter('name'), base.json_setter('name'))
    type = property(base.json_getter('type'), base.json_setter('type'))
    description = property(base.json_getter('description'), base.json_setter('description'))
    organization = property(base.json_getter('organization'), base.json_setter('organization'))

    def get_related(self, name, **kwargs):
        assert name in self.json['related']
        related_cls = None
        if name == 'users':
            related_cls = Users_Page
        elif name == 'organization':
            from organizations import Organization_Page
            related_cls = Organization_Page
        elif name == 'credentials':
            from credentials import Credentials_Page
            related_cls = Credentials_Page
        elif name == 'permissions':
            from permissions import Permissions_Page
            related_cls = Permissions_Page
        else:
            raise NotImplementedError
        related = related_cls(self.testsetup, base_url=self.json['related'][name])
        return related.get(**kwargs)


class Teams_Page(Team_Page, base.Base_List):
    base_url = '/api/v1/teams/'
