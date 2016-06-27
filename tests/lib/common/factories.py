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
        get_or_create = ('name',)

    name = factory.LazyFunction(fauxfactory.gen_alphanumeric)
    description = factory.LazyFunction(fauxfactory.gen_utf8)


class ProjectFactory(PageFactory):
    class Meta:
        model = Projects_Page
        inline_args = ('request',)
        get_or_create = ('name',)
        related = ('organization',)

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
        get_or_create = ('username',)

    username = factory.LazyFunction(fauxfactory.gen_alphanumeric)
    password = DEFAULT_PASSWORD
    is_superuser = False
    first_name = factory.LazyFunction(fauxfactory.gen_utf8)
    last_name = factory.LazyFunction(fauxfactory.gen_utf8)
    email = factory.LazyFunction(fauxfactory.gen_email)

    @factory.post_generation
    def organization(obj, create, org):
        """When using this factory, provide an organization model
        using the related_organization keyword to associate the
        user to the organization after creation.
        """
        if create and org is not None:
            with pytest.raises(NoContent_Exception):
                org.get_related('users').post({'id': obj.id})


class TeamFactory(PageFactory):
    class Meta:
        model = Teams_Page
        inline_args = ('request',)
        get_or_create = ('name',)
        related = ('organization',)

    organization = factory.SubFactory(
        OrganizationFactory, request=factory.SelfAttribute('..request'))
    name = factory.Sequence(lambda n: 'team_{}'.format(n))
    description = factory.LazyFunction(fauxfactory.gen_utf8)


class CredentialFactory(PageFactory):
    class Meta:
        model = Credentials_Page
        inline_args = ('request',)
        get_or_create = ('name',)
        related = ('organization',)

    organization = factory.SubFactory(
        OrganizationFactory, request=factory.SelfAttribute('..request'))

    kind = 'ssh'
    name = factory.LazyFunction(fauxfactory.gen_alphanumeric)
    description = factory.LazyFunction(fauxfactory.gen_utf8)
    username = factory.LazyFunction(fauxfactory.gen_alphanumeric)

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
        get_or_create = ('name',)
        related = ('organization',)

    organization = factory.SubFactory(
        OrganizationFactory, request=factory.SelfAttribute('..request'))
    name = factory.LazyFunction(fauxfactory.gen_alphanumeric)
    description = factory.LazyFunction(fauxfactory.gen_utf8)


class HostFactory(PageFactory):
    class Meta:
        model = Hosts_Page
        inline_args = ('request',)
        get_or_create = ('name',)
        related = ('inventory',)

    inventory = factory.SubFactory(
        InventoryFactory,
        request=factory.SelfAttribute('..request'))

    name = factory.LazyFunction(fauxfactory.gen_alphanumeric)
    description = factory.LazyFunction(fauxfactory.gen_utf8)
    variables = json.dumps({
        'ansible_ssh_host': '127.0.0.1',
        'ansible_connection': 'local',
    }),


class GroupFactory(PageFactory):
    class Meta:
        model = Groups_Page
        inline_args = ('request',)
        get_or_create = ('name',)
        related = ('inventory', 'credential',)

    inventory = factory.SubFactory(
        InventoryFactory,
        request=factory.SelfAttribute('..request'))
    credential = factory.SubFactory(
        CredentialFactory,
        request=factory.SelfAttribute('..request'))

    name = factory.LazyFunction(fauxfactory.gen_alphanumeric)
    description = factory.LazyFunction(fauxfactory.gen_utf8)


class JobTemplateFactory(PageFactory):
    class Meta:
        model = Job_Templates_Page
        inline_args = ('request',)
        get_or_create = ('name',)
        exclude = ('organization', 'localhost')
        related = ('project', 'inventory', 'credential', 'organization',)
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
    localhost = factory.SubFactory(
        HostFactory,
        name='localhost',
        request=factory.SelfAttribute('..request'),
        inventory=factory.SelfAttribute('..inventory'),
        variables=json.dumps({
            'ansible_ssh_host': '127.0.0.1',
            'ansible_connection': 'local',
        }),
    )
    job_type = 'run'
    playbook = 'ping.yml'
    name = factory.LazyFunction(fauxfactory.gen_alphanumeric)
    description = factory.LazyFunction(fauxfactory.gen_utf8)
