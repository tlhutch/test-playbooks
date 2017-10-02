from contextlib import contextmanager
import logging
import pytest


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
        config = api.current_version.get().config.get()

        initial_info = config.license_info

        try:
            if license_type is None:
                log.info('Deleting current license...')
                config.delete()
            else:
                log.info('Applying {} license...'.format(license_type))
                config.install_license(license_type=license_type, days=days, **kwargs)
            yield config.get().license_info

        finally:
            log.info('Restoring initial license.')
            if not initial_info:
                config.delete()
            else:
                initial_info['eula_accepted'] = True
                config.post(initial_info)

    return _apply_license


@pytest.fixture(scope='class')
def no_license(apply_license):
    """Remove an active license"""
    with apply_license(None):
        yield


@pytest.fixture(scope='class')
def install_legacy_license(apply_license):
    with apply_license('legacy'):
        yield


@pytest.fixture(scope='class')
def install_basic_license(apply_license):
    with apply_license('basic'):
        yield


@pytest.fixture(scope='class')
def install_enterprise_license(apply_license):
    with apply_license('enterprise'):
        yield


@pytest.fixture(scope='class')
def install_enterprise_license_unlimited(apply_license):
    with apply_license('enterprise'):
        yield
