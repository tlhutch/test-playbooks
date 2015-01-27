import base


class Credential_Page(base.Base):
    # FIXME - it would be nice for base_url to always return self.json.url.
    base_url = '/api/v1/credentials/{id}/'
    name = property(base.json_getter('name'), base.json_setter('name'))
    description = property(base.json_getter('description'), base.json_setter('description'))
    kind = property(base.json_getter('kind'), base.json_setter('kind'))
    user = property(base.json_getter('user'), base.json_setter('user'))
    team = property(base.json_getter('team'), base.json_setter('team'))


class Credentials_Page(Credential_Page, base.Base_List):
    base_url = '/api/v1/credentials/'
