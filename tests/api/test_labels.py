import json

import towerkit.exceptions as exc
import fauxfactory
import pytest

from tests.api import APITest


@pytest.mark.api
@pytest.mark.destructive
@pytest.mark.usefixtures('authtoken', 'install_enterprise_license_unlimited')
class Test_Labels(APITest):

    def test_duplicate_labels_disallowed_by_organization(self, factories):
        label = factories.v2_label()
        with pytest.raises(exc.Duplicate) as e:
            factories.v2_label(name=label.name, organization=label.ds.organization)
        assert e.value[1]['__all__'] == ['Label with this Name and Organization already exists.']

    def test_duplicate_across_different_organizations(self, label, another_organization, api_labels_pg):
        """Verify that labels with the same name may be created across different organizations."""
        payload = dict(name=label.name, organization=another_organization.id)
        api_labels_pg.post(payload)

    def test_job_association(self, job_template_with_labels):
        """Verify that resulting jobs list JT labels."""
        # launch JT
        job_pg = job_template_with_labels.launch().wait_until_completed()
        job_pg.assert_successful()

        # verify that the job has the same labels as the job template
        job_template_labels = job_template_with_labels.get_related('labels')
        job_pg_labels = job_pg.get_related('labels')
        assert job_template_labels.json == job_pg_labels.json, \
            "JT labels json is as follows:\n%s\n\nJob labels json is as follows:\n%s\n" \
            % (json.dumps(job_template_labels.json, indent=2), json.dumps(job_pg_labels.json, indent=2))

    def test_job_label_persistence(self, job_template_with_label):
        """Verify that job_pg labels persist beyond JT deletion."""
        job_pg = job_template_with_label.launch().wait_until_completed()

        # find JT labels
        job_template_summary_field_labels = job_template_with_label.summary_fields['labels']
        job_template_labels = job_template_with_label.get_related('labels')

        # delete JT and assess that job_pg labels persist
        job_template_with_label.delete()
        job_pg_summary_field_labels = job_pg.get().summary_fields['labels']
        job_pg_labels = job_pg.get_related('labels')

        assert job_template_summary_field_labels == job_pg_summary_field_labels, \
            "JT and job_pg summary_field labels do not match."
        assert job_template_labels.json == job_pg_labels.json, \
            "JT labels json is as follows:\n%s\n\nJob labels json is as follows:\n%s\n" \
            % (json.dumps(job_template_labels.json, indent=2), json.dumps(job_pg_labels.json, indent=2))

    def test_job_template_association(self, job_template, label):
        """Verify that you can associate a label with a JT."""
        # Check that we don't have any labels to start
        labels_pg = job_template.get_related('labels')
        assert labels_pg.count == 0, \
            "Unexpected number of labels returned: (%s != 0)." % labels_pg.count

        # Associate a label with the JT and assess results
        payload = dict(associate=True, id=label.id)
        with pytest.raises(exc.NoContent):
            labels_pg.post(payload)

        assert labels_pg.get().count == 1, \
            "Unexpected number of labels returned: (%s != 1)." % labels_pg.count

    def test_job_template_disassociation(self, job_template_with_label):
        """Verify that you can disassociate a label from a JT."""
        # Check that we have one label to start
        labels_pg = job_template_with_label.get_related('labels')
        assert labels_pg.count == 1, \
            "Unexpected number of labels returned: (%s != 1)." % labels_pg.count

        # Disassociate a label with the JT and assess results
        label_pg = labels_pg.results[0]
        payload = dict(disassociate=True, id=label_pg.id)
        with pytest.raises(exc.NoContent):
            labels_pg.post(payload)

        assert labels_pg.get().count == 0, \
            "Unexpected number of labels returned: (%s != 0)." % labels_pg.count

    def test_organization_reference_delete(self, label):
        """Tests that labels get reference deleted with their organization."""
        # find and delete label organization
        organization_pg = label.get_related('organization')
        organization_pg.delete()

        # check that label gets deleted
        with pytest.raises(exc.NotFound):
            label.get()

    def test_reference_delete_with_job_template_deletion(self, job_template, another_job_template, label):
        """Tests that a label attached to JTs get reference deleted when their last associated JT gets deleted
        in the absence of jobs that use this label.
        """
        # associate label with both JTs
        labels_pg = job_template.get_related('labels')
        another_labels_pg = another_job_template.get_related('labels')

        payload = dict(associate=True, id=label.id)
        with pytest.raises(exc.NoContent):
            labels_pg.post(payload)
        with pytest.raises(exc.NoContent):
            another_labels_pg.post(payload)

        # check that labels associated
        assert labels_pg.get().count == 1, "Unexpected number of labels found."
        assert another_labels_pg.get().count == 1, "Unexpected number of labels found."

        # label should not get reference deleted with first JT deletion
        job_template.delete()
        label.get()

        # label should get reference deleted with final JT deletion
        another_job_template.delete()
        with pytest.raises(exc.NotFound):
            label.get()

    @pytest.mark.yolo
    def test_reference_delete_with_job_template_disassociation(self, job_template, another_job_template, label):
        """Tests that a label attached to JTs get reference deleted after getting disassociated with its last JT
        in the absence of jobs that use this label.
        """
        # associate label with both JTs
        labels_pg = job_template.get_related('labels')
        another_labels_pg = another_job_template.get_related('labels')

        payload = dict(associate=True, id=label.id)
        with pytest.raises(exc.NoContent):
            labels_pg.post(payload)
        with pytest.raises(exc.NoContent):
            another_labels_pg.post(payload)

        # check that labels associated
        assert labels_pg.get().count == 1, "Unexpected number of labels found."
        assert another_labels_pg.get().count == 1, "Unexpected number of labels found."

        # label should not get reference deleted with first JT disassociation
        with pytest.raises(exc.NoContent):
            labels_pg.post(dict(id=label.id, disassociate=True))
        label.get()

        # label should get reference deleted with final JT disassociation
        with pytest.raises(exc.NoContent):
            another_labels_pg.post(dict(id=label.id, disassociate=True))
        with pytest.raises(exc.NotFound):
            label.get()

    def test_job_reference_delete(self, job_template_with_label, api_labels_pg):
        """Labels should get reference deleted when their last remaining job gets deleted"""
        # launch JT and assert successful
        job_pg = job_template_with_label.launch().wait_until_completed()
        job_pg.assert_successful()

        # launch JT again and assert successful
        second_job_pg = job_template_with_label.launch().wait_until_completed()
        second_job_pg.assert_successful()

        # find our label in api/v1/labels
        label_id = job_template_with_label.get_related('labels').results[0].id
        labels_pg = api_labels_pg.get(id=label_id)
        assert labels_pg.count == 1, "No label with id %s found." % label_id
        label_pg = labels_pg.results[0]

        # label should persist after JT deletion
        job_template_with_label.delete()
        assert api_labels_pg.get(id=label_pg.id).count == 1

        # label should persist after job_pg deletion
        job_pg.delete()
        assert api_labels_pg.get(id=label_pg.id).count == 1

        # label should get reference deleted after second_job_pg deletion
        second_job_pg.delete()
        assert api_labels_pg.get(id=label_pg.id).count == 0

    def test_summary_field_label_max(self, job_template):
        """JTs and jobs may have an infinite number of labels. The summary_fields of
        JTs and jobs, however, are limited to ten labels each.
        """
        job_template_labels_pg = job_template.get_related('labels')
        organization_id = job_template.get_related('inventory').organization

        # create eleven JT labels
        for i in range(11):
            payload = dict(name="label %s - %s" % (i, fauxfactory.gen_utf8()), organization=organization_id)
            job_template_labels_pg.post(payload)
        assert job_template_labels_pg.get().count == 11, "Unexpected number of labels returned. Expected eleven but got %s." % job_template_labels_pg.count

        # although JT has eleven labels, only ten should show in JT summary_fields
        job_template_summary_field_labels = job_template.get().summary_fields['labels']['results']
        assert len(job_template_summary_field_labels) == 10, \
            "Unexpected number of summary_field labels returned. Expected ten but got %s." % len(job_template_summary_field_labels)

        # launch JT and assert successful
        job_pg = job_template.launch().wait_until_completed()
        job_pg.assert_successful()

        # resulting jobs should also have ten summary_field labels. The job summary_field labels should be the JT summary_field labels
        job_summary_field_labels = job_pg.summary_fields['labels']['results']
        assert len(job_summary_field_labels) == 10, \
            "Unexpected number of job_summary_field_labels returned. Expected ten but got %s. Labels are: %s." \
            % (len(job_summary_field_labels), job_summary_field_labels)
        assert job_template_summary_field_labels == job_summary_field_labels, \
            "JT and its resulting job have different values for summary_field labels."

        # job should contain all JT labels
        job_labels_pg = job_pg.get_related('labels')
        assert job_labels_pg.count == 11, "Unexpected number of job labels returned. Expected eleven but got %s." % job_labels_pg.count

    def test_summary_field_label_order(self, job_template_with_labels):
        """JT summary_field labels should be presented in alphabetical order."""
        summary_field_labels = job_template_with_labels.summary_fields['labels']['results']
        sorted_summary_field_labels = sorted(summary_field_labels, key=lambda k: k['name'].lower())
        assert summary_field_labels == sorted_summary_field_labels, \
            "JT summary fields not sorted by name. API gave %s but we expected %s." % (summary_field_labels, sorted_summary_field_labels)

    def test_filter_by_label_name(self, job_template_with_label, api_job_templates_pg, api_jobs_pg):
        """Test that JTs and jobs may be filtered by label."""
        # launch JT and assert success
        job_pg = job_template_with_label.launch().wait_until_completed()
        job_pg.assert_successful()

        # find label name
        labels_pg = job_template_with_label.get_related('labels')
        assert labels_pg.count == 1, "Unexpected number of labels returned (%s != 1)." % labels_pg.count
        label_name = labels_pg.results[0].name

        # find our JT and job by searching by label name
        job_templates_pg = api_job_templates_pg.get(labels__name=label_name)
        assert job_templates_pg.count == 1, "No JT matches for label %s." % label_name
        jobs_pg = api_jobs_pg.get(labels__name=label_name)
        assert jobs_pg.count == 1, "No job matches for label %s." % label_name

    def test_unable_to_assign_label_to_different_org(self, org_admin, user_password, label, another_organization):
        """Tests that org_admins may not reassign a label to an organization for which they
        are not a member.
        """
        with self.current_user(org_admin.username, user_password):
            with pytest.raises(exc.Forbidden):
                label.patch(organization=another_organization.id)

    def test_able_to_assign_label_to_different_org(self, org_admin, user_password, label, another_organization):
        """Tests that org_admins may reassign a label to an organization for which they
        are a member.
        """
        # make org_admin a member of another_organization
        org_users_pg = another_organization.get_related('users')
        with pytest.raises(exc.NoContent):
            org_users_pg.post(dict(id=org_admin.id))

        # assert that org_admin can reassign label
        with self.current_user(org_admin.username, user_password):
            label.patch(organization=another_organization.id)

    def test_unable_to_assign_label_to_different_org_as_unprivileged_user(self, unprivileged_users, user_password, label, another_organization):
        """Tests that unprivileged users may not reassign labels across organizations."""
        for unprivileged_user in unprivileged_users:
            # make unprivileged user a member of another_organization
            users_pg = another_organization.get_related('users')
            with pytest.raises(exc.NoContent):
                users_pg.post(dict(id=unprivileged_user.id))

            # assert that unprivileged user cannot reassign label
            with self.current_user(unprivileged_user.username, user_password):
                with pytest.raises(exc.Forbidden):
                    label.patch(organization=another_organization.id)
