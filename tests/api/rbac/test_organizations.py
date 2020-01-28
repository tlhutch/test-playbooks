import pytest
import awxkit.exceptions
from awxkit import utils
from tests.api import APITest
import fauxfactory


@pytest.fixture(scope="function", params=['job_template_plain',
                                          'check_job_template_plain',
                                          'org_user',
                                          'team',
                                          'org_admin',
                                          'inventory',
                                          'project'])
def related_organization_object(request):
    """Create organization_related_counts objects sequentially."""
    return request.getfixturevalue(request.param)


@pytest.mark.usefixtures('authtoken')
class Test_Organizations(APITest):
    """Verify the /users endpoint displays the expected information based on the current user"""

    def test_duplicate_organizations_disallowed(self, factories):
        org = factories.organization()
        with pytest.raises(awxkit.exceptions.Duplicate) as e:
            factories.organization(name=org.name)
        assert e.value[1]['name'] == ['Organization with this Name already exists.']

    def test_delete(self, api_organizations_pg, organization):
        """Verify that deleting an organization actually works."""
        # Delete the organization
        organization.delete()

        # assert the organization was deleted
        matches = api_organizations_pg.get(id=organization.id)
        assert matches.count == 0, "An organization was deleted, but is still visible from the /api/v2/organizations/ endpoint"

    @pytest.mark.yolo
    def test_organization_related_counts(self, organization, related_organization_object, api_job_templates_pg):
        """Verify summary_fields 'related_field_counts' content."""
        # determine the expected JTs count
        project_pg = organization.get_related('projects')
        org_project_ids = [proj_pg.id for proj_pg in project_pg.results]

        params = dict(project__in=-1)
        if org_project_ids:
            params['project__in'] = ','.join(str(entry) for entry in org_project_ids)
        job_templates_count = api_job_templates_pg.get(**params).count

        # check related_field_counts
        # note: there is no 'job_templates' get_related field so we handle job_templates differently
        related_field_counts = organization.get().summary_fields['related_field_counts']
        for key in related_field_counts.keys():
            if key != 'job_templates':
                assert related_field_counts[key] == organization.get_related(key).count, \
                    "Incorrect value for %s. Expected %s, got %s." % (key, organization.get_related(key).count, related_field_counts[key])

        assert job_templates_count == related_field_counts['job_templates'], \
            "Incorrect value for job_templates. Expected %s, got %s." % (job_templates_count, related_field_counts['job_templates'])

    def test_organization_host_limits_do_not_allow_adding_too_many_hosts(self, factories):
        org = factories.organization()
        org.max_hosts = 2
        inv = factories.inventory(organization=org)
        [inv.add_host() for _ in range(2)]
        with pytest.raises(awxkit.exceptions.Forbidden) as e:
            inv.add_host()
        assert e.value.msg['detail'] == 'You have already reached the maximum number of 2 hosts allowed for your organization. Contact your System Administrator for assistance.'

    def test_organization_host_limits_apply_across_all_inventories(self, factories):
        org = factories.organization()
        org.max_hosts = 2
        inv = factories.inventory(organization=org)
        [inv.add_host() for _ in range(2)]
        inv2 = factories.inventory(organization=org)
        with pytest.raises(awxkit.exceptions.Forbidden) as e:
            inv2.add_host()
        assert e.value.msg['detail'] == 'You have already reached the maximum number of 2 hosts allowed for your organization. Contact your System Administrator for assistance.'

    @pytest.mark.yolo
    def test_organization_host_limits_allow_same_host_multiple_inventories(self, factories):
        org = factories.organization()
        org.max_hosts = 2
        inv = factories.inventory(organization=org)
        hosts = [inv.add_host() for _ in range(2)]
        inv2 = factories.inventory(organization=org)
        factories.host(name=hosts[1].name, inventory=inv2)
        utils.logged_sleep(5)
        assert inv.get_related('hosts').count == 2
        assert inv2.get_related('hosts').count == 1
        host_set = set()
        for i in org.get().related.inventories.get().results:
            for h in i.related.hosts.get().results:
                host_set.add(h.name)
        assert len(host_set) == 2

    def test_organization_host_limits_no_longer_apply_to_inventory_if_org_changed(self, factories):
        org = factories.organization()
        org2 = factories.organization()
        org.max_hosts = 2
        inv = factories.inventory(organization=org)
        [inv.add_host() for _ in range(2)]
        inv.patch(organization=org2.id)
        inv.add_host()
        utils.logged_sleep(5)
        assert inv.get().total_hosts == 3

    def test_organization_host_limits_no_longer_apply_if_max_hosts_zero(self, factories):
        org = factories.organization()
        org.max_hosts = 2
        inv = factories.inventory(organization=org)
        [inv.add_host() for _ in range(2)]
        org.max_hosts = 0
        inv.add_host()
        utils.logged_sleep(5)
        assert inv.get().total_hosts == 3

    def test_organization_host_limits_rbac_only_superuser_can_change_max_hosts(self, factories):
        org = factories.organization()
        user = factories.user()
        org.set_object_roles(user, 'admin')
        with self.current_user(username=user.username, password=user.password):
            with pytest.raises(awxkit.exceptions.BadRequest) as e:
                org.max_hosts = 5
        assert e.value.msg['__all__'] == ['Cannot change max_hosts.']

    def test_organization_host_limits_dynamic_inventory(self, factories, host_script):
        org = factories.organization()
        org.max_hosts = 4
        inv = factories.inventory(organization=org)
        inv_script = factories.inventory_script(organization=org, script=host_script(5))
        inv_source = factories.inventory_source(inventory=inv, source_script=inv_script)
        assert inv_source.source_script == inv_script.id
        assert inv.organization == org.id
        job = inv.update_inventory_sources(wait=True).pop()
        assert job.org_host_limit_error is True, job

    def test_organization_host_limits_cannot_launch_jt_if_limit_exceeded(self, factories):
        org = factories.organization()
        org.max_hosts = 5
        inv = factories.inventory(organization=org)
        [inv.add_host() for _ in range(5)]
        org.max_hosts = 1
        jt = factories.job_template(inventory=inv)
        utils.logged_sleep(5)
        with pytest.raises(awxkit.exceptions.Forbidden) as e:
            jt.launch()
        assert e.value.msg['detail'] == 'You have already reached the maximum number of 1 hosts allowed for your organization. Contact your System Administrator for assistance.'

    def test_organization_host_limits_apply_to_awxmanage_imports(self, skip_if_openshift, ansible_runner, factories):
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
        org = factories.organization()
        org.max_hosts = 2
        inv = factories.inventory(organization=org)
        contacted = ansible_runner.shell(
            "awx-manage inventory_import --overwrite --inventory-id {0.id} "
            "--source {1}".format(inv, inv_filename)
            )
        for results in contacted.values():
            assert results['rc'] == 1, "awx-manage inventory_import failed: %s" % results
        assert inv.get_related('hosts').count == 0
        assert "Host limit for organization exceeded!" in results['stderr']
