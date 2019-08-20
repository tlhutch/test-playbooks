import logging

from awxkit.utils import poll_until
from awxkit.exceptions import BadRequest


log = logging.getLogger(__name__)


# Occasionally, license does not become effective after being installed.
# The following two helpers poll until the license is effective.
# Refer to https://github.com/ansible/tower/issues/2375
def apply_license_until_effective(config, license_info):
    # If we have an equivalent license, go ahead and return
    config = config.get()
    if config.license_info:
        if 'license_type' in config.license_info and 'instance_count' in config.license_info:
            if config.license_info.license_type == license_info['license_type'] and config.license_info.instance_count == license_info['instance_count']:
                if not config.license_info.date_expired:
                    return
    log.info('Applying {} license...'.format(license_info['license_type']))
    try:
        config.post(license_info)
    except BadRequest:
        if config.is_awx_license:
            log.warning('Detected AWX instead of Tower, see README "Set up Tower-License module", proceed at own risk.')
            return
        else:
            raise
    poll_until(lambda: config.get().license_info and config.license_info.instance_count == license_info['instance_count'],
               interval=1, timeout=90)


def delete_license_until_effective(config):
    if config.is_awx_license:
        return
    log.info('Deleting current license...')
    config.delete()
    poll_until(lambda: not config.get().license_info, interval=1, timeout=90)
