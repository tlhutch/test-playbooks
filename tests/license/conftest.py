import logging
import sys
from contextlib import contextmanager

import pytest

from awxkit.tower.license import generate_license

from tests.lib.license import (
    apply_license_until_effective,
    delete_license_until_effective,
)


log = logging.getLogger(__name__)


@pytest.fixture(scope='session')
def apply_license(api):
    """Create a context manager for on-the-fly license switching. The initial
    license intallation state is retained after exiting.
    """

    @contextmanager
    def _apply_license(license_type=None, days=365, **kwargs):
        """Switch the license installation to one with the provided license
        information.

        :param license_type: The type of license to install. If the None
            keyword is provided, existing licenses will be deleted.
        :param kwargs: Additional key-value pairs for generating the
             configuration endpoint request payload.

        Usage::
            >>> # make an organization and try to read it with a basic license
            >>> org = factories.organization()
            >>> with apply_license('basic'):
            >>>     org.get()
            >>> # attempt to delete the organization without a license
            >>> with apply_license(None):
            >>>     org.delete()
            >>> *** PaymentRequired_Exception
        """
        request = kwargs.pop('request', False)

        instance_count = kwargs.get('instance_count', 0)
        trial = kwargs.get('trial', False)
        license_hash = str(license_type) + str(days) + str(instance_count) + str(trial)

        # Fetch the current license information to restore later
        config = api.current_version.get().config.get()
        initial_license_info = config.license_info

        node_name = request.node.name if request else "Unknown"
        func_name = request._pyfuncitem.name if request else "Unknown"

        def teardown_license():
            log.debug("{}::{} teardown license {}".format(node_name, func_name, license_hash))
            config = api.current_version.get().config.get()
            license_info = initial_license_info
            log.info('Restoring initial license.')
            if not license_info:
                delete_license_until_effective(config)
            else:
                license_info['eula_accepted'] = True
                apply_license_until_effective(config, license_info)

        try:
            log.debug("{}::{} setup license {}".format(node_name, func_name, license_hash))
            if license_type is None:
                delete_license_until_effective(config)
            else:
                instance_count = kwargs.pop('instance_count', sys.maxsize)
                license_info = generate_license(instance_count=instance_count,
                                                days=days,
                                                license_type=license_type, **kwargs)
                apply_license_until_effective(config, license_info)

            if request:
                # We need to explictly register teardowns instead of yield-driven
                # teardown for class_factory teardown ordering
                request.addfinalizer(teardown_license)

            yield
        finally:
            if not request:
                teardown_license()

    return _apply_license


@pytest.fixture(scope='module')
def no_license(module_authtoken, apply_license, module_subrequest):
    with apply_license(None, request=module_subrequest):
        yield


@pytest.fixture(scope='module')
def install_legacy_license(module_authtoken, apply_license, module_subrequest):
    with apply_license('legacy', request=module_subrequest):
        yield


@pytest.fixture(scope='module')
def install_basic_license(module_authtoken, apply_license, module_subrequest):
    with apply_license('basic', request=module_subrequest):
        yield


@pytest.fixture(scope='module')
def install_enterprise_license(module_authtoken, apply_license, module_subrequest):
    with apply_license('enterprise', request=module_subrequest):
        yield


@pytest.fixture(scope='module')
def install_enterprise_license_unlimited(module_authtoken, apply_license, module_subrequest):
    with apply_license('enterprise', request=module_subrequest):
        yield


@pytest.fixture(scope='session', autouse=False)
def session_install_enterprise_license_unlimited(session_authtoken, v2_session):
    """Override the session_install_enterprise_license_unlimited from the parent's directory conftest.

    Make the session_install_enterprise_license_unlimited no-op so it does not affect tests on this
    package. Be aware that you may get unexpected behavior if you don't run these tests separate from
    the other tests.
    """
