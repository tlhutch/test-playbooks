from selenium.webdriver.common.by import By

from common.ui.pages.base import TowerCrudPage
from common.ui.pages.forms import FormPanel
from common.ui.pages.forms import SelectDropDown
from common.ui.pages.forms import Password


class Credentials(TowerCrudPage):

    _path = '/#/credentials/{index}'

    @property
    def details(self):
        return CredDetails(self)

    @property
    def forms(self):
        subforms = (
            'machine',
            'openstack',
            'aws',
            'gce',
            'azure_classic',
            'azure_resource_manager',
            'rackspace',
            'vmware_vcenter',
            'source_control',
            'satellite_v6',
            'cloudforms',
            'network',)

        for form in subforms:
            yield getattr(self.details, form)


class CredDetails(FormPanel):

    _region_spec = {
        'description': {
            'region_type': 'text_input',
            'root_locator': (
                (By.CSS_SELECTOR, 'label[for=description]'),
                (By.XPATH, '..'))
        },
        'name': {
            'region_type': 'text_input',
            'required': True,
            'root_locator': (
                (By.CSS_SELECTOR, 'label[for=name]'),
                (By.XPATH, '..'))
        },
        'organization': {
            'region_type': 'lookup',
            'root_locator': (
                (By.CSS_SELECTOR, 'label[for=organization]'),
                (By.XPATH, '..'))
        },
    }

    _kind = ((By.CSS_SELECTOR, 'label[for=kind]'), (By.XPATH, '..'))

    @property
    def kind(self):
        return SelectDropDown(self.page, root_locator=self._kind)

    @property
    def machine(self):
        self.kind.select('Machine')
        return MachineDetails(self.page)

    @property
    def openstack(self):
        self.kind.select('OpenStack')
        return OpenStackDetails(self.page)

    @property
    def source_control(self):
        self.kind.select('Source Control')
        return SourceControlDetails(self.page)

    @property
    def rackspace(self):
        self.kind.select('Rackspace')
        return RackspaceDetails(self.page)

    @property
    def vmware_vcenter(self):
        self.kind.select('VMware vCenter')
        return VMWareDetails(self.page)

    @property
    def gce(self):
        self.kind.select('Google Compute Engine')
        return GCEDetails(self.page)

    @property
    def aws(self):
        self.kind.select('Amazon Web Services')
        return AWSDetails(self.page)

    @property
    def azure_classic(self):
        self.kind.select('Microsoft Azure Classic (deprecated)')
        return AzureClassicDetails(self.page)

    @property
    def azure_resource_manager(self):
        self.kind.select('Microsoft Azure Resource Manager')
        return AzureResourceManagerDetails(self.page)

    @property
    def satellite_v6(self):
        self.kind.select('Red Hat Satellite 6')
        return Satellite6Details(self.page)

    @property
    def cloudforms(self):
        self.kind.select('Red Hat CloudForms')
        return CloudFormsDetails(self.page)

    @property
    def network(self):
        self.kind.select('Network')
        return NetworkDetails(self.page)


class MachineDetails(CredDetails):

    _region_spec = {
        'username': {
            'region_type': 'text_input',
            'root_locator': (
                (By.CSS_SELECTOR, 'label[for=username]'),
                (By.XPATH, '..'))
        },
        'password': {
            'region_type': 'password',
            'root_locator': (
                (By.CSS_SELECTOR, 'label[for=ssh_password]'),
                (By.XPATH, '..'))
        },
        'ask_password': {
            'region_type': 'checkbox',
            'root_locator': (
                (By.CSS_SELECTOR, 'label[for=ssh_password]'),
                (By.XPATH, '..'))
        },
        'ssh_key_data': {
            'region_type': 'text_area',
            'root_locator': (
                (By.CSS_SELECTOR, 'label[for=ssh_key_data]'),
                (By.XPATH, '..'))
        },
        'become_method': {
            'region_type': 'select',
            'root_locator': (
                (By.CSS_SELECTOR, 'label[for=become_method]'),
                (By.XPATH, '..'))
        },
        'vault_password': {
            'region_type': 'password',
            'root_locator': (
                (By.CSS_SELECTOR, 'label[for=vault_password]'),
                (By.XPATH, '..'))
        },
        'ask_vault_password': {
            'region_type': 'checkbox',
            'root_locator': (
                (By.CSS_SELECTOR, 'label[for=vault_password]'),
                (By.XPATH, '..'))
        },
    }

    _region_spec = dict(
        CredDetails._region_spec.items() + _region_spec.items())


class OpenStackDetails(CredDetails):

    _region_spec = {
        'host': {
            'region_type': 'text_input',
            'required': True,
            'root_locator': (
                (By.CSS_SELECTOR, 'label[for=host]'),
                (By.XPATH, '..'))
        },
        'username': {
            'region_type': 'text_input',
            'required': True,
            'root_locator': (
                (By.CSS_SELECTOR, 'label[for=username]'),
                (By.XPATH, '..'))
        },
        'password': {
            'required': True,
            'region_type': 'password',
            'root_locator': (
                (By.CSS_SELECTOR, 'label[for=password]'),
                (By.XPATH, '..'))
        },
        'project': {
            'region_type': 'text_input',
            'required': True,
            'root_locator': (
                (By.CSS_SELECTOR, 'label[for=project]'),
                (By.XPATH, '..'))
        },
        'domain': {
            'region_type': 'text_input',
            'root_locator': (
                (By.CSS_SELECTOR, 'label[for=domain]'),
                (By.XPATH, '..'))
        },

    }

    _region_spec = dict(
        CredDetails._region_spec.items() + _region_spec.items())


class SourceControlDetails(CredDetails):

    _region_spec = {
        'username': {
            'region_type': 'text_input',
            'root_locator': (
                (By.CSS_SELECTOR, 'label[for=username]'),
                (By.XPATH, '..'))
        },
        'ssh_key_data': {
            'region_type': 'text_area',
            'root_locator': (
                (By.CSS_SELECTOR, 'label[for=ssh_key_data]'),
                (By.XPATH, '..'))
        },
        'password': {
            'region_type': 'password',
            'root_locator': (
                (By.CSS_SELECTOR, 'label[for=password]'),
                (By.XPATH, '..'))
        },
    }

    _region_spec = dict(
        CredDetails._region_spec.items() + _region_spec.items())


class RackspaceDetails(CredDetails):

    _region_spec = {
        'username': {
            'region_type': 'text_input',
            'required': True,
            'root_locator': (
                (By.CSS_SELECTOR, 'label[for=username]'),
                (By.XPATH, '..'))
        },
        'api_key': {
            'region_type': 'password',
            'required': True,
            'root_locator': (
                (By.CSS_SELECTOR, 'label[for=api_key]'),
                (By.XPATH, '..'))
        },

    }

    _region_spec = dict(
        CredDetails._region_spec.items() + _region_spec.items())


class VMWareDetails(CredDetails):

    _region_spec = {
        'host': {
            'region_type': 'text_input',
            'required': True,
            'root_locator': (
                (By.CSS_SELECTOR, 'label[for=host]'),
                (By.XPATH, '..'))
        },
        'username': {
            'region_type': 'text_input',
            'required': True,
            'root_locator': (
                (By.CSS_SELECTOR, 'label[for=username]'),
                (By.XPATH, '..'))
        },
        'password': {
            'region_type': 'password',
            'required': True,
            'root_locator': (
                (By.CSS_SELECTOR, 'label[for=password]'),
                (By.XPATH, '..'))
        },

    }

    _region_spec = dict(
        CredDetails._region_spec.items() + _region_spec.items())


class AzureClassicDetails(CredDetails):

    _region_spec = {
        'subscription_id': {
            'region_type': 'text_input',
            'required': True,
            'root_locator': (
                (By.CSS_SELECTOR, 'label[for=subscription]'),
                (By.XPATH, '..'))
        },
        'ssh_key_data': {
            'region_type': 'text_area',
            'required': True,
            'root_locator': (
                (By.CSS_SELECTOR, 'label[for=ssh_key_data]'),
                (By.XPATH, '..'))
        },
    }

    _region_spec = dict(
        CredDetails._region_spec.items() + _region_spec.items())


class AzureResourceManagerDetails(CredDetails):

    _region_spec = {
        'subscription_id': {
            'region_type': 'text_input',
            'required': True,
            'root_locator': (
                (By.CSS_SELECTOR, 'label[for=subscription]'),
                (By.XPATH, '..'))
        },
        'username': {
            'region_type': 'text_input',
            'required': True,
            'root_locator': (
                (By.CSS_SELECTOR, 'label[for=username]'),
                (By.XPATH, '..'))
        },
        'password': {
            'region_type': 'password',
            'required': True,
            'root_locator': (
                (By.CSS_SELECTOR, 'label[for=password]'),
                (By.XPATH, '..'))
        },
        'client_id': {
            'region_type': 'text_input',
            'required': True,
            'root_locator': (
                (By.CSS_SELECTOR, 'label[for=client]'),
                (By.XPATH, '..'))
        },
        'client_secret': {
            'region_type': 'password',
            'required': True,
            'root_locator': (
                (By.CSS_SELECTOR, 'label[for=secret]'),
                (By.XPATH, '..'))
        },
        'tenant_id': {
            'region_type': 'text_input',
            'required': True,
            'root_locator': (
                (By.CSS_SELECTOR, 'label[for=tenant]'),
                (By.XPATH, '..'))
        },

    }

    _region_spec = dict(
        CredDetails._region_spec.items() + _region_spec.items())


class GCEDetails(CredDetails):

    _region_spec = {
        'email_address': {
            'region_type': 'email',
            'required': True,
            'root_locator': (
                (By.CSS_SELECTOR, 'label[for=email_address]'),
                (By.XPATH, '..'))
        },
        'project': {
            'region_type': 'text_input',
            'required': False,
            'root_locator': (
                (By.CSS_SELECTOR, 'label[for=project]'),
                (By.XPATH, '..'))
        },
        'ssh_key_data': {
            'region_type': 'text_area',
            'required': True,
            'root_locator': (
                (By.CSS_SELECTOR, 'label[for=ssh_key_data]'),
                (By.XPATH, '..'))
        },
    }

    _region_spec = dict(
        CredDetails._region_spec.items() + _region_spec.items())


class AWSDetails(CredDetails):

    _region_spec = {
        'access_key': {
            'region_type': 'text_input',
            'required': True,
            'root_locator': (
                (By.CSS_SELECTOR, 'label[for=access_key]'),
                (By.XPATH, '..'))
        },
        'secret_key': {
            'region_type': 'password',
            'required': True,
            'root_locator': (
                (By.CSS_SELECTOR, 'label[for=secret_key]'),
                (By.XPATH, '..'))
        },
        'security_token': {
            'region_type': 'password',
            'root_locator': (
                (By.CSS_SELECTOR, 'label[for=security_token]'),
                (By.XPATH, '..'))
        },

    }

    _region_spec = dict(
        CredDetails._region_spec.items() + _region_spec.items())


class Satellite6Details(CredDetails):

    _region_spec = {
        'username': {
            'region_type': 'text_input',
            'required': True,
            'root_locator': (
                (By.CSS_SELECTOR, 'label[for=username]'),
                (By.XPATH, '..'))
        },
        'password': {
            'region_type': 'password',
            'required': True,
            'root_locator': (
                (By.CSS_SELECTOR, 'label[for=password]'),
                (By.XPATH, '..'))
        },
    }

    _region_spec = dict(
        CredDetails._region_spec.items() + _region_spec.items())


class CloudFormsDetails(CredDetails):

    _region_spec = {
        'username': {
            'region_type': 'text_input',
            'required': True,
            'root_locator': (
                (By.CSS_SELECTOR, 'label[for=username]'),
                (By.XPATH, '..'))
        },
        'password': {
            'region_type': 'password',
            'required': True,
            'root_locator': (
                (By.CSS_SELECTOR, 'label[for=password]'),
                (By.XPATH, '..'))
        },
    }

    _region_spec = dict(
        CredDetails._region_spec.items() + _region_spec.items())


class NetworkDetails(CredDetails):

    _region_spec = {
        'username': {
            'region_type': 'text_input',
            'required': True,
            'root_locator': (
                (By.CSS_SELECTOR, 'label[for=username]'),
                (By.XPATH, '..'))
        },
        'password': {
            'region_type': 'password',
            'required': True,
            'root_locator': (
                (By.CSS_SELECTOR, 'label[for=password]'),
                (By.XPATH, '..'))
        },
        'ssh_key': {
            'region_type': 'text_area',
            'required': False,
            'root_locator': (
                (By.CSS_SELECTOR, 'label[for=ssh_key_data]'),
                (By.XPATH, '..'))
        },
        'authorize': {
            'region_type': 'checkbox',
            'required': False,
            'root_locator': (
                (By.ID, 'credential_authorize_chbox'),
                (By.XPATH, '..'),
                (By.XPATH, '..'))
        },
    }

    _region_spec = dict(
        CredDetails._region_spec.items() + _region_spec.items())

    _auth_password = (
        (By.CSS_SELECTOR, 'label[for=authorize_password]'),
        (By.XPATH, '..'))

    @property
    def auth_password(self):
        self.authorize.select(True)
        return Password(self.page, root_locator=self._auth_password)
