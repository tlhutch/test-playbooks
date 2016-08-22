from common.api import resources
import base


class Dashboard(base.Base):

    pass

base.register_page(resources.v1_dashboard, Dashboard)

# backwards compatibility
Dashboard_Page = Dashboard
