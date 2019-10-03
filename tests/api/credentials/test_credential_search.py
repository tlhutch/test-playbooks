import pytest

from tests.api import APITest


@pytest.mark.usefixtures('authtoken')
class TestCredentialSearch(APITest):

    related_search_fields = set([
        'ad_hoc_commands__search',
        'created_by__search',
        'credential_type__search',
        'input_sources__search',
        'insights_inventories__search',
        'joblaunchconfigs__search',
        'jobs__search',
        'jobtemplates__search',
        'modified_by__search',
        'organization__search',
        'projects__search',
        'projectupdates__search',
        'schedules__search',
        'target_input_sources__search',
        'unifiedjobs__search',
        'unifiedjobtemplates__search',
        'workflowjobnodes__search',
        'workflowjobs__search',
        'workflowjobtemplatenodes__search',
        'workflowjobtemplates__search'])

    def test_desired_related_search_fields(self, v2):
        assert set(v2.credentials.options().related_search_fields) == self.related_search_fields

    def confirm_sole_credential_in_related_search(self, v2, credential, **kwargs):
        search_results = v2.credentials.get(**kwargs)
        assert credential.name in [item.name for item in search_results.results]
        assert search_results.count == 1

    def test_search_by_sourcing_ad_hoc_command(self, v2, factories):
        cred = factories.credential()
        host = factories.host()
        ahc = factories.ad_hoc_command(inventory=host.ds.inventory, credential=cred).wait_until_completed()
        self.confirm_sole_credential_in_related_search(v2, cred, ad_hoc_commands__search=ahc.name)

    def test_search_by_organization(self, v2, factories):
        org = factories.organization()
        cred = factories.credential(organization=org)
        self.confirm_sole_credential_in_related_search(v2, cred, organization__search=cred.ds.organization.name)

    def test_search_by_creator(self, v2, factories):
        org = factories.organization()
        user = factories.user()
        org.add_admin(user)

        with self.current_user(user):
            cred = factories.credential(kind='ssh', organization=org)

        self.confirm_sole_credential_in_related_search(v2, cred, created_by__search=user.username)

    @pytest.mark.yolo
    def test_search_by_modifier(self, v2, factories):
        org = factories.organization()
        user = factories.user()
        org.add_admin(user)

        cred = factories.credential(kind='ssh', organization=org)
        with self.current_user(user):
            cred.name = 'SomeUpdatedName'

        self.confirm_sole_credential_in_related_search(v2, cred, modified_by__search=user.username)

    def test_search_by_credential_type(self, v2, factories):
        cred_type = factories.credential_type(kind='cloud')
        cred = factories.credential(credential_type=cred_type)

        self.confirm_sole_credential_in_related_search(v2, cred, credential_type__search=cred_type.name)

    def test_search_by_sourcing_insights_inventory(self, v2, factories):
        cred = factories.credential(kind='insights')
        inventory = factories.inventory()
        inventory.insights_credential = cred.id

        self.confirm_sole_credential_in_related_search(v2, cred, insights_inventories__search=inventory.name)

    def test_search_by_sourcing_inventory_and_inventory_update(self, v2, factories):
        cred = factories.credential(kind='aws')
        inv_source = factories.inventory_source(source='ec2', credential=cred)

        self.confirm_sole_credential_in_related_search(v2, cred, unifiedjobtemplates__search=inv_source.name)

        inv_source.update().wait_until_completed()

        self.confirm_sole_credential_in_related_search(v2, cred, unifiedjobs__search=inv_source.name)

    def test_search_by_sourcing_job_template_and_job(self, v2, factories):
        cred = factories.credential()
        jt = factories.job_template(credential=cred)

        self.confirm_sole_credential_in_related_search(v2, cred, unifiedjobtemplates__search=jt.name)

        jt.launch().wait_until_completed()

        self.confirm_sole_credential_in_related_search(v2, cred, unifiedjobs__search=jt.name)

    def test_search_by_sourcing_project_and_project_update(self, v2, factories):
        cred = factories.credential(kind='scm')
        project = factories.project(credential=cred)

        self.confirm_sole_credential_in_related_search(v2, cred, projects__search=project.name)

        project.update().wait_until_completed()

        self.confirm_sole_credential_in_related_search(v2, cred, projectupdates__search=project.name)

    @pytest.mark.yolo
    def test_search_by_sourcing_workflow_job_template_node_and_workflow_job_node(self, v2, factories):
        cred = factories.credential()
        jt = factories.job_template(ask_credential_on_launch=True)
        wfjt = factories.workflow_job_template()
        wfjtn = factories.workflow_job_template_node(workflow_job_template=wfjt,
                                                        unified_job_template=jt)

        wfjtn.add_credential(cred)
        self.confirm_sole_credential_in_related_search(
            v2, cred, workflowjobtemplatenodes__workflow_job_template__search=wfjt.name
        )

        wfjtn.ds.workflow_job_template.launch().wait_until_completed()

        self.confirm_sole_credential_in_related_search(v2, cred, workflowjobnodes__unified_job_template__search=jt.name)
