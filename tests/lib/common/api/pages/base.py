import time
import inspect
import httplib
import common.utils
from common.api.pages import Page
# from page import Page
from common.api.schema import validate
import common.exceptions


def json_getter(var):
    '''
    Generic property fget method
    '''
    def get_json(self):
        return getattr(self.json, var)
    return get_json


def json_setter(var):
    '''
    Generic property fset method
    '''
    def set_json(self, value):
        setattr(self.json, var, value)
    return set_json


class Base(Page):
    """
    Base class for global project methods
    """

    base_url = None
    id = property(json_getter('id'), json_setter('id'))

    def __init__(self, *args, **kwargs):
        super(Base, self).__init__(*args)
        self.json = kwargs.get('json', {})
        self.objectify = kwargs.get('objectify', True)

        if kwargs.get('base_url', False):
            self.base_url = kwargs.get('base_url')

    @property
    def __item_class__(self):
        '''Returns the class representing a single 'Base' item'''
        return self.__class__

    def validate_json(self, json=None, request='GET'):
        '''
        Perform JSON validation on JSON response
        '''
        if json is None:
            validate(self.json, self.base_url, request.lower(), version=self.testsetup.request.config.getvalue('api_version'))
            # validate(self.json, self.base_url, request.lower(), version=self.testsetup.api.version)
        else:
            validate(json, self.base_url, request.lower(), version=self.testsetup.request.config.getvalue('api_version'))
            # validate(json, self.base_url, request.lower(), version=self.testsetup.api.version)

    def handle_request(self, r):
        try:
            data = r.json()
        except ValueError:
            '''If there was no json to parse'''
            data = dict()

        exc_str = "%s (%s) received" % (httplib.responses[r.status_code], r.status_code)
        if r.status_code in (httplib.OK, httplib.CREATED, httplib.ACCEPTED):
            self.validate_json(json=data, request=r.request.method)

            # Not all JSON responses include a URL.  Grab it from the request
            # object, if needed.
            if 'url' in data:
                base_url = data['url']
            else:
                base_url = r.request.path_url

            # Also, don't forget to call r.objectify() on the json structure.
            # Without that call, it will simply be a json dictionary.  By calling
            # r.objectify(), it behaves like a classic dictionary, but also is
            # JSON_Wrapped() to allow attribute access (e.g.
            # self.json['username'] == self.username)
            if self.objectify:
                self.json = r.objectify()
            else:
                self.json = r.json()

            # GET requests should return an object of the same type that made
            # the request.  For example, when performing a GET on /api/v1/users,
            # return an object of type 'Users'.  A GET on /api/v1/users/4/
            # would return an object of type 'User'.
            if r.request.method.lower() == 'get':
                return self.__class__(self.testsetup, base_url=base_url, json=self.json)
            # Other requests (POST, PATCH, PUT etc...) always return a singular
            # element.  For example, a POST to /api/v1/users will return a 'User'
            # object.
            else:
                return self.__item_class__(self.testsetup, base_url=base_url, json=self.json)
        elif r.status_code == httplib.NO_CONTENT:
            raise common.exceptions.NoContent_Exception(exc_str)
        elif r.status_code == httplib.NOT_FOUND:
            raise common.exceptions.NotFound_Exception(exc_str)
        elif r.status_code == httplib.FORBIDDEN:
            try:
                self.validate_json(json=data, request='license_exceeded')
            except:
                raise common.exceptions.Forbidden_Exception(exc_str)
            else:
                raise common.exceptions.LicenseExceeded_Exception(exc_str)
        elif r.status_code == httplib.BAD_REQUEST:
            # Validate the 400 BAD_REQUEST response with known 400 errors.
            for (request, exc) in [('license_invalid', common.exceptions.LicenseInvalid_Exception),
                                   ('duplicate', common.exceptions.Duplicate_Exception)]:
                try:
                    self.validate_json(json=data, request=request)
                except:
                    continue
                else:
                    if request == 'duplicate':
                        exc_str += ". However, JSON validation determined the cause " \
                                   "was a duplicate object already exists: %s" % data
                    else:
                        exc_str += ": %s" % data
                    raise exc(exc_str, data)

            # No custom 400 exception was raised, raise a generic 400 BAD_REQUEST exception
            raise common.exceptions.BadRequest_Exception(exc_str + ": %s" % data, data)

        elif r.status_code == httplib.INTERNAL_SERVER_ERROR:
            raise common.exceptions.InternalServerError_Exception(exc_str + ": %s" % data, data)
        elif r.status_code == httplib.METHOD_NOT_ALLOWED:
            raise common.exceptions.Method_Not_Allowed_Exception(exc_str + ": %s" % data, data)
        elif r.status_code == httplib.UNAUTHORIZED:
            raise common.exceptions.Unauthorized_Exception(exc_str + ": %s" % data, data)
        else:
            raise common.exceptions.Unknown_Exception(exc_str + ": %s" % data, data)

    def get(self, **params):
        r = self.api.get(self.base_url.format(**self.json), params=params)
        self.handle_request(r)
        return self

    def post(self, payload={}):
        r = self.api.post(self.base_url, payload)
        return self.handle_request(r)

    def put(self):
        r = self.api.put(self.base_url.format(**self.json), self.json)
        return self.handle_request(r)

    def patch(self, **payload):
        r = self.api.patch(self.base_url.format(**self.json), payload)
        return self.handle_request(r)

    def delete(self):
        r = self.api.delete(self.base_url.format(**self.json))
        try:
            return self.handle_request(r)
        except common.exceptions.NoContent_Exception:
            pass

    def silent_delete(self):
        '''
        Delete the object.  If it's already deleted, ignore the error
        '''
        r = self.api.delete(self.base_url.format(**self.json))
        try:
            return self.handle_request(r)
        except (common.exceptions.NoContent_Exception, common.exceptions.NotFound_Exception):
            pass

    def get_related(self, name, **kwargs):
        assert name in self.json['related']
        return Base(self.testsetup, base_url=self.json['related'][name]).get(**kwargs)


class Base_List(Base):
    '''
    Allow: GET, POST, HEAD, OPTIONS
    '''

    base_url = None

    # Common properties for list objects
    count = property(json_getter('count'), json_setter('count'))
    next = property(json_getter('next'), json_setter('next'))
    previous = property(json_getter('previous'), json_setter('previous'))

    @property
    def __item_class__(self):
        '''Returns the class representing a single 'Base' item'''
        # With an inheritence of Org_List -> Org -> Base -> Page, the following
        # will return the parent class of the current object (e.g. 'Org').
        return inspect.getmro(self.__class__)[1]

    @property
    def results(self):
        return [self.__item_class__(self.testsetup, base_url=data.get('url', None), json=data) for data in self.json['results']]

    def options(self, **kwargs):
        r = self.api.options(self.base_url.format(**self.json))
        return self.handle_request(r)

    def head(self, **kwargs):
        raise NotImplementedError

    def get(self, **params):
        r = self.api.get(self.base_url.format(**self.json), params=params)
        return self.handle_request(r)

    def post(self, payload={}):
        r = self.api.post(self.base_url, payload)
        return self.handle_request(r)

    def go_to_next(self):
        if self.next:
            next_page = self.__class__(self.testsetup, base_url=self.next)
            return next_page.get()

    def go_to_previous(self):
        if self.previous:
            prev_page = self.__class__(self.testsetup, base_url=self.previous)
            return prev_page.get()
