import base
from users import Users_Page
from common.exceptions import *

class Team_Page(base.Base):
    # FIXME - it would be nice for base_url to always return self.json.url.
    base_url = '/api/v1/teams/{id}/'
    name = property(base.json_getter('name'), base.json_setter('name'))
    description = property(base.json_getter('description'), base.json_setter('description'))

    def get_related(self, name, **kwargs):
        assert name in self.json['related']
        if name == 'users':
            related = Users_Page(self.testsetup, base_url=self.json['related'][name])
        elif name == 'credentials':
            from credentials import Credentials_Page
            related = Credentials_Page(self.testsetup, base_url=self.json['related'][name])
        elif name == 'permissions':
            from permissions import Permissions_Page
            related = Permissions_Page(self.testsetup, base_url=self.json['related'][name])
        else:
            raise NotImplementedError
        return related.get(**kwargs)

class Teams_Page(Team_Page, base.Base_List):
    base_url = '/api/v1/teams/'
