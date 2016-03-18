import random

import fauxfactory
import pytest

pytestmark = [
    pytest.mark.ui,
    pytest.mark.nondestructive,
    pytest.mark.usefixtures(
        'authtoken',
        'install_basic_license',
        'maximized_window_size'
    )
]


@pytest.fixture(params=('ui_job_templates_add', 'ui_job_templates_edit'))
def ui_job_templates_update(request):
    return request.getfuncargvalue(request.param)


@pytest.mark.usefixtures('supported_window_sizes')
def test_details_component_visibility(ui_job_templates_update):
    """Verify basic details form component visibility
    """
    assert ui_job_templates_update.details.machine_credential.is_displayed(), (
        'Machine credential form element unexpectedly not displayed')


@pytest.mark.github('https://github.com/ansible/ansible-tower/issues/1199')
@pytest.mark.usefixtures('authtoken')
def test_update_job_template(api_job_templates_pg, ui_job_templates_edit):
    """Basic end-to-end functional test for updating an existing job template
    """
    # get job_template data api side
    job_template_id = ui_job_templates_edit.kwargs.get('index')
    api_job_template_data = api_job_templates_pg.get(id=job_template_id).results[0]

    # query the table for the edited job_template
    results = ui_job_templates_edit.table.query(
        lambda r: r['name'].text == api_job_template_data.name)

    # fail informatively if we don't find the row of the job_template we're editing
    assert len(results) == 1, 'Unable to find row of edited resource'

    # verify that the row selection indicator is displayed for the row
    # corresponding to the job_template we're editing
    assert ui_job_templates_edit.table.row_is_selected(results[0]), (
        'Edited job_template row unexpectedly unselected')

    # make some data
    name = fauxfactory.gen_utf8()
    description = fauxfactory.gen_utf8()
    job_tags = fauxfactory.gen_utf8()

    # choose a verbosity option to select
    current_verbosity = ui_job_templates_edit.details.verbosity.selected_option
    verbosity_choices = ui_job_templates_edit.details.verbosity.options
    verbosity_choices.remove(current_verbosity)
    verbosity_choices.remove('Choose a verbosity')

    verbosity = random.choice(verbosity_choices)

    # update the job_template
    ui_job_templates_edit.details.name.set_text(name)
    ui_job_templates_edit.details.description.set_text(description)
    ui_job_templates_edit.details.job_tags.set_text(job_tags)
    ui_job_templates_edit.details.verbosity.select(verbosity)

    ui_job_templates_edit.details.save.click()

    # get job_template data api side
    api_job_template_data = api_job_templates_pg.get(id=job_template_id).results[0]

    # verify the update took place
    assert api_job_template_data.name == name, (
        'Unable to verify successful update of job_template resource')

    assert api_job_template_data.description == description, (
        'Unable to verify successful update of job_template resource')

    assert api_job_template_data.job_tags == job_tags, (
        'Unable to verify successful update of job_template resource')

    assert str(api_job_template_data.verbosity) in verbosity, (
        'Unable to verify successful update of job_template resource')

    # query the table for the edited job_template
    results = ui_job_templates_edit.table.query(
        lambda r: r['name'].text == api_job_template_data.name)

    # check that we find a row showing the updated job_template name
    assert len(results) == 1, 'Unable to find row of updated job template'


@pytest.mark.skipif(True, reason='not implemented')
@pytest.mark.usefixtures('authtoken')
def test_add_job_template(ui_job_templates):
    """Basic end-to-end verification for creating a job template
    """
    pass  # TODO: implement


@pytest.mark.skipif(True, reason='not implemented')
@pytest.mark.usefixtures('authtoken')
def test_delete_job_template(job_template, ui_job_templates):
    """Basic end-to-end verification for deleting a job template
    """
    pass  # TODO: implement
