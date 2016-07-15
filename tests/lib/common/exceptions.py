class Common_Exception(Exception):

    def __init__(self, status_string, data=''):
        self.message = data


class BadRequest_Exception(Common_Exception):
    pass


class Conflict_Exception(Common_Exception):
    pass


class Duplicate_Exception(Common_Exception):
    pass


class Forbidden_Exception(Common_Exception):
    pass


class InternalServerError_Exception(Common_Exception):
    pass


class LicenseInvalid_Exception(Common_Exception):
    pass


class LicenseExceeded_Exception(Common_Exception):
    pass


class Method_Not_Allowed_Exception(Common_Exception):
    pass


class NoContent_Exception(Common_Exception):

    message = ''


class NotFound_Exception(Common_Exception):
    pass


class PaymentRequired_Exception(Common_Exception):
    pass


class Unauthorized_Exception(Common_Exception):
    pass


class Unknown_Exception(Common_Exception):
    pass
