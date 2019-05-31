import pytest

import towerkit.exceptions
from tests.api import APITest


@pytest.mark.usefixtures('authtoken', 'install_enterprise_license_unlimited')
class Test_Label_RBAC(APITest):

    def test_label_post_with_unprivileged_user(self, factories):
        """Unprivileged users cannot create labels."""
        user = factories.user()
        organization = factories.organization()

        with self.current_user(username=user.username, password=user.password):
            with pytest.raises(towerkit.exceptions.Forbidden):
                factories.label(organization=organization)

    @pytest.mark.parametrize('role', ['admin', 'auditor', 'read', 'member'])
    def test_label_post_with_privileged_user(self, factories, api_labels_pg, role):
        """Users with organization 'admin' and 'member' should be able to create a label with their
        organization. Users with organization 'auditor' and 'read' should receive a 403 forbidden.
        """
        ALLOWED_ROLES = ['admin', 'member']
        REJECTED_ROLES = ['read', 'auditor']

        user = factories.user()
        organization = factories.organization()

        organization.set_object_roles(user, role)

        # test label creation
        with self.current_user(username=user.username, password=user.password):
            if role in ALLOWED_ROLES:
                factories.label(organization=organization)
            elif role in REJECTED_ROLES:
                with pytest.raises(towerkit.exceptions.Forbidden):
                    factories.label(organization=organization)
            else:
                raise ValueError("Received unhandled organization role.")

    @pytest.mark.parametrize("role", ["admin", "execute", "read"])
    def test_job_template_label_association(self, factories, role):
        """Users with JT-admin should be able to associate labels with their
        JT. Users with JT-execute and JT-read should receive a 403 forbidden.
        """
        ALLOWED_ROLES = ['admin']
        REJECTED_ROLES = ['execute', 'read']

        job_template = factories.job_template()
        organization = job_template.ds.project.ds.organization
        user = factories.user(organization=organization)
        label = factories.label(organization=organization)

        job_template.set_object_roles(user, role)

        # test label association
        with self.current_user(username=user.username, password=user.password):
            if role in ALLOWED_ROLES:
                job_template.add_label(label)
            elif role in REJECTED_ROLES:
                with pytest.raises(towerkit.exceptions.Forbidden):
                    job_template.add_label(label)
            else:
                raise ValueError("Received unhandled JT role.")
