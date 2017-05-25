from contextlib import contextmanager
import logging
import sys

import pytest

from towerkit.tower.license import generate_license


log = logging.getLogger(__name__)


def install_license(api_config_pg, **license_info):
    """Install a Tower license

    :param api_config_pg: A Tower API configuration endpoint model
    :param license_info: key-value pairs for the configuration endpoint request

    Usage::
        >>> # install a basic license with 100 days remaining
        >>> install_license(api_config_pg, license_type='basic', days=100)
    """
    # install license
    api_config_pg.post(license_info)
    # confirm that license is present
    conf = api_config_pg.get()
    assert conf.is_valid_license, 'Invalid license found'
    # confirm license type
    expected_license_type = license_info['license_type']
    assert conf.license_info.license_type == expected_license_type, (
        'expected {0} license, found {1}'.format(
            expected_license_type, conf.license_info.license_type))
    # confirm license key
    expected_license_key = license_info['license_key']
    assert conf.license_info.license_key == expected_license_key, (
        'License found differs from license applied')


@pytest.fixture
def apply_license(api_config_pg):
    """Create a context manager for on-the-fly license switching. The initial
    license intallation state is retained after exiting.
    """
    @contextmanager
    def _apply_license(license_type, days=365, **kwargs):
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
        if license_type is None and kwargs:
            raise ValueError('No additional data may be provided for deletions')

        initial_info = getattr(api_config_pg.get(), 'license_info', None)

        if license_type is None:
            api_config_pg.delete()
        else:
            info = generate_license(license_type=license_type, days=days, **kwargs)
            install_license(api_config_pg, **info)
        yield
        if not initial_info:
            api_config_pg.delete()
        else:
            install_license(api_config_pg, eula_accepted=True, **initial_info)
    return _apply_license


@pytest.yield_fixture
def no_license(api_config_pg):
    """Remove an active license"""
    log.debug('deleting any active license')
    api_config_pg.delete()
    yield
    api_config_pg.delete()


@pytest.yield_fixture
def install_legacy_license(api_config_pg):
    """Install legacy license"""
    log.debug('calling fixture install_legacy_license')
    license_info = generate_license(
        days=365,
        instance_count=sys.maxint,
        license_type='legacy')
    install_license(api_config_pg, **license_info)
    yield
    api_config_pg.delete()


@pytest.yield_fixture
def install_basic_license(api_config_pg):
    """Install basic license"""
    log.debug('calling fixture install_basic_license')
    license_info = generate_license(
        days=365,
        instance_count=sys.maxint,
        license_type='basic')
    install_license(api_config_pg, **license_info)
    yield
    api_config_pg.delete()


@pytest.yield_fixture
def install_enterprise_license(api_config_pg):
    """Install enterprise license"""
    log.debug('calling fixture install_enterprise_license')
    license_info = generate_license(
        days=365,
        instance_count=sys.maxint,
        license_type='enterprise')
    install_license(api_config_pg, **license_info)
    yield
    api_config_pg.delete()


@pytest.yield_fixture(scope='class')
def install_enterprise_license_unlimited(api_config_pg):
    """Install enterprise license at the class fixture scope"""
    log.debug('calling fixture install_enterprise_license_unlimited')
    license_info = generate_license(
        days=365,
        instance_count=sys.maxint,
        license_type='enterprise')
    install_license(api_config_pg, **license_info)
    yield
    api_config_pg.delete()
