from common.api.pages import Base, Base_List, json_getter, json_setter


class Setting_Page(Base):
    base_url = '/api/v1/settings/'
    key = property(json_getter('key'), json_setter('key'))
    description = property(json_getter('description'), json_setter('description'))
    category = property(json_getter('category'), json_setter('category'))
    value = property(json_getter('value'), json_setter('value'))
    value_type = property(json_getter('value_type'), json_setter('value_type'))
    user = property(json_getter('user'), json_setter('user'))


class Settings_Page(Setting_Page, Base_List):
    base_url = '/api/v1/settings/'
