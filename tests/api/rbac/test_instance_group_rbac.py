import pytest
import random

import towerkit.exceptions

from tests.api import Base_Api_Test


@pytest.mark.api
@pytest.mark.rbac
@pytest.mark.requires_ha
@pytest.mark.usefixtures('authtoken', 'install_enterprise_license_unlimited')
class TestInstanceGroupRBAC(Base_Api_Test):

    # Note: superuser's ability to see all instance_groups and instances
    # is implicitly tested by TestInstanceGroups.test_instance_group_creation

    def test_org_admin(self, v2, factories):
        """An org admin should be able to see the instance groups
        associated with their organization, as well as all instances
        listed in those groups.
        """
        user = factories.user()
        org = factories.organization()
        org.add_admin(user)

        instance_groups = random.sample(v2.instance_groups.get().results, 2)
        expected_instances = set()
        for ig in instance_groups:
            org.add_instance_group(ig)
            expected_instances.update(set(ig.get_related('instances').results))

        with self.current_user(username=user.username, password=user.password):
            assert set([ig.id for ig in v2.instance_groups.get().results]) == set([ig.id for ig in instance_groups])
            assert set([i.id for i in v2.instances.get().results]) == set([i.id for i in expected_instances])

    def test_regular_user(self, v2, factories):
        """A regular user should not see any items listed on
        the instance_groups or instances endpoints
        """
        user = factories.user()

        with self.current_user(username=user.username, password=user.password):
            assert v2.instances.get().count == 0
            assert len(v2.instances.get().results) == 0

            assert v2.instance_groups.get().count == 0
            assert len(v2.instance_groups.get().results) == 0


@pytest.mark.api
@pytest.mark.rbac
@pytest.mark.requires_ha
@pytest.mark.usefixtures('authtoken', 'install_enterprise_license_unlimited')
class TestInstanceGroupAssignmentRBAC(Base_Api_Test):

    @pytest.mark.parametrize('resource_type', ['job_template', 'inventory', 'organization'])
    def test_superuser(self, v2, factories, resource_type):
        """A superuser should be able to (un)assign any instance group to a resource."""
        resource = getattr(factories, resource_type)()
        assert resource.get_related('instance_groups').count == 0

        for ig in v2.instance_groups.get().results:
            resource.add_instance_group(ig)
            assert resource.get_related('instance_groups').count == 1
            assert resource.get_related('instance_groups').results.pop().id == ig.id
            resource.remove_instance_group(ig)
            assert resource.get_related('instance_groups').count == 0

    @pytest.mark.parametrize('resource_type', ['job_template', 'inventory'])
    def test_org_admin(self, v2, factories, resource_type):
        """An org admin should only be able to (un)assign instance groups associated
        with their organization.
        """
        user = factories.user()
        resource = getattr(factories, resource_type)()
        resource.set_object_roles(user, 'admin')
        if resource_type == 'job_template':
            org = resource.ds.project.ds.organization
        else:
            org = resource.ds.organization
        org.add_admin(user)

        all_instance_groups = v2.instance_groups.get().results
        org_instance_groups = random.sample(all_instance_groups, 2)
        for ig in org_instance_groups:
            org.add_instance_group(ig)

        with self.current_user(username=user.username, password=user.password):
            for ig in all_instance_groups:
                if ig in org_instance_groups:
                    resource.add_instance_group(ig)
                else:
                    with pytest.raises(towerkit.exceptions.Forbidden):
                        resource.add_instance_group(ig)
        assert resource.get_related('instance_groups').count == len(org_instance_groups)
        assert set([ig.id for ig in resource.get_related('instance_groups').results]) == set([ig.id for ig in org_instance_groups])

        for ig in all_instance_groups:
            if ig in org_instance_groups:
                with self.current_user(username=user.username, password=user.password):
                    resource.remove_instance_group(ig)
            else:
                resource.add_instance_group(ig)
                with self.current_user(username=user.username, password=user.password):
                    with pytest.raises(towerkit.exceptions.Forbidden):
                        resource.remove_instance_group(ig)
        resource_instance_group_ids = set([ig.id for ig in resource.get_related('instance_groups').results])
        org_instance_group_ids = set([ig.id for ig in all_instance_groups if ig.id not in [org_ig.id for org_ig in org_instance_groups]])
        assert resource_instance_group_ids == org_instance_group_ids

    def test_org_admin_managing_organization_instance_groups(self, v2, factories):
        """An org admin should not be able to (un)set instance groups on their own
        organization (or any other).
        """
        user = factories.user()
        org = factories.organization()
        org.add_admin(user)
        other_org = factories.organization()

        # Org admin cannot add instance groups to any org
        all_instance_groups = v2.instance_groups.get().results
        for ig in all_instance_groups:
            with self.current_user(username=user.username, password=user.password):
                with pytest.raises(towerkit.exceptions.Forbidden):
                    org.add_instance_group(ig)
                with pytest.raises(towerkit.exceptions.Forbidden):
                    other_org.add_instance_group(ig)
            assert org.get_related('instance_groups').count == 0
            assert other_org.get_related('instance_groups').count == 0

        org_instance_groups = random.sample(all_instance_groups, 2)
        for ig in org_instance_groups:
            org.add_instance_group(ig)
            other_org.add_instance_group(ig)

        assert org.get_related('instance_groups').count == len(org_instance_groups)
        assert other_org.get_related('instance_groups').count == len(org_instance_groups)
        assert set([ig.id for ig in org.get_related('instance_groups').results]) == set([ig.id for ig in org_instance_groups])
        assert set([ig.id for ig in other_org.get_related('instance_groups').results]) == set([ig.id for ig in org_instance_groups])

        # Org admin cannot remove instance groups from any org
        for ig in org_instance_groups:
            with self.current_user(username=user.username, password=user.password):
                with pytest.raises(towerkit.exceptions.Forbidden):
                    org.remove_instance_group(ig)
                with pytest.raises(towerkit.exceptions.Forbidden):
                    other_org.remove_instance_group(ig)
            assert org.get_related('instance_groups').count == len(org_instance_groups)
            assert other_org.get_related('instance_groups').count == len(org_instance_groups)

    @pytest.mark.parametrize('resource_type', ['job_template', 'inventory', 'organization'])
    def test_regular_user(self, v2, factories, resource_type):
        """A regular user should not be able to (un)assign instance_groups to any resources"""
        user = factories.user()
        jt = factories.job_template()
        jt.set_object_roles(user, 'admin')

        instance_groups = v2.instance_groups.get().results
        with self.current_user(username=user.username, password=user.password):
            for ig in instance_groups:
                with pytest.raises(towerkit.exceptions.Forbidden):
                    jt.add_instance_group(ig)
        assert jt.get_related('instance_groups').count == 0

        for ig in instance_groups:
            jt.add_instance_group(ig)
        with self.current_user(username=user.username, password=user.password):
            for ig in instance_groups:
                with pytest.raises(towerkit.exceptions.Forbidden):
                    jt.remove_instance_group(ig)
        assert jt.get_related('instance_groups').count == len(instance_groups)
