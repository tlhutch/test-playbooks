import pytest


class TestReadOnlyButtonVisbility(object):

    @pytest.fixture(scope='class')
    def ro(self, v1, session_fixtures):
        user = v1.users.create(organization=session_fixtures.organization)
        session_fixtures.credential.set_object_roles(user, 'read')
        session_fixtures.inventory.set_object_roles(user, 'read')
        session_fixtures.project.set_object_roles(user, 'read')
        session_fixtures.job_template.set_object_roles(user, 'read')
        session_fixtures.team.set_object_roles(user, 'read')
        yield user
        user.silent_cleanup()

    def test_org_save_invisible(self, ui, ro, session_fixtures):
        edit = ui.organization_edit.get(id=session_fixtures.organization.id)
        assert edit.details.is_save_displayed()
        with edit.current_user(ro.username):
            assert not edit.details.is_save_displayed()

    def test_credential_save_invisible(self, ui, ro, session_fixtures):
        edit = ui.credential_edit.get(id=session_fixtures.credential.id)
        assert edit.details.is_save_displayed()
        with edit.current_user(ro.username):
            assert not edit.details.is_save_displayed()

    def test_inventory_save_invisible(self, ui, ro, session_fixtures):
        edit = ui.inventory_edit.get(id=session_fixtures.inventory.id)
        assert edit.details.is_save_displayed()
        with edit.current_user(ro.username):
            assert not edit.details.is_save_displayed()

    def test_project_save_invisible(self, ui, ro, session_fixtures):
        edit = ui.project_edit.get(id=session_fixtures.project.id)
        assert edit.details.is_save_displayed()
        with edit.current_user(ro.username):
            assert not edit.details.is_save_displayed()

    def test_template_save_invisible(self, ui, ro, session_fixtures):
        edit = ui.job_template_edit.get(id=session_fixtures.job_template.id)
        assert edit.details.is_save_displayed()
        with edit.current_user(ro.username):
            assert not edit.details.is_save_displayed()

    def test_team_save_invisible(self, ui, ro, session_fixtures):
        edit = ui.team_edit.get(id=session_fixtures.team.id)
        assert edit.details.is_save_displayed()
        with edit.current_user(ro.username):
            assert not edit.details.is_save_displayed()

    def test_credential_edit_action_visibility(self, ui, ro, session_fixtures):
        creds = ui.credentials.get()

        with creds.current_user(ro.username):
            creds.search(session_fixtures.credential.name)
            row = creds.table.query(
                lambda r: r.name.text == session_fixtures.credential.name).pop()

            assert not row.edit.is_displayed()
            assert row.view.is_displayed()

    def test_inventory_edit_action_visibility(self, ui, ro, session_fixtures):
        invs = ui.inventories.get()

        with invs.current_user(ro.username):
            invs.search(session_fixtures.inventory.name)
            row = invs.table.query(
                lambda r: r.name.text == session_fixtures.inventory.name).pop()

            assert not row.edit.is_displayed()
            assert row.view.is_displayed()

    def test_project_edit_action_visibility(self, ui, ro, session_fixtures):
        projs = ui.projects.get()

        with projs.current_user(ro.username):
            projs.search(session_fixtures.project.name)
            row = projs.table.query(
                lambda r: r.name.text == session_fixtures.project.name).pop()

            assert not row.edit.is_displayed()
            assert row.view.is_displayed()

    def test_template_edit_action_visibility(self, ui, ro, session_fixtures):
        templates = ui.job_templates.get()

        with templates.current_user(ro.username):
            templates.search(session_fixtures.job_template.name)
            row = templates.table.query(
                lambda r: r.name.text == session_fixtures.job_template.name).pop()

            assert not row.edit.is_displayed()
            assert row.view.is_displayed()

    def test_team_edit_action_visibility(self, ui, ro, session_fixtures):
        teams = ui.teams.get()

        with teams.current_user(ro.username):
            teams.search(session_fixtures.team.name)
            row = teams.table.query(
                lambda r: r.name.text == session_fixtures.team.name).pop()

            assert not row.edit.is_displayed()
            assert row.view.is_displayed()
