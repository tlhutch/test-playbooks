import pytest

import towerkit.exceptions
from tests.lib.helpers.rbac_utils import set_roles
from tests.api import Base_Api_Test


@pytest.mark.api
@pytest.mark.rbac
@pytest.mark.skip_selenium
class Test_Label_RBAC(Base_Api_Test):

    pytestmark = pytest.mark.usefixtures('authtoken', 'install_enterprise_license_unlimited')

    @pytest.mark.parametrize('role', ['admin', 'auditor', 'read', 'member'])
    def test_organization_label_post(self, factories, user_password, api_labels_pg, role):
        """Users with organization 'admin' and 'member' should be able to create a label with their role
        organization. Users with organization 'auditor' and 'read' should receive a 403 forbidden.
        """
        ALLOWED_ROLES = ['admin', 'member']
        REJECTED_ROLES = ['read', 'auditor']

        user_pg = factories.user()
        organization_pg = factories.organization()
        payload = factories.label.payload(organization=organization_pg)[0]

        # assert initial label post raises 403
        with self.current_user(username=user_pg.username, password=user_password):
            with pytest.raises(towerkit.exceptions.Forbidden):
                api_labels_pg.post(payload)

        # grant user target organization permission
        set_roles(user_pg, organization_pg, [role])

        # assert label post accepted
        with self.current_user(username=user_pg.username, password=user_password):
            if role in ALLOWED_ROLES:
                api_labels_pg.post(payload)
            elif role in REJECTED_ROLES:
                with pytest.raises(towerkit.exceptions.Forbidden):
                    api_labels_pg.post(payload)
            else:
                raise ValueError("Received unhandled organization role.")

    @pytest.mark.parametrize("role", ["admin", "read"])
    def test_job_template_label_association(self, factories, user_password, role):
        """Tests that when JT can_edit is true that our test user may associate a label with
        a JT. Note: our test iterates through "admin_role" and "read_role" since these two
        roles should unlock can_edit as true and false respectively.
        """
        job_template_pg = factories.job_template()
        labels_pg = job_template_pg.get_related('labels')
        organization_pg = job_template_pg.get_related('inventory').get_related('organization')
        user_pg = factories.user(organization=organization_pg)
        label_pg = factories.label(organization=organization_pg)

        # grant user target JT permission
        set_roles(user_pg, job_template_pg, [role])

        # test label association
        payload = dict(id=label_pg.id)
        with self.current_user(username=user_pg.username, password=user_password):
            job_template_pg.get()
            if job_template_pg.summary_fields.user_capabilities.edit:
                with pytest.raises(towerkit.exceptions.NoContent):
                    labels_pg.post(payload)
            else:
                with pytest.raises(towerkit.exceptions.Forbidden):
                    labels_pg.post(payload)
