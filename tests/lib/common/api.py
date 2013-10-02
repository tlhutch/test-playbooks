import json
import urllib2

class Connection(object):

    def __init__(self, server):
        self.server = server

    def login(username=None, password=None):

        # Setup urllib2 for basic password authentication.
        password_mgr = urllib2.HTTPPasswordMgrWithDefaultRealm()
        password_mgr.add_password(None, self.server, username, password)
        handler = urllib2.HTTPBasicAuthHandler(password_mgr)
        opener = urllib2.build_opener(handler)
        urllib2.install_opener(opener)

        try:
            self.get('/api')
        except Exception, e:
            raise BaseException(str(e))

    def _request(self, endpoint, data=None, method='GET'):
        url = "%s%s" % (self.server, endpoint)
        request = urllib2.Request(url)

        if method in ['PUT', 'PATCH', 'POST', 'DELETE']:
            request.add_header('Content-type', 'application/json')
            request.get_method = lambda: method

        if data is not None:
            request.add_data(json.dumps(data))

        data = None
        try:
            response = urllib2.urlopen(request)
            data = response.read()
        except Exception, e:
            err_str = "%s, url: %s, data: %s" % (str(e), url, data, )

            if hasattr(e, 'read'):
                err_str += ", %s" % (e.read())
            raise BaseException(err_str)
        try:
            result = json.loads(data)
            return result
        except:
            return data

    def get(self, endpoint):
        return self._request(endpoint)

    def post(self, endpoint, data):
        return self._request(endpoint, data, method='POST')

    def put(self, endpoint, data):
        return self._request(endpoint, data, method='PUT')

    def patch(self, endpoint, data):
        return self._request(endpoint, data, method='PATCH')

    def delete(self, endpoint):
        return self._request(endpoint, method='DELETE')
