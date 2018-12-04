from StringIO import StringIO
import logging
import re

from towerkit.config import config
from towerkit.tower import utils
import contextlib
import pytest


error_pattern = re.compile(r'SchemaValidationError\:.*\n')


@pytest.mark.api
class APITest(object):
    """Base class"""

    @classmethod
    def setup_class(cls):
        cls.connections = pytest.config.pluginmanager.getplugin('plugins.pytest_restqa.plugin').connections

    @pytest.fixture(autouse=True)
    def attach_stream_handler_and_validate_schema_on_teardown(self, request):
        stream = StringIO()
        handler = logging.StreamHandler(stream)
        handler.setLevel('ERROR')

        # This is not xdist friendly to say the least
        # TODO: implement per-test suite logging system
        log = logging.getLogger('towerkit.api.pages.page')
        log.addHandler(handler)

        def _raise_on_teardown_if_validation_error():
            stream.flush()
            stream.seek(0)
            test_log = ''.join(stream.readlines())
            errors = error_pattern.findall(test_log)

            log.removeHandler(handler)

            if errors:
                raise Exception('Found SchemaValidationError: {0}'.format(''.join(errors)))

        request.addfinalizer(_raise_on_teardown_if_validation_error)

    @property
    def credentials(self):
        """convenient access to credentials"""
        return config.credentials

    def has_credentials(self, ctype, sub_ctype=None, fields=[]):
        """assert whether requested credentials are present"""
        # Make sure credentials.yaml has ctype we need
        assert ctype in self.credentials, \
            "No '%s' credentials defined in credentals.yaml" % ctype
        creds = self.credentials[ctype]

        # Ensure requested sub-type is present
        if sub_ctype:
            assert sub_ctype in creds, \
                "No '%s' '%s' credentials defined in credentals.yaml" % \
                (ctype, sub_ctype)
            creds = creds[sub_ctype]

        # Ensure requested fields are present
        if fields:
            assert all([field in creds for field in fields]), \
                "Missing required credentials (%s) for section '%s' in credentials.yaml" % \
                (', '.join(fields), ctype)

        return True

    def ensure_jt_runs_on_primary_instance(self, jt, api_version):
        igs = api_version.instance_groups.get(controller__isnull=True)
        if igs.count != 1:
            ig = [ig for ig in igs.results if ig.name == '1'].pop()
            jt.add_instance_group(ig)

    @contextlib.contextmanager
    def current_user(self, username=None, password=None):
        with utils.as_user(self.connections['root'], username, password):
            yield

    @contextlib.contextmanager
    def current_instance(self, connection, v=None):
        """
        Context manager to allow running tests against alternative tower instance.

        Set connection object (sets connection for factories):
        >>> from towerkit.api.client import Connection
        >>> connection = Connection('https://' + hostname)
        >>> connection.login(user.username, user.password)
        >>> with self.current_instance(connection):
        >>>     jt = factories.job_template()

        Set connection object and provide version object
        (sets connection for factories and version object):
        >>> from towerkit.api.client import Connection
        >>> connection = Connection('https://' + hostname)
        >>> connection.login(user.username, user.password)
        >>> with self.current_instance(connection, v2):
        >>>     ig = v2.instance_groups.get().results.pop()
        >>>     jt = factories.job_template()
        >>>     jt.add_instance_group(ig)
        >>>     job = jt.launch()
        >>>     assert ig.consumed_capacity > 0
        """
        try:
            previous_connection = self.connections['root']
            self.connections['root'] = connection
            if v:
                previous_v_connection = v.connection
                v.connection = connection
            yield
        finally:
            self.connections['root'] = previous_connection
            if v:
                v.connection = previous_v_connection
