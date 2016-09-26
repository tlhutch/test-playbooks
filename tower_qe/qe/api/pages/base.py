import logging
import inspect
import httplib
import types
import json
import re

from toposort import toposort

from qe.utils import PseudoNamespace, is_relative_endpoint
from qe.api.client import Connection
from qe.api.schema import validate
from qe.api.pages import Page
from qe.api import resources
from qe.config import config
import qe.exceptions
import qe


log = logging.getLogger(__name__)


# Page Class Registration utilities.
_page_registry = {}


def register_page(urls, page_cls):
    """Registers a `Base` subclass by a (list of) re-friendly url(s) for retrieval
       through `get_registered_page`. The first, or only, url provided will be that
       page class's default `base_url`.

       ex:
       register_page('/api/v1/resource/', ResourcesPageClass)
       register_page(['/api/v1/resource/\d+/',
                      '/api/v1/other_resource/\d+/resource/\d+/'], ResourcePageClass)
       >>> ResourcesPageClass().base_url
       '/api/v1/resource/'
    """
    if not isinstance(urls, list):
        urls = [urls]
    page_cls.base_url = urls[0]
    for url in urls:
        # should account for any relative endpoint w/ query parameters
        pattern = '\A' + url + '(\?.*)*\Z'
        re_key = re.compile(pattern)
        _page_registry[re_key] = page_cls


def get_registered_page(url):
    """Matches api provided urls to a registered Base subclass."""
    page_cls = Base
    for re_key in _page_registry:
        if re_key.match(url):
            page_cls = _page_registry[re_key]
            break
    log.debug('Retrieved {} by url: {}'.format(page_cls, url))
    return page_cls


def dependency_graph(page):
    """Creates a dependency graph of the form
       {page: set(page.dependencies[0:i]),
        page.dependencies[0]: set(page.dependencies[0][0:j]
        ...
        page.dependencies[i][j][...][n]: set(page.dependencies[i][j][...][n][0:z]),
        ...}
    """
    graph = {}
    dependencies = set(page.dependencies)
    graph[page] = dependencies
    for dependency in page.dependencies:
        graph.update(dependency_graph(dependency))
    return graph


def creation_order(graph):
    """returns a list of sets representing the order of page creation that will resolve the dependencies
       of subsequent pages for any non-cyclic dependency_graph
    """
    return list(toposort(graph))


def page_creation_order(page):
    """returns the `creation_order()` for any desired page"""
    return creation_order(dependency_graph(page))


def all_instantiated_dependencies(pages):
    """returns a list of all instantiated dependencies including pages themselves"""
    scope_provided_dependencies = []
    pages = [page for page in pages if hasattr(page, 'dependency_store')]
    for provided in pages:
        for dependency in provided.dependency_store.values():
            if dependency and dependency not in scope_provided_dependencies:
                scope_provided_dependencies.extend(all_instantiated_dependencies([dependency]))
                scope_provided_dependencies = list(set(scope_provided_dependencies))

    scope_provided_dependencies.extend(pages)
    scope_provided_dependencies = list(set(scope_provided_dependencies))
    return scope_provided_dependencies


class Base(Page):
    """Base class for global project methods"""

    base_url = ''
    dependencies = []  # For reference only.  Use self.dependency_store as an instance variable

    def __init__(self, testsetup=None, base_url=None, **kwargs):
        if not testsetup:  # Create a mock testsetup w/ pytest_restqa-like content
            testsetup = PseudoNamespace()
            testsetup.request = PseudoNamespace()
            testsetup.request.config = config
            testsetup.api = Connection(config.base_url,
                                       version=config.api_version,
                                       verify=not config.assume_untrusted)
            testsetup.base_url = config.base_url

        super(Base, self).__init__(testsetup)
        self.json = kwargs.get('json', {})
        self.objectify = kwargs.get('objectify', True)

        if base_url:
            self.base_url = base_url

        self.dependency_store = {base_subclass: None for base_subclass in self.dependencies}

    def __getattr__(self, name):
        if 'json' in self.__dict__ and name in self.json:
            value = self.json[name]
            if is_relative_endpoint(value):
                value = TentativeBase(value, self.testsetup)
            elif isinstance(value, types.DictType):
                for key, item in value.items():
                    if is_relative_endpoint(item):
                        value[key] = TentativeBase(item, self.testsetup)
            return value
        raise AttributeError("{!r} object has no attribute {!r}"
                             .format(self.__class__.__name__, name))

    def __setattr__(self, name, value):
        if 'json' in self.__dict__ and name in self.json:
            # Update field only.  For new field use explicit patch
            self.patch(**{name: value})
        else:
            self.__dict__[name] = value

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return json.dumps(self.json, indent=4)

    @property
    def __item_class__(self):
        '''Returns the class representing a single 'Base' item'''
        return self.__class__

    def validate_json(self, json=None, request='GET'):
        '''Perform JSON validation on JSON response'''
        if json is None:
            validate(self.json, self.base_url, request.lower(),
                     version=config.api_version)
        else:
            validate(json, self.base_url, request.lower(),
                     version=config.api_version)

    def handle_request(self, r):
        try:
            data = r.json()
        except ValueError, e:
            '''If there was no json to parse'''
            log.warn("Unable to parse JSON response (%s): %s - '%s'" % (r.status_code, e, r.text))
            data = dict()

        exc_str = "%s (%s) received" % (httplib.responses[r.status_code], r.status_code)

        exception = exception_from_status_code(r.status_code)
        if exception:
            raise(exception(exc_str, data))

        elif r.status_code in (httplib.OK, httplib.CREATED, httplib.ACCEPTED):
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
        elif r.status_code == httplib.FORBIDDEN:
            try:
                self.validate_json(json=data, request='license_exceeded')
            except:
                raise qe.exceptions.Forbidden_Exception(exc_str, data)
            else:
                raise qe.exceptions.LicenseExceeded_Exception(exc_str, data)
        elif r.status_code == httplib.BAD_REQUEST:
            # Validate the 400 BAD_REQUEST response with known 400 errors.
            for (request, exc) in [('license_invalid', qe.exceptions.LicenseInvalid_Exception),
                                   ('duplicate', qe.exceptions.Duplicate_Exception)]:
                try:
                    self.validate_json(json=data, request=request)
                except:
                    continue
                else:
                    if request == 'duplicate':
                        exc_str += ". However, JSON validation determined the cause " \
                                   "was a duplicate object already exists."
                    raise exc(exc_str, data)

            # No custom 400 exception was raised, raise a generic 400 BAD_REQUEST exception
            raise qe.exceptions.BadRequest_Exception(exc_str, data)
        else:
            raise qe.exceptions.Unknown_Exception(exc_str, data)

    def get(self, **params):
        r = self.api.get(self.base_url.format(**self.json), params=params)
        self.handle_request(r)
        return self

    def post(self, payload={}):
        r = self.api.post(self.base_url, payload)
        return self.handle_request(r)

    def put(self, payload=None):
        '''If a payload is supplied, PUT the payload. If not, submit our
           existing page JSON as our payload.
        '''
        if payload is None:
            payload = self.json
        r = self.api.put(self.base_url.format(**payload), payload)
        return self.handle_request(r)

    def patch(self, **payload):
        r = self.api.patch(self.base_url.format(**self.json), payload)
        return self.handle_request(r)

    def options(self):
        r = self.api.options(self.base_url.format(**self.json))
        return self.handle_request(r)

    def delete(self):
        r = self.api.delete(self.base_url.format(**self.json))
        try:
            return self.handle_request(r)
        except qe.exceptions.NoContent_Exception:
            pass

    def silent_delete(self):
        '''Delete the object. If it's already deleted, ignore the error'''
        r = self.api.delete(self.base_url.format(**self.json))
        try:
            return self.handle_request(r)
        except (qe.exceptions.NoContent_Exception, qe.exceptions.NotFound_Exception):
            pass

    def get_related(self, related_name, **kwargs):
        assert related_name in self.json['related']
        base_url = self.json['related'][related_name]
        return self.walk(base_url, **kwargs)

    def walk(self, base_url, **kw):
        page_cls = get_registered_page(base_url)
        return page_cls(self.testsetup, base_url=base_url).get(**kw)

    def get_object_role(self, name):
        object_roles_pg = self.get_related('object_roles', role_field=name)
        assert object_roles_pg.count == 1, \
            "No role with name '%s' found." % name
        return object_roles_pg.results[0]

    @property
    def object_roles(self):
        from qe.api.pages import Roles_Page, Role_Page
        url = self.get().json.related.object_roles
        for obj_role in Roles_Page(self.testsetup, base_url=url).get().json.results:
            yield Role_Page(self.testsetup, base_url=obj_role.url).get()

    def cleanup(self):
        return self._cleanup(self.delete)

    def silent_cleanup(self):
        return self._cleanup(self.silent_delete)

    def _cleanup(self, delete_method):
        try:
            delete_method()
        except qe.exceptions.Conflict_Exception as e:
            if "running jobs" in e.message['conflict']:
                active_jobs = e.message.get('active_jobs', [])  # [{type: id},], not page containing
                jobs = []
                for active_job in active_jobs:
                    job_type = active_job['type']
                    base_url = '/api/v1/{}s/{}/'.format(job_type, active_job['id'])
                    job_class = get_registered_page(base_url)
                    job = job_class(self.testsetup, base_url=base_url).get()
                    jobs.append(job)
                    job.cancel()
                for job in jobs:
                    job.wait_until_completed(raise_on_timeout=True)
                delete_method()
            else:
                raise(e)

    def create(self, *a, **kw):
        """Actual tower resource creation.  Override in `Base` subclasses.
           If `Base` subclass has any dependenices, `self.create_necessary_dependencies(provided_dependencies)` should be called before
           resource creation logic.  Should never require arguments at call time (use defaults) and should always return `self`.
        """
        raise(NotImplementedError())

    def update_identity(self, obj):
        """Takes a `Base` and updates attributes to reflect its content"""
        self.base_url = obj.base_url
        self.json = obj.json
        return self

    def _update_dependencies(self, dependency_candidates):
        """updates self._dependency_cache to reflect instantiated dependencies, if any"""
        if self.dependencies:
            for potential in dependency_candidates:
                if potential.__class__ in self.dependency_store:
                    self.dependency_store[potential.__class__] = potential

    def create_and_update_dependencies(self, *provided_dependencies):
        """in order creation of dependencies and updating of self.dependency_store
           to include instances, indexed by page class:
           ```
           self.dependencies = [qe.api.pages.Inventory]
           self.create_and_update_dependencies()
           inventory = self.dependency_store[qe.api.pages.Inventory]
           ```
        """
        def _create_uninitialized_dependencies(instantiated_dependencies):
            """calls default `create()` for all uninitialized dependencies in order"""
            dependency_list = list(instantiated_dependencies)
            if not self.dependencies:
                return dependency_list

            scoped_dependencies = {d.__class__.__name__.lower(): d for d in dependency_list}

            for group in page_creation_order(self):
                for to_create in [page for page in group if page != self]:
                    create = True
                    for dependency in dependency_list:
                        # provided dependency already created
                        if isinstance(dependency, to_create):
                            create = False
                            break
                    if create:
                        obj = to_create(self.testsetup).create(**scoped_dependencies)
                        dependency_list.append(obj)
                        scoped_dependencies[obj.__class__.__name__.lower()] = obj
            return dependency_list

        self._update_dependencies(_create_uninitialized_dependencies(all_instantiated_dependencies(provided_dependencies)))

    def load_default_authtoken(self):
        default_cred = config.credentials.default
        payload = dict(username=default_cred.username,
                       password=default_cred.password)
        auth_url = resources.v1_authtoken
        auth = get_registered_page(auth_url)(self.testsetup, base_url=auth_url).post(payload)
        self.testsetup.api.login(token=auth.token)
        return self


_exception_map = {httplib.NO_CONTENT: qe.exceptions.NoContent_Exception,
                  httplib.NOT_FOUND: qe.exceptions.NotFound_Exception,
                  httplib.INTERNAL_SERVER_ERROR: qe.exceptions.InternalServerError_Exception,
                  httplib.METHOD_NOT_ALLOWED: qe.exceptions.Method_Not_Allowed_Exception,
                  httplib.UNAUTHORIZED: qe.exceptions.Unauthorized_Exception,
                  httplib.PAYMENT_REQUIRED: qe.exceptions.PaymentRequired_Exception,
                  httplib.CONFLICT: qe.exceptions.Conflict_Exception}


def exception_from_status_code(status_code):
    return _exception_map.get(status_code, None)


class BaseList(object):
    '''Allow: GET, POST, HEAD, OPTIONS'''
    @property
    def __item_class__(self):
        '''Returns the class representing a single 'Base' item'''
        # With an inheritence of OrgListSubClass -> OrgList -> BaseList -> Org -> Base -> Page, the following
        # will return the parent class of the current object (e.g. 'Org').
        mro = inspect.getmro(self.__class__)
        bl_index = mro.index(BaseList)
        return mro[bl_index + 1]

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

    def go_to_next(self):
        if self.next:
            next_page = self.__class__(self.testsetup, base_url=self.next)
            return next_page.get()

    def go_to_previous(self):
        if self.previous:
            prev_page = self.__class__(self.testsetup, base_url=self.previous)
            return prev_page.get()

    def create(self, *a, **kw):
        return self.__item_class__(self.testsetup).create(*a, **kw)


class TentativeBase(str):

    def __new__(cls, endpoint, testsetup):
        return super(TentativeBase, cls).__new__(cls, endpoint)

    def __init__(self, endpoint, testsetup):
        self.endpoint = endpoint
        self.testsetup = testsetup

    def _create(self):
        return get_registered_page(self.endpoint)(self.testsetup, base_url=self.endpoint)

    def get(self, **params):
        return self._create().get(**params)

    def post(self, payload={}):
        return self._create().post(payload)

    def put(self):
        return self._create().put()

    def patch(self, **payload):
        return self._create().patch(**payload)

    def delete(self):
        return self._create().delete()

    def options(self):
        return self._create().options()

    def create(self, *a, **kw):
        return self._create().create(*a, **kw)

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return self.endpoint

    def __eq__(self, other):
        return self.endpoint == other

    def __ne__(self, other):
        return self.endpoint != other
