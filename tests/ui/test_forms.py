import pytest


pytestmark = [pytest.mark.ui]


class RequiredFields(object):

    def test_clearing_required_fields_disables_save(self, form):
        """Verify save enabled / disabled behavior for required input fields
        """
        msg_fail_enabled = 'save enabled after clearing required field: '
        msg_fail_disabled = 'save disabled after populating required field: '

        [f.randomize() for _, f in form.load_groups(required=True) if not f.value]

        form.save.is_enabled(), msg_fail_disabled + '[all]'

        for name, field in form.load_groups(required=True):
            if field.options: continue  # NOQA
            initial_value = field.value
            field.clear()
            assert form.save_eventually_disabled(), msg_fail_enabled + name
            field.value = initial_value
            assert form.save_eventually_enabled(), msg_fail_disabled + name


class TextInputReset(object):

    def test_text_input_fields_not_updated_unless_saved(self, form):
        initial_field_values = {}
        # msg_fail = 'value for field {0} unexpectedly persisted without saving'

        for name, field in form.load_groups(kind='text_input'):
            initial_field_values[name] = field.value
            field.randomize()

        with form.page.handle_dialog(lambda d: d.cancel.click()):
            form.scroll_save_into_view()
            form.cancel.click()


class TextInputPanelResponse(object):

    def test_lengthy_text_input(self, form):
        msg_fail = 'field {0} not fully surrounded by form panel'
        for name, field in form.load_groups(kind='text_input'):
            field.randomize()
            field.value = 'a'*200 + field.value
            assert form.surrounds(field), msg_fail.format(name)


# -----------------------------------------------------------------------------
# Tests
# -----------------------------------------------------------------------------

class TestConfiguration(TextInputReset, TextInputPanelResponse):

    form_names = (
        'auth.github',
        'auth.github_org',
        'auth.github_team',
        'auth.google',
        'auth.ldap',
        'auth.radius',
        'auth.saml',
        'jobs',
        'system',
        'ui',)

    @pytest.fixture(params=form_names)
    def form(self, request, ui):
        yield reduce(getattr, request.param.split('.'), ui.configuration.get())


class TestCredDetails(RequiredFields, TextInputPanelResponse):

    form_names = (
        'details.machine',
        'details.openstack',
        'details.aws',
        'details.gce',
        'details.azure_classic',
        'details.azure_resource_manager',
        'details.rackspace',
        'details.vmware_vcenter',
        'details.source_control',
        'details.satellite_v6',
        'details.cloudforms',
        'details.network',)

    @pytest.fixture(params=form_names)
    def form(self, request, ui, session_fixtures):
        obj = ui.credential_edit.get(id=session_fixtures.credential.id)
        yield reduce(getattr, request.param.split('.'), obj)


class TestInventoryDetails(RequiredFields, TextInputPanelResponse):

    @pytest.fixture
    def form(self, request, ui, session_fixtures):
        yield ui.inventory_edit.get(id=session_fixtures.inventory.id).details


class TestOrgDetails(RequiredFields, TextInputPanelResponse):

    @pytest.fixture
    def form(self, request, ui, session_fixtures):
        yield ui.organization_edit.get(id=session_fixtures.organization.id).details


class TestProjectDetails(RequiredFields, TextInputPanelResponse):

    @pytest.fixture
    def form(self, request, ui, session_fixtures):
        edit = ui.project_edit.get(id=session_fixtures.project.id)
        edit.wait.until(lambda _: 'Git' in edit.details.scm_type.options)
        yield edit.details


class TestTeamDetails(RequiredFields, TextInputPanelResponse):

    @pytest.fixture
    def form(self, request, ui, session_fixtures):
        yield ui.team_edit.get(id=session_fixtures.team.id).details


class TestUserDetails(RequiredFields, TextInputPanelResponse):

    @pytest.fixture
    def form(self, request, ui, session_fixtures):
        yield ui.user_edit.get(id=session_fixtures.user.id).details


class TestJobTemplateDetails(RequiredFields, TextInputPanelResponse):

    @pytest.fixture
    def form(self, request, ui, session_fixtures):
        yield ui.job_template_edit.get(id=session_fixtures.job_template.id).details

    @pytest.mark.xfail(reason='placeholder')
    def test_clearing_required_fields_disables_save(self, form):
        super(TestJobTemplateDetails, self).test_clearing_required_fields_disables_save(form)
