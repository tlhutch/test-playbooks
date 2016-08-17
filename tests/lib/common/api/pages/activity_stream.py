from common.api import resources
import base


class Activity_Page(base.Base):

    pass

base.register_page(resources.v1_activity, Activity_Page)


class Activity_Stream_Page(Activity_Page, base.Base_List):

    pass

base.register_page([resources.v1_activity_stream,
                    resources.v1_object_activity_stream], Activity_Stream_Page)
