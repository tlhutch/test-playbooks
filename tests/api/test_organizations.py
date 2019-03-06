import pytest
import towerkit.exceptions
from towerkit import utils
from tests.api import APITest
import fauxfactory


@pytest.fixture(scope="function", params=['job_template',
                                          'check_job_template',
                                          'org_user',
                                          'team',
                                          'org_admin',
                                          'inventory',
                                          'project'])
def related_organization_object(request):
    """Create organization_related_counts objects sequentially."""
    return request.getfixturevalue(request.param)


@pytest.mark.api
@pytest.mark.destructive
@pytest.mark.usefixtures('authtoken', 'install_enterprise_license_unlimited')
class Test_Organizations(APITest):
    """Verify the /users endpoint displays the expected information based on the current user"""

    def test_duplicate_organizations_disallowed(self, factories):
        org = factories.v2_organization()
        with pytest.raises(towerkit.exceptions.Duplicate) as e:
            factories.v2_organization(name=org.name)
        assert e.value[1]['name'] == ['Organization with this Name already exists.']

    def test_delete(self, api_organizations_pg, organization):
        """Verify that deleting an organization actually works."""
        # Delete the organization
        organization.delete()

        # assert the organization was deleted
        matches = api_organizations_pg.get(id=organization.id)
        assert matches.count == 0, "An organization was deleted, but is still visible from the /api/v1/organizations/ endpoint"

    def test_organization_related_counts(self, organization, related_organization_object, api_job_templates_pg):
        """Verify summary_fields 'related_field_counts' content."""
        # determine the expected JTs count
        #
        # note: the API determines the organization of a non-scan JT by looking at the organization of the JT project. For scan JTs, it
        # looks at the organization of the JT inventory instead.
        inventory_pg = organization.get_related('inventories')
        org_inventory_ids = [inv_pg.id for inv_pg in inventory_pg.results]
        project_pg = organization.get_related('projects')
        org_project_ids = [proj_pg.id for proj_pg in project_pg.results]

        params = dict(job_type='scan', inventory__in=-1)
        if org_inventory_ids:
            params['inventory__in'] = ','.join(str(entry) for entry in org_inventory_ids)
        scan_job_templates_count = api_job_templates_pg.get(**params).count

        params = dict(not__job_type='scan', project__in=-1)
        if org_project_ids:
            params['project__in'] = ','.join(str(entry) for entry in org_project_ids)
        other_job_templates_count = api_job_templates_pg.get(**params).count

        # check related_field_counts
        # note: there is no 'job_templates' get_related field so we handle job_templates differently
        related_field_counts = organization.get().summary_fields['related_field_counts']
        for key in related_field_counts.keys():
            if key != 'job_templates':
                assert related_field_counts[key] == organization.get_related(key).count, \
                    "Incorrect value for %s. Expected %s, got %s." % (key, organization.get_related(key).count, related_field_counts[key])

        job_templates_count = scan_job_templates_count + other_job_templates_count
        assert job_templates_count == related_field_counts['job_templates'], \
            "Incorrect value for job_templates. Expected %s, got %s." % (job_templates_count, related_field_counts['job_templates'])

    def test_organization_host_limits_do_not_allow_adding_too_many_hosts(self, factories):
        org = factories.v2_organization()
        org.max_hosts = 2
        inv = factories.v2_inventory(organization=org)
        [inv.add_host() for _ in range(2)]
        with pytest.raises(towerkit.exceptions.Forbidden) as e:
            inv.add_host()
        assert e.value.msg['detail'] == 'Organization host limit of 2 would be exceeded, 2 hosts active.'

    def test_organization_host_limits_apply_across_all_inventories(self, factories):
        org = factories.v2_organization()
        org.max_hosts = 2
        inv = factories.v2_inventory(organization=org)
        [inv.add_host() for _ in range(2)]
        inv2 = factories.v2_inventory(organization=org)
        with pytest.raises(towerkit.exceptions.Forbidden) as e:
            inv2.add_host()
        assert e.value.msg['detail'] == 'Organization host limit of 2 would be exceeded, 2 hosts active.'

    def test_organization_host_limits_allow_same_host_multiple_inventories(self, factories):
        org = factories.v2_organization()
        org.max_hosts = 2
        inv = factories.v2_inventory(organization=org)
        hosts = [inv.add_host() for _ in range(2)]
        inv2 = factories.v2_inventory(organization=org)
        factories.v2_host(name=hosts[1].name, inventory=inv2)
        utils.logged_sleep(5)
        assert inv.get().total_hosts == 2
        assert inv2.get().total_hosts == 1
        host_set = set()
        for i in org.get().related.inventories.get().results:
            for h in i.related.hosts.get().results:
                host_set.add(h.name)
        assert len(host_set) == 2

    def test_organization_host_limits_no_longer_apply_to_inventory_if_org_changed(self, factories):
        org = factories.v2_organization()
        org2 = factories.v2_organization()
        org.max_hosts = 2
        inv = factories.v2_inventory(organization=org)
        [inv.add_host() for _ in range(2)]
        inv.patch(organization=org2.id)
        inv.add_host()
        utils.logged_sleep(5)
        assert inv.get().total_hosts == 3

    def test_organization_host_limits_no_longer_apply_if_max_hosts_zero(self, factories):
        org = factories.v2_organization()
        org.max_hosts = 2
        inv = factories.v2_inventory(organization=org)
        [inv.add_host() for _ in range(2)]
        org.max_hosts = 0
        inv.add_host()
        utils.logged_sleep(5)
        assert inv.get().total_hosts == 3

    def test_organization_host_limits_rbac_only_superuser_can_change_max_hosts(self, factories):
        org = factories.v2_organization()
        user = factories.user()
        org.set_object_roles(user, 'admin')
        with self.current_user(username=user.username, password=user.password):
            with pytest.raises(towerkit.exceptions.BadRequest) as e:
                org.max_hosts = 5
        assert e.value.msg['__all__'] == ['Cannot change max_hosts.']

    def test_organization_host_limits_dynamic_inventory(self, factories, host_script):
        org = factories.v2_organization()
        inv_script = factories.v2_inventory_script(script=host_script(5))
        inv_source = factories.v2_inventory_source(inventory_script=inv_script)
        inv = inv_source.ds.inventory
        inv.organization = org.id
        org.max_hosts = 4
        job = inv.update_inventory_sources(wait=True)
        assert job.pop().org_host_limit_error is True

    def test_organization_host_limits_cannot_launch_jt_if_limit_exceeded(self, factories):
        org = factories.v2_organization()
        org.max_hosts = 5
        inv = factories.v2_inventory(organization=org)
        [inv.add_host() for _ in range(5)]
        org.max_hosts = 1
        jt = factories.v2_job_template(inventory=inv)
        utils.logged_sleep(5)
        with pytest.raises(towerkit.exceptions.Forbidden) as e:
            jt.launch()
        assert e.value.msg['detail'] == 'Organization host limit of 1 has been exceeded, 5 hosts active.'

    def test_organization_host_limits_apply_to_awxmanage_imports(self, ansible_runner, factories):
        inventory_content = """
        hostA
        hostB
        hostC
        """
        inv_filename = '/tmp/inventory_{}.ini'.format(fauxfactory.gen_alphanumeric())
        ansible_runner.copy(dest=inv_filename,
                            force=True,
                            mode='0644',
                            content=inventory_content)
        org = factories.v2_organization()
        org.max_hosts = 2
        inv = factories.v2_inventory(organization=org)
        contacted = ansible_runner.shell(
            "awx-manage inventory_import --overwrite --inventory-id {0.id} "
            "--source {1}".format(inv, inv_filename)
            )
        for results in contacted.values():
            assert results['rc'] == 1, "awx-manage inventory_import failed: %s" % results
        assert inv.get_related('hosts').count == 0
        assert "Host limit for organization exceeded!" in results['stderr']
