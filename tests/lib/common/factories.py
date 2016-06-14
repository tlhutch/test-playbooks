import json
import os

from Crypto.PublicKey import RSA
import factory
import fauxfactory

from common.api.page_factory import PageFactory

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

    name = 'Default'
    description = factory.LazyFunction(fauxfactory.gen_utf8)


class ProjectFactory(PageFactory):
    class Meta:
        model = Projects_Page
        inline_args = ('request',)
        get_or_create = ('name',)
        exclude = ('related_organization',)

    related_organization = factory.SubFactory(
        OrganizationFactory, request=factory.SelfAttribute('..request'))

    name = factory.Sequence(lambda n: 'project_{}'.format(n))
    organization = factory.SelfAttribute('related_organization.id')
    scm_type = 'git'

    @factory.LazyAttribute
    def scm_url(self):
        if self.scm_type == 'git':
            return URL_PROJECT_GIT
        elif self.scm_type == 'hg':
            return URL_PROJECT_HG

    @factory.post_generation
    def wait(self, create, extracted, **kwargs):
        """When using this factory, provide keyword argument wait=True
        to update the project and wait for it to be completed
        """
        if create and extracted:
            update = self.get_related('project_updates', order_by="-id")
            try:
                update.results.pop().wait_until_completed()
            except IndexError:
                raise IndexError('No project updates found')


class UserFactory(PageFactory):
    class Meta:
        model = Users_Page
        inline_args = ('request',)
        get_or_create = ('username',)
        exclude = ('related_organization',)

    related_organization = factory.SubFactory(
        OrganizationFactory, request=factory.SelfAttribute('..request'))

    username = factory.Sequence(lambda n: 'user_{}'.format(n))
    password = 'fo0m4nchU'
    is_superuser = False
    first_name = factory.LazyFunction(fauxfactory.gen_utf8)
    last_name = factory.LazyFunction(fauxfactory.gen_utf8)
    email = factory.LazyFunction(fauxfactory.gen_email)
    organization = factory.SelfAttribute('related_organization.id')


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
        exclude = ('owner',)

    owner = factory.SubFactory(
        UserFactory, request=factory.SelfAttribute('..request'))

    name = factory.Sequence(lambda n: 'credential_{}'.format(n))
    description = factory.LazyFunction(fauxfactory.gen_utf8)
    user = factory.SelfAttribute('owner.id')
    username = factory.SelfAttribute('owner.username')
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

    name = factory.Sequence(lambda n: 'inventory_{}'.format(n))
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

    name = factory.Sequence(lambda n: 'host_{}'.format(n))
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

    name = factory.Sequence(lambda n: 'group_{}'.format(n))
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
        wait=True,
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
    name = factory.Sequence(lambda n: 'job_template_{}'.format(n))
    description = factory.LazyFunction(fauxfactory.gen_utf8)
    job_type = 'run'
    playbook = 'site.yml'
    project = factory.SelfAttribute('related_project.id')
    credential = factory.SelfAttribute('related_credential.id')
    inventory = factory.SelfAttribute('related_inventory.id')
