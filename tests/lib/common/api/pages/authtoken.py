from common.api.pages import Base, json_getter, json_setter


class AuthToken_Page(Base):
    base_url = '/api/v1/authtoken/'
    token = property(json_getter('token'), json_setter('token'))
    expires = property(json_getter('expires'), json_setter('expires'))
