import logging
import json
import urllib2
import requests
import warnings
import types

# Adapted from
# http://code.activestate.com/recipes/389916-example-setattr-getattr-overloading/
class JSON_Wrapper(dict):
    '''
    Provide object interface to json dictionary structure.  This class
    overloads the __getattr__ and __setattr__ methods to allow accessing
    dictionary items as class attributes.
    '''
    def __init__(self, json={}):
        self.merge_json(json)

    def merge_json(self, json):
        # If the json parameter doesn't support iteritems(), move on.  This
        # addresses the scenario when:
        #   json = {u'name': [u'Organization with this Name already exists.']}
        #   json = [u'setfact_50.yml']
        if not hasattr(json, 'iteritems'):
            warnings.warn("Attempting to wrap non-dict object: %s" % json)
            return

        super(JSON_Wrapper, self).__init__(json)

        # Convert nested structures into JSON_Wrappers
        for k, v in json.iteritems():
            if isinstance(v, list):
                # If every item in the list is a dict ... wrap it
                if all([isinstance(item, dict) for item in v]):
                    setattr(self, k, [JSON_Wrapper(item) for item in v])
            elif isinstance(v, tuple):
                # If every item in the tuple is a dict ... wrap it
                if all([isinstance(item, dict) for item in v]):
                    setattr(self, k, (JSON_Wrapper(item) for item in v))
            elif isinstance(v, dict):
                setattr(self, k, JSON_Wrapper(v))
            #else:
            #    setattr(self, k, v)

    def __getattr__(self, item):
        """Maps values to attributes.
        Only called if there *isn't* an attribute with this name
        """
        try:
            return self.__getitem__(item)
        except KeyError:
            raise AttributeError(item)

    def __setattr__(self, item, value):
        """Maps attributes to values.
        Only if we are initialised
        """
        # any normal attributes are handled normally
        if self.__dict__.has_key(item):
            super(JSON_Wrapper, self).__setattr__(item, value)
        else:
            self.__setitem__(item, value)

def objectify(self):
    '''
    Returns an initialized JSON_Wrapper object.  Used by the Connection class
    for monkey patching the request response.
    '''
    # If the JSON response fails to parse (typically for an empty dict), return
    # an empty-dict
    try:
        json = self.json()
    except ValueError, e:
        warnings.warn("Unable to parse JSON response: " % self.text)
        json = dict()

    return JSON_Wrapper(json=json)

class Token_Auth(requests.auth.AuthBase):
    '''Implement token based authentication for requests'''
    def __init__(self, token):
        self.token = token

    def __call__(self, request):
        request.headers['Authorization'] = 'Token %s' % self.token
        return request

class Connection(object):
    def __init__(self, server, version=None, verify=False):
        self.server = server
        self.version = version
        self.verify = verify
        self.auth = None
        self.url = ""
        self.requests_log = None

        # prepare session object
        self.session = requests.Session()
        adapter = requests.adapters.HTTPAdapter(max_retries=3)
        self.session.mount('http://', adapter)
        self.session.mount('https://', adapter)
        self.session.headers['Content-type'] = 'application/json'

    # http://docs.python-requests.org/en/latest/api/?highlight=logging
    # these two lines enable debugging at httplib level (requests->urllib3->httplib)
    # you will see the REQUEST, including HEADERS and DATA, and RESPONSE with HEADERS but without DATA.
    # the only thing missing will be the response.body which is not logged.

    def setup_logging(self, hdlr=None):
        # FIXME - Figure out how to pipe this to a file (not stdout)
        root_log = logging.getLogger()
        if root_log.level <= logging.DEBUG:
            import httplib
            httplib.HTTPConnection.debuglevel = 1

        self.requests_log = logging.getLogger("requests.packages.urllib3")
        self.requests_log.setLevel(logging.DEBUG)

        if hdlr:
            self.requests_log.addHandler(hdlr)

    def login(self, username=None, password=None, token=None):
        '''Store authentication credentials for future requests'''
        if username and password:
            self.session.auth = (username, password)
        elif token:
            self.session.auth = Token_Auth(token)
        else:
            self.session.auth = None

    def logout(self):
        '''Remove stored credentials for future requests'''
        self.session.auth = None

    def _request(self, endpoint, data=None, method='GET', params=None):
        payload = ''

        # Locate correct requests method
        method = method.lower()
        if not hasattr(self.session, method):
            raise Exception("Unknown request method: %s" % method)
        request_handler = getattr(self.session, method)

        # Build url
        url = "%s%s" % (self.server, endpoint)

        # jsonify the POST payload (if available)
        if data is not None:
            payload = json.dumps(data)

        # Define requests hook to display API elapsed time
        def log_elapsed(r, *args, **kwargs):
            if self.requests_log:
                self.requests_log.debug("\"%s %s\" elapsed: %s" % (r.request.method, r.url, r.elapsed))

        try:
            response = request_handler(url,
                verify=self.verify,
                params=params,
                data=payload,
                hooks=dict(response=log_elapsed))
        except Exception, e:
            err_str = "%s, url: %s" % (str(e), url,)

            if hasattr(e, 'read'):
                err_str += ", %s" % (e.read())
            raise BaseException(err_str)

        # Save the full URL for later inspection
        self.url = response.url

        # Add convenience attribute 'code' to mimick urllib2 response
        response.code = response.status_code

        # Add conventience method to return object representation of json
        response.objectify = types.MethodType(objectify, response)

        return response

    def get(self, endpoint, params=None):
        return self._request(endpoint, params=params)

    def head(self, endpoint):
        return self._request(endpoint, method='HEAD')

    def options(self, endpoint):
        return self._request(endpoint, method='OPTIONS')

    def post(self, endpoint, data):
        return self._request(endpoint, data, method='POST')

    def put(self, endpoint, data):
        return self._request(endpoint, data, method='PUT')

    def patch(self, endpoint, data):
        return self._request(endpoint, data, method='PATCH')

    def delete(self, endpoint):
        return self._request(endpoint, method='DELETE')
