import webapp2

from google.appengine.ext import ndb

DEFAULT_LOG = "default_log"


class LogEntry(ndb.Model):
    """A main model for representing log entry for this request"""

    request_body = ndb.StringProperty(indexed=False)
    headers = ndb.StringProperty(indexed=False)
    date = ndb.DateTimeProperty(auto_now_add=True)


def log_key(log_name=DEFAULT_LOG):
    """Constructs a Datastore key for a LogEntry entity.
    Use log_name as the key.
    """
    return ndb.Key('Log', log_name)


class MainPage(webapp2.RequestHandler):
    """Simple webservice for receiving webhook notifications from Tower"""

    def get(self):
        """Support for GET method"""
        self.response.headers['Content-Type'] = 'text/plain'
        self.response.write('Notification webservice is active.')

    def post(self):
        """Support for POST method"""
        # Get information from request
        headers = self.request.headers
        body = self.request.body
        if 'log_name' in headers:
            log_name = headers['log_name']
        else:
            log_name = DEFAULT_LOG

        # Create log entry
        log_entry = LogEntry(parent=log_key(log_name))
        # Dictionary should use double-quotes (so it can be converted to JSON)
        log_entry.headers = str(headers).replace('"', '<temp quote>').replace('\'', '"').replace('<temp quote>', '\'')
        log_entry.request_body = body
        log_entry.put()

        # Create response
        response = "[Log %s] <headers: %s> <body: %s>" % \
                   (log_name, headers, body)
        self.response.headers['Content-Type'] = 'text/plain'
        self.response.write(response)


app = webapp2.WSGIApplication([
    ('/', MainPage),
], debug=True)
