from common.api import resources
import base


class AuthToken_Page(base.Base):

    pass

base.register_page(resources.v1_authtoken, AuthToken_Page)
