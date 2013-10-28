import logging
import json
import urllib2
import types
import requests

class Connection(object):
    def __init__(self, server, version=None, verify=False, authtoken=None):
        self.server = server
        self.version = version
        self.verify = verify
        self.authtoken = authtoken
        self.auth = None

    # http://docs.python-requests.org/en/latest/api/?highlight=logging
    # these two lines enable debugging at httplib level (requests->urllib3->httplib)
    # you will see the REQUEST, including HEADERS and DATA, and RESPONSE with HEADERS but without DATA.
    # the only thing missing will be the response.body which is not logged.

    def setup_logging(self, hdlr=None):
        # Figure out how to pipe this to a file (not stdout)
        import httplib
        httplib.HTTPConnection.debuglevel = 0

        #root_log = logging.getLogger()
        #root_log.setLevel(logging.DEBUG)
        requests_log = logging.getLogger("requests.packages.urllib3")
        requests_log.setLevel(logging.DEBUG)

        if hdlr:
            requests_log.addHandler(hdlr)

    def login(self, username, password):
        '''store credentials for future requests'''
        self.auth = (username, password)

    def _request(self, endpoint, data=None, method='GET', params=None):
        method = method.lower()
        headers = dict()
        payload = ''

        # Locate correct requests method
        if not hasattr(requests, method):
            raise Exception("Unknown request method: %s" % method)
        request_handler = getattr(requests, method)

        # Build url, headers and params
        url = "%s%s" % (self.server, endpoint)
        headers['Content-type'] = 'application/json'

        # Pass along authtoken if available
        if self.authtoken is not None:
            headers['Authorization'] = 'Token %s' % self.authtoken['token']

        # jsonify the POST payload (if available)
        if data is not None:
            payload = json.dumps(data)

        try:
            response = request_handler(url,
                verify=self.verify,
                headers=headers,
                params=params,
                data=payload,
                auth=self.auth)
        except Exception, e:
            err_str = "%s, url: %s" % (str(e), url,)

            if hasattr(e, 'read'):
                err_str += ", %s" % (e.read())
            raise BaseException(err_str)

        # Add convenience attribute 'code' to mimick urllib2 response
        response.code = response.status_code

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
