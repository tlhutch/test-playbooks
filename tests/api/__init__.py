from io import StringIO
import logging

from awxkit.config import config
from awxkit.awx import utils
import contextlib
import pytest


class APITest(object):
    """Base class"""

    @pytest.fixture(autouse=True)
    def access_connections(self, request):
        setattr(self, 'connections', request.config.pluginmanager.getplugin('plugins.pytest_restqa.plugin').connections)

    @pytest.fixture(autouse=True)
    def attach_stream_handler(self, request):
        stream = StringIO()
        handler = logging.StreamHandler(stream)
        handler.setLevel('ERROR')

        # This is not xdist friendly to say the least
        # TODO: implement per-test suite logging system
        log = logging.getLogger('awxkit.api.pages.page')
        log.addHandler(handler)

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

    def primary_instance_group(self, api_version):
        """Clusters normally are deployed with each instance having a numbered instance group.

        The instance group '1' is for the 'primary instance', e.g. the one we connect with '--base-url=`

        Otherwise, even for standalone instances we can't be guaranteed that other instance groups are not present.
        In this case the most trustworthy instance group is 'tower', which should be the standard instance group
        made for the standalone instance.

        Note that a standalone instance group could have any number of empty instance groups or instance groups pointing to the same instance.
        """
        igs = api_version.instance_groups.get(controller__isnull=True).results
        is_cluster = api_version.ping.get().ha
        igs = [ig for ig in igs if not ig.is_containerized]
        if len(igs) > 1 and is_cluster:
            return [ig for ig in igs if ig.name == '1'].pop()
        else:
            return [ig for ig in igs if ig.name == 'tower'].pop()

    def ensure_jt_runs_on_primary_instance(self, jt, api_version):
        jt.add_instance_group(self.primary_instance_group(api_version))

    @contextlib.contextmanager
    def current_user(self, username=None, password=None):
        with utils.as_user(self.connections['root'], username, password):
            yield

    @contextlib.contextmanager
    def current_instance(self, connection, v=None, pages=[]):
        """
        Context manager to allow running tests against alternative tower instance.

        Set connection object (sets connection for factories):
        >>> from awxkit.api.client import Connection
        >>> connection = Connection('https://' + hostname)
        >>> connection.login(user.username, user.password)
        >>> with self.current_instance(connection):
        >>>     jt = factories.job_template()

        Set connection object and provide version object
        (sets connection for factories and version object):
        >>> from awxkit.api.client import Connection
        >>> connection = Connection('https://' + hostname)
        >>> connection.login(user.username, user.password)
        >>> with self.current_instance(connection, v2):
        >>>     ig = v2.instance_groups.get().results.pop()
        >>>     jt = factories.job_template()
        >>>     jt.add_instance_group(ig)
        >>>     job = jt.launch()
        >>>     assert ig.consumed_capacity > 0

        Set connection object and provide page objects
        (sets connection for factories and page objects):
        >>> from awxkit.api.client import Connection
        >>> connection = Connection('https://' + hostname)
        >>> connection.login(user.username, user.password)
        >>> jt1 = factories.job_template()
        >>> jt2 = factories.job_template()
        >>> with self.current_instance(connection, pages=[jt1, jt2]):
        >>>     jt1.get()  # both jt1 and jt2 will use
        >>>     jt2.get()  # new connection to perform GET
        """
        try:
            previous_connection = self.connections['root']
            self.connections['root'] = connection
            if v:
                previous_v_connection = v.connection
                v.connection = connection
            reset_page_connections = []
            for p in pages:
                previous_page_connection = p.connection

                def _reset_page_connection():
                    p.connection = previous_page_connection

                p.connection = connection
                reset_page_connections.append(_reset_page_connection)
            yield
        finally:
            self.connections['root'] = previous_connection
            if v:
                v.connection = previous_v_connection
            for f in reset_page_connections:
                f()
