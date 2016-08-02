import json
import os

from Crypto.PublicKey import RSA
import factory
import fauxfactory
import pytest

from common.api.page_factory import PageFactory
from common.exceptions import NoContent_Exception

from common.api.pages import (
    Credentials_Page,
    Groups_Page,
    Hosts_Page,
    Inventories_Page,
    Job_Templates_Page,
    Organizations_Page,
    Projects_Page,
    Users_Page,
    Teams_Page,
)


# TODO: standardize global project configuration for tower-qa
DEFAULT_PASSWORD = 'fo0m4nchU'
URL_PROJECT_GIT = 'https://github.com/jlaska/ansible-playbooks.git'
URL_PROJECT_HG = 'https://bitbucket.org/jlaska/ansible-helloworld'


class OrganizationFactory(PageFactory):
    class Meta:
        model = Organizations_Page
        inline_args = ('request',)

    name = factory.LazyFunction(fauxfactory.gen_alphanumeric)
    description = factory.LazyFunction(fauxfactory.gen_alphanumeric)


class ProjectFactory(PageFactory):
    class Meta:
        model = Projects_Page
        inline_args = ('request',)
        resources = ('organization',)

    organization = factory.SubFactory(
        OrganizationFactory, request=factory.SelfAttribute('..request'))

    scm_type = 'git'
    name = factory.LazyFunction(fauxfactory.gen_alphanumeric)

    @factory.LazyAttribute
    def scm_url(self):
        if self.scm_type == 'git':
            return URL_PROJECT_GIT
        elif self.scm_type == 'hg':
            return URL_PROJECT_HG

    @factory.post_generation
    def wait(obj, create, val, **kwargs):
        """Wait for project update completion after creation. Use keyword
        argument wait=False when invoking the factory to skip.
        """
        if create and val in (True, None):
            obj.update().wait_until_completed()


class UserFactory(PageFactory):
    class Meta:
        model = Users_Page
        inline_args = ('request',)

    username = factory.LazyFunction(fauxfactory.gen_alphanumeric)
    password = DEFAULT_PASSWORD
    is_superuser = False
    first_name = factory.LazyFunction(fauxfactory.gen_alphanumeric)
    last_name = factory.LazyFunction(fauxfactory.gen_alphanumeric)
    email = factory.LazyFunction(fauxfactory.gen_email)

    @factory.post_generation
    def organization(obj, create, org):
        """When using this factory, provide an organization model
        using the organization keyword to associate the user with
        the organization after creation.
        """
        if create and org is not None:
            with pytest.raises(NoContent_Exception):
                org.get_related('users').post({'id': obj.id})


class TeamFactory(PageFactory):
    class Meta:
        model = Teams_Page
        inline_args = ('request',)
        resources = ('organization',)

    organization = factory.SubFactory(
        OrganizationFactory, request=factory.SelfAttribute('..request'))
    name = factory.LazyFunction(fauxfactory.gen_alphanumeric)
    description = factory.LazyFunction(fauxfactory.gen_alphanumeric)


class CredentialFactory(PageFactory):
    class Meta:
        model = Credentials_Page
        inline_args = ('request',)
        resources = ('organization', 'user', 'team')

    user = None
    team = None
    organization = factory.SubFactory(
        OrganizationFactory,
        request=factory.SelfAttribute('..request'))

    kind = 'ssh'
    name = factory.LazyFunction(fauxfactory.gen_alphanumeric)
    description = factory.LazyFunction(fauxfactory.gen_alphanumeric)

    @factory.LazyAttribute
    def password(self):
        if self.kind == 'net':
            return DEFAULT_PASSWORD

    @factory.LazyAttribute
    def ssh_key_data(self):
        if self.kind in ('ssh', 'net'):
            return RSA.generate(2048, os.urandom).exportKey('PEM')


class InventoryFactory(PageFactory):
    class Meta:
        model = Inventories_Page
        inline_args = ('request',)
        resources = ('organization',)
    localhost = factory.RelatedFactory(
        'common.factories.HostFactory',
        factory_related_name='inventory',
        request=factory.SelfAttribute('inventory.testsetup.request'),
        name='localhost')
    organization = factory.SubFactory(
        OrganizationFactory,
        request=factory.SelfAttribute('..request'))
    name = factory.LazyFunction(fauxfactory.gen_alphanumeric)
    description = factory.LazyFunction(fauxfactory.gen_alphanumeric)


class HostFactory(PageFactory):
    class Meta:
        model = Hosts_Page
        inline_args = ('request',)
        resources = ('inventory',)
    inventory = factory.SubFactory(
        InventoryFactory,
        request=factory.SelfAttribute('..request'))
    variables = json.dumps({
        'ansible_ssh_host': '127.0.0.1',
        'ansible_connection': 'local'
    })
    name = factory.LazyFunction(fauxfactory.gen_alphanumeric)
    description = factory.LazyFunction(fauxfactory.gen_alphanumeric)


class GroupFactory(PageFactory):
    class Meta:
        model = Groups_Page
        inline_args = ('request',)
        resources = ('inventory',)
    inventory = factory.SubFactory(
        InventoryFactory,
        request=factory.SelfAttribute('..request'))
    name = factory.LazyFunction(fauxfactory.gen_alphanumeric)
    description = factory.LazyFunction(fauxfactory.gen_alphanumeric)


class JobTemplateFactory(PageFactory):
    class Meta:
        model = Job_Templates_Page
        inline_args = ('request',)
        exclude = ('organization',)
        resources = ('project', 'inventory', 'credential', 'organization',)
    organization = factory.SubFactory(
        OrganizationFactory,
        request=factory.SelfAttribute('..request'))
    project = factory.SubFactory(
        ProjectFactory,
        request=factory.SelfAttribute('..request'),
        organization=factory.SelfAttribute('..organization'),
        wait=True)
    credential = factory.SubFactory(
        CredentialFactory,
        request=factory.SelfAttribute('..request'),
        organization=factory.SelfAttribute('..organization'))
    inventory = factory.SubFactory(
        InventoryFactory,
        request=factory.SelfAttribute('..request'),
        organization=factory.SelfAttribute('..organization'))
    job_type = 'run'
    playbook = 'ping.yml'
    name = factory.LazyFunction(fauxfactory.gen_alphanumeric)
    description = factory.LazyFunction(fauxfactory.gen_alphanumeric)
