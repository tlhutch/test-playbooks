from contextlib import contextmanager
import logging
import os

import pytest


log = logging.getLogger(__name__)


@pytest.fixture(scope='session')
def apply_license(api, mp_message_board, mp_lock):
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

        config = api.current_version.get().config.get()
        initial_info = config.license_info

        def teardown_license():
            log.info('Restoring initial license.')
            if not initial_info:
                config.delete()
            else:
                initial_info['eula_accepted'] = True
                config.post(initial_info)

        pid = os.getpid()
        try:
            log.info('{} Waiting for setup lock'.format(pid))
            with mp_lock:
                log.info('{} HAS LOCK: {} {}'.format(pid, id(mp_message_board), mp_message_board))
                if 'apply_license_current_type' not in mp_message_board:
                    log.info('{} ESTABLISHING APPLY_LICENSE: {}'.format(pid, mp_message_board))
                    mp_message_board['apply_license_current_type'] = None
                    mp_message_board['apply_license_previous_info'] = {}
                    mp_message_board['apply_license_consumers'] = 0

                if mp_message_board['apply_license_current_type'] != license_type \
                   and mp_message_board['apply_license_consumers'] == 0:
                    log.info('{} APPLYING LICENSE: {}'.format(pid, mp_message_board))
                    initial_info = config.license_info
                    mp_message_board['apply_license_previous_info'] = initial_info
                    log.info('{} STORING PREVIOUS INFO: {}'.format(pid, mp_message_board))
                    if license_type is None:
                        log.info('{} Deleting current license...')
                        config.delete()
                    else:
                        log.info('{} Applying {} license...'.format(pid, license_type))
                        config.install_license(license_type=license_type, days=days, **kwargs)
                    if request:
                        # We need to explictly register teardowns instead of yield-driven
                        # teardown for class_factory teardown ordering
                        request.addfinalizer(teardown_license)
                    mp_message_board['apply_license_current_type'] = license_type
                    log.info('{} set current_type: {}'.format(pid, mp_message_board))
                else:
                    log.info('{} LICENSE ALREADY APPLIED: {}'.format(pid, mp_message_board))

                mp_message_board['apply_license_consumers'] += 1

            log.info('{} Released setup lock'.format(pid))
            yield config.get().license_info
        finally:
            if not request:
                log.info('{} Waiting for teardown lock'.format(pid))
                with mp_lock:
                    log.info('IN TEARDOWN: {}'.format(mp_message_board))
                    current_type = mp_message_board['apply_license_current_type']
                    previous_info = mp_message_board['apply_license_previous_info']

                    mp_message_board['apply_license_consumers'] -= 1
                    log.info('DECREMENTED CONSUMERS {}'.format(mp_message_board['apply_license_consumers']))
                    if current_type != previous_info.get('license_type') and mp_message_board['apply_license_consumers'] == 0:
                        teardown_license()
                        mp_message_board['apply_license_current_type'] = previous_info.get('license_type')
                log.info('{} Released teardown lock'.format(pid))

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
