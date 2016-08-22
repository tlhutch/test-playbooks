from common.api import resources
import base


class ApiV1(base.Base):

    pass

base.register_page(resources.v1, ApiV1)
