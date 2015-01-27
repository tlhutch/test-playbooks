import base


class Activity_Page(base.Base):
    base_url = '/api/v1/activity_stream/{id}/'
    operation = property(base.json_getter('operation'), base.json_setter('operation'))


class Activity_Stream_Page(Activity_Page, base.Base_List):
    base_url = '/api/v1/activity_stream/'
