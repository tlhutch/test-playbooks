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
URL_PROJECT_GIT = 'https://github.com/jlaska/ansible-playbooks.git'
URL_PROJECT_HG = 'https://bitbucket.org/jlaska/ansible-helloworld'


class OrganizationFactory(PageFactory):
    class Meta:
        model = Organizations_Page
        inline_args = ('request',)
        get_or_create = ('name',)

    name = 'Random organization %s' % fauxfactory.gen_utf8()
    description = factory.LazyFunction(fauxfactory.gen_utf8)


class ProjectFactory(PageFactory):
    class Meta:
        model = Projects_Page
        inline_args = ('request',)
        get_or_create = ('name',)
        exclude = ('related_organization',)

    related_organization = factory.SubFactory(
        OrganizationFactory, request=factory.SelfAttribute('..request'))

    name = factory.LazyFunction(fauxfactory.gen_utf8)
    organization = factory.SelfAttribute('related_organization.id')
    scm_type = 'git'

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
        if create:
            update = obj.get_related('project_updates', order_by="-id")
            if val or val is None:
                # we end up here if keyword argument wait=True was used when
                # calling the factory or if the wait keyword was not used
                try:
                    update.results.pop().wait_until_completed()
                except IndexError:
                    raise IndexError('No project updates found')


class UserFactory(PageFactory):
    class Meta:
        model = Users_Page
        inline_args = ('request',)
        get_or_create = ('username',)

    username = factory.LazyFunction(fauxfactory.gen_alphanumeric)
    password = 'fo0m4nchU'
    is_superuser = False
    first_name = factory.LazyFunction(fauxfactory.gen_utf8)
    last_name = factory.LazyFunction(fauxfactory.gen_utf8)
    email = factory.LazyFunction(fauxfactory.gen_email)

    @factory.post_generation
    def related_organization(obj, create, org):
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
        exclude = ('related_organization',)

    related_organization = factory.SubFactory(
        OrganizationFactory, request=factory.SelfAttribute('..request'))

    name = factory.Sequence(lambda n: 'team_{}'.format(n))
    description = factory.LazyFunction(fauxfactory.gen_utf8)
    organization = factory.SelfAttribute('related_organization.id')


class CredentialFactory(PageFactory):
    class Meta:
        model = Credentials_Page
        inline_args = ('request',)
        get_or_create = ('name',)
        exclude = ('related_organization',)

    related_organization = factory.SubFactory(
        OrganizationFactory, request=factory.SelfAttribute('..request'))

    name = factory.LazyFunction(fauxfactory.gen_utf8)
    description = factory.LazyFunction(fauxfactory.gen_utf8)
    organization = factory.SelfAttribute('related_organization.id')
    username = factory.LazyFunction(fauxfactory.gen_alphanumeric)
    kind = 'ssh'

    @factory.LazyAttribute
    def ssh_key_data(self):
        if self.kind == 'ssh':
            return RSA.generate(2048, os.urandom).exportKey('PEM')


class InventoryFactory(PageFactory):
    class Meta:
        model = Inventories_Page
        inline_args = ('request',)
        get_or_create = ('name',)
        exclude = ('related_organization',)

    related_organization = factory.SubFactory(
        OrganizationFactory, request=factory.SelfAttribute('..request'))

    name = factory.LazyFunction(fauxfactory.gen_utf8)
    description = factory.LazyFunction(fauxfactory.gen_utf8)
    organization = factory.SelfAttribute('related_organization.id')


class HostFactory(PageFactory):
    class Meta:
        model = Hosts_Page
        inline_args = ('request',)
        get_or_create = ('name',)
        exclude = ('related_inventory',)

    related_inventory = factory.SubFactory(
        InventoryFactory, request=factory.SelfAttribute('..request'))

    name = factory.LazyFunction(fauxfactory.gen_utf8)
    description = factory.LazyFunction(fauxfactory.gen_utf8)
    variables = json.dumps({
        'ansible_ssh_host': '127.0.0.1',
        'ansible_connection': 'local',
    }),
    inventory = factory.SelfAttribute('related_inventory.id')


class GroupFactory(PageFactory):
    class Meta:
        model = Groups_Page
        inline_args = ('request',)
        get_or_create = ('name',)
        exclude = ('related_inventory', 'group_credential',)

    related_inventory = factory.SubFactory(
        InventoryFactory,
        request=factory.SelfAttribute('..request'))
    group_credential = factory.SubFactory(
        CredentialFactory,
        request=factory.SelfAttribute('..request'))

    name = factory.LazyFunction(fauxfactory.gen_utf8)
    description = factory.LazyFunction(fauxfactory.gen_utf8)
    inventory = factory.SelfAttribute('related_inventory.id')
    credential = factory.SelfAttribute('group_credential.id')


class JobTemplateFactory(PageFactory):
    class Meta:
        model = Job_Templates_Page
        inline_args = ('request',)
        get_or_create = ('name',)
        exclude = ('localhost', 'related_project',
                   'related_inventory', 'related_credential',)
    related_project = factory.SubFactory(
        ProjectFactory,
        request=factory.SelfAttribute('..request'))
    related_credential = factory.SubFactory(
        CredentialFactory,
        request=factory.SelfAttribute('..request'))
    related_inventory = factory.SubFactory(
        InventoryFactory,
        request=factory.SelfAttribute('..request'))
    localhost = factory.SubFactory(
        HostFactory,
        name='localhost',
        request=factory.SelfAttribute('..request'),
        related_inventory=factory.SelfAttribute('..related_inventory'),
        variables=json.dumps({
            'ansible_ssh_host': '127.0.0.1',
            'ansible_connection': 'local',
        }),
    )
    name = factory.LazyFunction(fauxfactory.gen_utf8)
    description = factory.LazyFunction(fauxfactory.gen_utf8)
    job_type = 'run'
    playbook = 'site.yml'
    project = factory.SelfAttribute('related_project.id')
    credential = factory.SelfAttribute('related_credential.id')
    inventory = factory.SelfAttribute('related_inventory.id')
