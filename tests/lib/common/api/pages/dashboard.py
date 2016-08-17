from common.api import resources
import base


class Dashboard_Page(base.Base):

    pass

base.register_page(resources.v1_dashboard, Dashboard_Page)
