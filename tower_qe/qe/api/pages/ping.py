from qe.api import resources
import base


class Ping(base.Base):

    pass

base.register_page(resources.v1_ping, Ping)

# backwards compatibility
Ping_Page = Ping
