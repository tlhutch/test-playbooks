import base
from common.exceptions import *

class Credential_Page(base.Base):
    # FIXME - it would be nice for base_url to always return self.json.url.
    base_url = '/api/v1/credentials/{id}/'
    name = property(base.json_getter('name'), base.json_setter('name'))
    description = property(base.json_getter('description'), base.json_setter('description'))

class Credentials_Page(Credential_Page, base.Base_List):
    base_url = '/api/v1/credentials/'
