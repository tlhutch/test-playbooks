import base


class Ping_Page(base.Base):
    base_url = '/api/v1/ping/'
    role = property(base.json_getter('role'), base.json_setter('role'))
    ha = property(base.json_getter('ha'), base.json_setter('ha'))
    version = property(base.json_getter('version'), base.json_setter('version'))
    instances = property(base.json_getter('instances'), base.json_setter('instances'))
