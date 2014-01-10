import inspect
import httplib
from page import Page, PageRegion
from common.api.schema import validate
from common.exceptions import *

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

        if kwargs.get('base_url', False):
            self.base_url = kwargs.get('base_url')

    def validate_json(self, json=None, request='GET'):
        '''
        Perform JSON validation on JSON response
        '''
        if json is None:
            validate(self.json, self.base_url, request.lower())
        else:
            validate(json, self.base_url, request.lower())

    def get(self, **params):
        ''' disables json validation '''
        r = self.api.get(self.base_url.format(**self.json), params=params)
        assert r.status_code == httplib.OK
        self.json = r.objectify()
        # TODO - validate schema
        #self.validate_json('get')
        return self

    def post(self, payload={}):
        r = self.api.post(self.base_url, payload)
        try:
            data = r.json()
        except ValueError, e:
            '''If there was no json to parse'''
            data = dict()

        exc_str = "%s (%s) received" % (httplib.responses[r.status_code], r.status_code)
        if r.status_code in (httplib.OK, httplib.CREATED, httplib.ACCEPTED):
            self.validate_json(json=data, request='post')
            # FIXME - this should return a populated object
            # return self.__class__(self.testsetup, base_url=data['url'], json=data)
            return self.__class__(self.testsetup, base_url=data['url'], json=r.objectify())
        elif r.status_code == httplib.NO_CONTENT:
            raise NoContent_Exception(exc_str)
        elif r.status_code == httplib.FORBIDDEN:
            raise Forbidden_Exception(exc_str)
        elif r.status_code == httplib.BAD_REQUEST:
            # Attempt to validate the json response.  If it validates against a
            # 'duplicate' method, then we return a Duplicate_Exception.  If
            # validation fails, raise BadRequest_Exception.
            try:
                self.validate_json(json=data, request='duplicate')
            except:
                raise BadRequest_Exception(exc_str + ": %s" % data)
            else:
                raise Duplicate_Exception(exc_str + ". However, JSON validation determined the cause was a duplicate object already exists: %s" % data)
        else:
            raise Unknown_Exception(exc_str + ": %s" % data)

    def put(self):
        r = self.api.put(self.base_url.format(**self.json), self.json)
        assert r.status_code == httplib.OK
        self.json = r.objectify()
        # TODO - validate schema
        #self.validate_json('put')

    def patch(self, **payload):
        r = self.api.patch(self.base_url.format(**self.json), payload)
        assert r.status_code == httplib.OK
        self.json = r.objectify()
        # TODO - validate schema
        #self.validate_json('patch')

    def delete(self):
        r = self.api.delete(self.base_url.format(**self.json))
        assert r.status_code == httplib.NO_CONTENT

    def get_related(self, name):
        assert name in self.json['related']
        return Base(self.testsetup, base_url=self.json['related'][name]).get()

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
    def results(self):
        return [self.__parent__(self.testsetup, base_url=data.get('url',None), json=data) for data in self.json['results']]

    @property
    def __parent__(self):
        return inspect.getmro(self.__class__)[1]

    def options(self, **kwargs):
        raise NotImplementedError

    def head(self, **kwargs):
        raise NotImplementedError

    def get(self, **params):
        ''' performs json validation '''
        r = self.api.get(self.base_url.format(**self.json), params=params)
        assert r.status_code == httplib.OK

        # validate schema
        self.json = r.objectify()
        self.validate_json(request='get')
        return self

    def post(self, payload={}):
        r = self.api.post(self.base_url, payload)
        try:
            data = r.json()
        except ValueError, e:
            '''If there was no json to parse'''
            data = dict()

        exc_str = "%s (%s) received" % (httplib.responses[r.status_code], r.status_code)
        if r.status_code in (httplib.OK, httplib.CREATED, httplib.ACCEPTED):
            self.validate_json(json=data, request='post')
            # With an inheritence of Org_List -> Org -> Base -> Page, the following
            # will find the parent class of the current object (e.g. 'Org').

            # Also, don't forget to call r.objectify() on the json structure.
            # Without that call, it will simply be a json dictionary.  By calling
            # r.objectify(), it behaves like a classic dictionary, but also is
            # JSON_Wrapped() to allow attribute access (e.g.
            # self.json['username'] == self.username)
            return self.__parent__(self.testsetup, base_url=data['url'], json=r.objectify())
        elif r.status_code == httplib.NO_CONTENT:
            raise NoContent_Exception(exc_str)
        elif r.status_code == httplib.FORBIDDEN:
            raise Forbidden_Exception(exc_str)
        elif r.status_code == httplib.BAD_REQUEST:
            # Attempt to validate the json response.  If it validates against a
            # 'duplicate' method, then we return a Duplicate_Exception.  If
            # validation fails, raise BadRequest_Exception.
            try:
                self.validate_json(json=data, request='duplicate')
            except:
                raise BadRequest_Exception(exc_str + ": %s" % data)
            else:
                raise Duplicate_Exception(exc_str + ". However, JSON validation determined the cause was a duplicate object already exists: %s" % data)
        else:
            raise Unknown_Exception(exc_str + ": %s" % data)

    def go_to_next(self):
        if self.next:
            next_page = self.__class__(self.testsetup, base_url=self.next)
            return next_page.get()

    def go_to_previous(self):
        if self.previous:
            prev_page = self.__class__(self.testsetup, base_url=self.previous)
            return prev_page.get()
