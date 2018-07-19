import logging

import pytest

import towerkit
from towerkit.api.resources import resources
from tests.api import Base_Api_Test


log = logging.getLogger(__name__)


def escape_pluses(name):
    """escape plusses for named urls and return a bytestring"""
    if isinstance(name, unicode):
        name = name.encode('utf8')
    return name.replace('+', '[+]')


def make_api_url(resource_name, format_string, *params):
    url_template = '{0.v2_%s}%s/' % (resource_name, format_string)
    return url_template.format(resources, *[escape_pluses(param) for param in params])


@pytest.mark.api
@pytest.mark.usefixtures('authtoken', 'install_enterprise_license_unlimited')
class TestNamedURLs(Base_Api_Test):

    def assert_resource_available_by_name(self, resource, named_url):
        # refetch the resource to get the latest vesrsion.
        resource.get()
        resource_by_name = resource.walk(named_url)

        if hasattr(resource, 'name'):
            # User and Instance have no name attribute.
            assert resource.name == resource_by_name.name
        if hasattr(resource, 'hostname'):
            assert resource.hostname == resource_by_name.hostname
        if hasattr(resource, 'username'):
            assert resource.username == resource_by_name.username

        assert resource.id == resource_by_name.id
        assert resource.related == resource_by_name.related

        if hasattr(resource, 'summary_fields'):
            # Instance has no summary_fields
            assert resource.summary_fields == resource_by_name.summary_fields

        assert resource.related.named_url == named_url

    def test_named_url_formats(self, v2):
        # If this test fails then the named url formats have changed, which is potentially
        # backwards incompatible and needs to be checked (i.e. have url formats changed
        # unexpectedly).
        expected = {
            u'applications': u'<name>++<organization.name>',
            u'credential_types': u'<name>+<kind>',
            u'credentials': u'<name>++<credential_type.name>+<credential_type.kind>++<organization.name>',
            u'groups': u'<name>++<inventory.name>++<organization.name>',
            u'hosts': u'<name>++<inventory.name>++<organization.name>',
            u'instance_groups': u'<name>',
            u'instances': u'<hostname>',
            u'inventories': u'<name>++<organization.name>',
            u'inventory_scripts': u'<name>++<organization.name>',
            u'inventory_sources': u'<name>++<inventory.name>++<organization.name>',
            u'job_templates': u'<name>',
            u'labels': u'<name>++<organization.name>',
            u'notification_templates': u'<name>++<organization.name>',
            u'organizations': u'<name>',
            u'projects': u'<name>++<organization.name>',
            u'teams': u'<name>++<organization.name>',
            u'users': u'<username>',
            u'workflow_job_templates': u'<name>++<organization.name>'
        }

        settings = v2.settings.get().get_endpoint('named-url')
        assert settings['NAMED_URL_FORMATS'] == expected

        with pytest.raises(towerkit.exceptions.MethodNotAllowed):
            settings.post(dict(NAMED_URL_FORMATS={}))

        # implicit patch, this returns 200 but should do nothing
        settings.NAMED_URL_FORMATS = {}

        # refresh the settings
        settings.get()
        assert settings['NAMED_URL_FORMATS'] == expected

    def test_organization_host_inventory(self, factories):
        host = factories.v2_host()
        inventory = host.ds.inventory
        organization = inventory.ds.organization

        organization_url = make_api_url('organizations', '{1}', organization.name)
        host_url = make_api_url('hosts', '{1}++{2}++{3}', host.name, inventory.name, organization.name)
        inventory_url = make_api_url('inventories', '{1}++{2}', inventory.name, organization.name)
        self.assert_resource_available_by_name(organization, organization_url)
        self.assert_resource_available_by_name(host, host_url)
        self.assert_resource_available_by_name(inventory, inventory_url)

    def test_credential_types_credentials_user(self, admin_user, factories):
        cred = factories.v2_credential(name="network credentials-named-urls-test",
                                       description="network credential - named urls test",
                                       kind='net', user=admin_user, ssh_key_data=None, authorize_password=None)
        cred_type = cred.ds.credential_type
        organization = cred.ds.organization
        # we do this rather than using admin_user directly as we need the v2 version of the user
        user = cred.related.created_by.get()

        cred_url = make_api_url('credentials', '{1}++{2}+{3}++{4}', cred.name, cred_type.name, cred_type.kind, organization.name)
        cred_type_url = make_api_url('credential_types', '{1}+{2}', cred_type.name, cred_type.kind)
        user_url = make_api_url('users', '{1}', user.username)
        self.assert_resource_available_by_name(cred_type, cred_type_url)
        self.assert_resource_available_by_name(cred, cred_url)
        self.assert_resource_available_by_name(user, user_url)

    def test_credential_without_organization(self, factories):
        cred = factories.v2_credential(user=True, organization=False)
        cred_type = cred.ds.credential_type
        cred_url = make_api_url('credentials', '{1}++{2}+{3}++', cred.name, cred_type.name, cred_type.kind)
        self.assert_resource_available_by_name(cred, cred_url)

    def test_groups_inventory_sources_inventory_scripts(self, factories):
        source = factories.v2_inventory_source()
        inv_script = source.ds.inventory_script
        org = inv_script.ds.organization
        inventory = source.ds.inventory
        group = factories.v2_group(inventory=inventory)
        # manually update the inventory as we have changed it by creating the group
        inventory.get()

        group_url = make_api_url('groups', '{1}++{2}++{3}', group.name, inventory.name, org.name)
        source_url = make_api_url('inventory_sources', '{1}++{2}++{3}', source.name, inventory.name, org.name)
        script_url = make_api_url('inventory_scripts', '{1}++{2}', inv_script.name, org.name)
        self.assert_resource_available_by_name(group, group_url)
        self.assert_resource_available_by_name(source, source_url)
        self.assert_resource_available_by_name(inv_script, script_url)

    def test_instances_instance_groups(self, v2):
        # select the first default instance and instance group
        instance = v2.instances.get().results[0]
        instance_group = None
        for group in v2.instance_groups.get().results:
            # In HA, some of the instance groups have integer names which don't work with named urls
            if not group.name.isdigit():
                instance_group = group
                break
        assert instance_group is not None

        instance_url = make_api_url('instances', '{1}', instance.hostname)
        instance_group_url = make_api_url('instance_groups', '{1}', instance_group.name)
        self.assert_resource_available_by_name(instance, instance_url)
        self.assert_resource_available_by_name(instance_group, instance_group_url)

    def test_templates(self, factories):
        template = factories.v2_job_template()
        workflow_template = factories.v2_workflow_job_template()

        template_url = make_api_url('job_templates', '{1}', template.name)
        # Note that this workflow_template has a null organization
        workflow_template_url = make_api_url('workflow_job_templates', '{1}++', workflow_template.name)
        self.assert_resource_available_by_name(template, template_url)
        self.assert_resource_available_by_name(workflow_template, workflow_template_url)

        # add an organization to the workflow template
        org = factories.v2_organization()
        workflow_template.organization = org.id
        workflow_template_url = make_api_url('workflow_job_templates', '{1}++{2}', workflow_template.name, org.name)
        self.assert_resource_available_by_name(workflow_template, workflow_template_url)

    def test_labels(self, factories):
        label = factories.v2_label()
        org = label.ds.organization
        label_url = make_api_url('labels', '{1}++{2}', label.name, org.name)
        self.assert_resource_available_by_name(label, label_url)

    def test_notification_templates(self, factories):
        template = factories.v2_notification_template(notification_type="email")
        org = template.ds.organization
        template_url = make_api_url('notification_templates', '{1}++{2}', template.name, org.name)
        self.assert_resource_available_by_name(template, template_url)

    def test_projects(self, factories):
        project = factories.v2_project()
        org = project.ds.organization
        project_url = make_api_url('projects', '{1}++{2}', project.name, org.name)
        self.assert_resource_available_by_name(project, project_url)

    def test_teams(self, factories):
        team = factories.v2_team()
        org = team.ds.organization
        team_url = make_api_url('teams', '{1}++{2}', team.name, org.name)
        self.assert_resource_available_by_name(team, team_url)

    def test_named_urls_v2_api_only(self, factories):
        host = factories.host()
        inventory = host.ds.inventory
        organization = inventory.ds.organization
        named_url = '{0.v1_inventories}{1}++{2}/'.format(resources, escape_pluses(inventory.name), escape_pluses(organization.name))
        with pytest.raises(towerkit.exceptions.NotFound):
            inventory.walk(named_url)

    def test_named_url_related_resource(self, factories):
        # related resources should be accessible via the named url
        host = factories.v2_host()
        inventory = host.ds.inventory
        org = inventory.ds.organization

        hosts_url = make_api_url('inventories', '{1}++{2}', inventory.name, org.name) + 'hosts/'
        hosts_by_related_name = inventory.walk(hosts_url)
        assert len(hosts_by_related_name.results) == 1
        host_by_name = hosts_by_related_name.results[0]
        assert host.id == host_by_name.id

    def test_integer_names(self, factories):
        # integer names should not be accessible by named url.
        username = "912345"
        user = factories.v2_user(username=username)
        user_url = make_api_url('users', '{1}', username)
        with pytest.raises(towerkit.exceptions.NotFound):
            user.walk(user_url)
