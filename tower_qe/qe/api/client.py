import requests
import logging
import types
import json

from qe.utils import PseudoNamespace


log = logging.getLogger(__name__)


def objectify(self):
    '''
    Returns an initialized PseudoNamespace object.  Used by the Connection class
    for monkey patching the request response.
    '''
    # If the JSON response fails to parse (typically for an empty dict), return
    # an empty-dict
    try:
        json = self.json()
    except ValueError:
        json = dict()

    # PseudoNamespace arg must be a dict, and json can be an array.
    if isinstance(json, types.DictType):
        return PseudoNamespace(json)
    return json


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

        # disable urllib3 warnings
        if not self.verify:
            requests.packages.urllib3.disable_warnings()

        # prepare session object
        self.session = requests.Session()
        # temporarily disabled to debug adapter problems
        # adapter = requests.adapters.HTTPAdapter(max_retries=3)
        # self.session.mount('http://', adapter)
        # self.session.mount('https://', adapter)
        self.session.headers['Content-type'] = 'application/json'

    # http://docs.python-requests.org/en/latest/api/?highlight=logging
    # these two lines enable debugging at httplib level (requests->urllib3->httplib)
    # you will see the REQUEST, including HEADERS and DATA, and RESPONSE with HEADERS but without DATA.
    # the only thing missing will be the response.body which is not logged.

    def setup_logging(self, hdlr=None):
        # FIXME - Figure out how to pipe httplib logs to a file (not just stdout)
        logger = logging.getLogger()
        if logger.level <= logging.DEBUG:
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

        attempts = 0
        while attempts < 5:
            try:
                response = request_handler(
                    url,
                    verify=self.verify,
                    params=params,
                    data=payload,
                    hooks=dict(response=log_elapsed))
            except requests.exceptions.ConnectionError, e:
                err_str = "%s, url: %s" % (str(e), url,)
                if hasattr(e, 'read'):
                    err_str += ", %s" % (e.read())
                log.warn("%s, retrying" % err_str)
                attempts + 1
                continue
            else:
                break

        # Save the full URL for later inspection
        self.url = response.url

        # Add convenience attribute 'code' to mimick urllib2 response
        response.code = response.status_code

        # Add convenience method to return object representation of json
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
