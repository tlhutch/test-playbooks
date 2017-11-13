from contextlib import contextmanager
import logging

import pytest


log = logging.getLogger(__name__)


@pytest.fixture(scope='session')
def apply_license(api, mp_trail, mp_message_board):
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

        initial_info_key = license_hash + '_initial_info'

        def teardown_license():
            with mp_trail(license_hash, 'finish') as finish:
                if finish:
                    config = api.current_version.get().config.get()
                    initial_info = mp_message_board[initial_info_key]
                    log.info('Restoring initial license.')
                    if not initial_info:
                        config.delete()
                    else:
                        initial_info['eula_accepted'] = True
                        config.post(initial_info)
                    del mp_message_board[initial_info_key]

        try:
            with mp_trail(license_hash, 'start') as start:
                if start:
                    config = api.current_version.get().config.get()
                    mp_message_board[initial_info_key] = config.license_info

                    if license_type is None:
                        log.info('Deleting current license...')
                        config.delete()
                    else:
                        log.info('Applying {} license...'.format(license_type))
                        config.install_license(license_type=license_type, days=days, **kwargs)
            if request:
                # We need to explictly register teardowns instead of yield-driven
                # teardown for class_factory teardown ordering
                request.addfinalizer(teardown_license)

            yield
        finally:
            if not request:
                teardown_license()

    return _apply_license


@pytest.fixture(scope='class')
def no_license(apply_license, class_subrequest):
    with apply_license(None, request=class_subrequest):
        yield


@pytest.fixture(scope='class')
def install_legacy_license(apply_license, class_subrequest):
    with apply_license('legacy', request=class_subrequest):
        yield


@pytest.fixture(scope='class')
def install_basic_license(apply_license, class_subrequest):
    with apply_license('basic', request=class_subrequest):
        yield


@pytest.fixture(scope='class')
def install_enterprise_license(apply_license, class_subrequest):
    with apply_license('enterprise', request=class_subrequest):
        yield


@pytest.fixture(scope='class')
def install_enterprise_license_unlimited(apply_license, class_subrequest):
    with apply_license('enterprise', request=class_subrequest):
        yield
