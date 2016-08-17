from common.api import resources
import base


class Ping_Page(base.Base):

    pass

base.register_page(resources.v1_ping, Ping_Page)
