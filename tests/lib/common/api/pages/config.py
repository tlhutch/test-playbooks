import base


class Config_Page(base.Base):
    base_url = '/api/v1/config/'
    version = property(base.json_getter('version'), base.json_setter('version'))
    license_info = property(base.json_getter('license_info'), base.json_setter('license_info'))
    ansible_version = property(base.json_getter('ansible_version'), base.json_setter('ansible_version'))
    time_zone = property(base.json_getter('time_zone'), base.json_setter('time_zone'))

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
