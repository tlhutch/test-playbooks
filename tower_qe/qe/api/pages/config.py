import sys

from qe.tower.license import generate_license
from qe.api import resources
import base


class Config(base.Base):

    @property
    def is_aws_license(self):
        return self.license_info.get('is_aws', False) or \
            'ami-id' in self.license_info or \
            'instance-id' in self.license_info

    @property
    def is_demo_license(self):
        return self.license_info.get('demo', False) or \
            self.license_info.get('key_present', False)

    @property
    def is_valid_license(self):
        return self.license_info.get('valid_key', False) and \
            'license_key' in self.license_info and \
            'instance_count' in self.license_info

    @property
    def is_trial_license(self):
        return self.is_valid_license and \
            self.license_info.get('trial', False)

    @property
    def is_legacy_license(self):
        return self.is_valid_license and \
            self.license_info.get('license_type', None) == 'legacy'

    @property
    def is_basic_license(self):
        return self.is_valid_license and \
            self.license_info.get('license_type', None) == 'basic'

    @property
    def is_enterprise_license(self):
        return self.is_valid_license and \
            self.license_info.get('license_type', None) == 'enterprise'

    @property
    def features(self):
        '''returns a list of enabled license features'''
        return [k for k, v in self.license_info.get('features', {}).items() if v]

    def install_license(self, instance_count=sys.maxint, days=365, license_type='enterprise', **kw):
        license = generate_license(instance_count=instance_count,
                                   days=days,
                                   license_type=license_type, **kw)
        self.post(license)
        self.get()
        return self.is_valid_license

base.register_page(resources.v1_config, Config)

# backwards compatibility
Config_Page = Config
