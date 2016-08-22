from common.api import resources
import base


class AuthToken(base.Base):

    pass

base.register_page(resources.v1_authtoken, AuthToken)

# backwards compatibility
AuthToken_Page = AuthToken
