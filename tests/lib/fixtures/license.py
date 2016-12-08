import os.path
import logging
import pytest


log = logging.getLogger(__name__)


@pytest.fixture(scope='session')
def tower_license_path(request, tower_config_dir):
    return os.path.join(tower_config_dir, 'license')
