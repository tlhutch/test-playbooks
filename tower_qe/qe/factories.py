import json
import os
import re

from Crypto.PublicKey import RSA
import factory
import fauxfactory

from qe.api.page_factory import PageFactory

from qe.api.pages import (Credential, Group, Host, Inventory, JobTemplate, Organization, Project,
                          User, Team, Label, InventoryScript, WorkflowJobTemplateNodes, WorkflowJobTemplates)


# TODO: standardize global project configuration for tower-qa
DEFAULT_PASSWORD = 'fo0m4nchU'
URL_PROJECT_GIT = 'https://github.com/jlaska/ansible-playbooks.git'
URL_PROJECT_HG = 'https://bitbucket.org/jlaska/ansible-helloworld'


class OrganizationFactory(PageFactory):
    class Meta:
        model = Organization
        inline_args = ('request',)

    name = factory.LazyFunction(fauxfactory.gen_alphanumeric)
    description = factory.LazyFunction(fauxfactory.gen_alphanumeric)


class LabelFactory(PageFactory):
    class Meta:
        model = Label
        inline_args = ('request',)
        resources = ('organization',)

    organization = factory.SubFactory(
        OrganizationFactory, request=factory.SelfAttribute('..request'))
    name = factory.LazyFunction(fauxfactory.gen_alphanumeric)
    description = factory.LazyFunction(fauxfactory.gen_utf8)


class ProjectFactory(PageFactory):
    class Meta:
        model = Project
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
            obj.get_related('current_update').wait_until_completed()


class UserFactory(PageFactory):
    class Meta:
        model = User
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
            org.add_user(obj)


class TeamFactory(PageFactory):
    class Meta:
        model = Team
        inline_args = ('request',)
        resources = ('organization',)

    organization = factory.SubFactory(
        OrganizationFactory, request=factory.SelfAttribute('..request'))
    name = factory.LazyFunction(fauxfactory.gen_alphanumeric)
    description = factory.LazyFunction(fauxfactory.gen_alphanumeric)


class CredentialFactory(PageFactory):
    class Meta:
        model = Credential
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
        model = Inventory
        inline_args = ('request',)
        resources = ('organization',)
    localhost = factory.RelatedFactory(
        'qe.factories.HostFactory',
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
        model = Host
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
        model = Group
        inline_args = ('request',)
        resources = ('inventory',)
    inventory = factory.SubFactory(
        InventoryFactory,
        request=factory.SelfAttribute('..request'))
    name = factory.LazyFunction(fauxfactory.gen_alphanumeric)
    description = factory.LazyFunction(fauxfactory.gen_alphanumeric)


class InventoryScriptFactory(PageFactory):
    class Meta:
        model = InventoryScript
        inline_args = ('request',)
        resources = ('organization',)
    organization = factory.SubFactory(
        OrganizationFactory,
        request=factory.SelfAttribute('..request'))
    name = factory.LazyFunction(fauxfactory.gen_alphanumeric)
    description = factory.LazyFunction(fauxfactory.gen_alphanumeric)

    @factory.LazyAttribute
    def script(self):
        script = '\n'.join([
            u'#!/usr/bin/env python',
            u'# -*- coding: utf-8 -*-',
            u'import json',
            u'inventory = dict()',
            u'inventory["{0}"] = list()',
            u'inventory["{0}"].append("{1}")',
            u'inventory["{0}"].append("{2}")',
            u'inventory["{0}"].append("{3}")',
            u'inventory["{0}"].append("{4}")',
            u'inventory["{0}"].append("{5}")',
            u'print json.dumps(inventory)'
        ])
        group_name = re.sub(r"[\']", "", u"group-%s" % fauxfactory.gen_utf8())
        host_names = [re.sub(r"[\':]", "", u"host-%s" % fauxfactory.gen_utf8()) for _ in xrange(5)]

        return script.format(group_name, *host_names)


class JobTemplateFactory(PageFactory):
    class Meta:
        model = JobTemplate
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


class WorkflowJobTemplateNodeFactory(PageFactory):
    class Meta:
        model = WorkflowJobTemplateNodes
        inline_args = ('request',)
        resources = ('unified_job_template',)

    # Note: By default, not instantiating node with reference to workflow job template

    unified_job_template = factory.SubFactory(
        JobTemplateFactory,
        request=factory.SelfAttribute('..request'))


class WorkflowJobTemplateFactory(PageFactory):
    class Meta:
        model = WorkflowJobTemplates
        inline_args = ('request',)

    name = factory.LazyFunction(fauxfactory.gen_alphanumeric)
    description = factory.LazyFunction(fauxfactory.gen_alphanumeric)
