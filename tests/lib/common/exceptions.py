class Common_Exception(Exception):

    def __init__(self, status_string, message=''):
        self.status_string = status_string
        self.message = message

    def __getitem__(self, val):
        return (self.status_string, self.message)[val]

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        try:
            return str(self.message)
        except UnicodeEncodeError:
            return unicode(self.message)


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


class LicenseExceeded_Exception(Common_Exception):

    pass


class LicenseInvalid_Exception(Common_Exception):

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


class Wait_Until_Timeout(Common_Exception):

    pass
