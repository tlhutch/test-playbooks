import time 

import fauxfactory
import pytest

from common.exceptions import NotFound_Exception

pytestmark = [
    pytest.mark.ui,
    pytest.mark.nondestructive,
    pytest.mark.usefixtures(
        'module_install_enterprise_license',
        'max_window',
    )
]


def test_edit_organization(api_organizations_pg, ui_organization_edit):
    """Basic end-to-end functional test for updating an existing organization
    """
    # make some data
    name = fauxfactory.gen_alphanumeric()
    description = fauxfactory.gen_alphanumeric()
    # update the organization
    ui_organization_edit.details.name.set_value(name)
    ui_organization_edit.details.description.set_value(description)
    # save the organization
    ui_organization_edit.details.save.click()
    ui_organization_edit.wait_until_loaded()
    # get organization data api side
    api_organization = api_organizations_pg.get(
        id=ui_organization_edit.kwargs['id']).results[0]
    # verify the update took place
    assert api_organization.name.lower() == name.lower(), (
        'Unable to verify successful update of organization')
    assert api_organization.description.lower() == description.lower(), (
        'Unable to verify successful update of organization')
    # query the table for the edited organization
    results = ui_organization_edit.query_cards(
        lambda c: c.name.text.lower() == name.lower())
    # check that we find a row showing the updated organization name
    assert len(results) == 1, 'Unable to find row of updated organization'


def test_delete_organization(factories, ui_organizations):
    """Basic end-to-end verification for deleting a organization
    """
    organization = factories.organization()
    search_name = organization.name.lower()
    # add a search filter for the organization
    ui_organizations.driver.refresh()
    ui_organizations.wait_until_loaded()
    ui_organizations.list_search.add_filter('name', search_name)
    # query the list for the newly created organization
    results = ui_organizations.query_cards(
        lambda c: c.name.text.lower() == search_name)
    assert results, 'unable to locate organization'
    # delete the organization
    results.pop().delete.click()
    # confirm deletion
    ui_organizations.dialog.confirm.click()
    ui_organizations.wait_until_loaded()
    # verify deletion api-side
    with pytest.raises(NotFound_Exception):
        organization.get()
    # verify that the deleted resource is no longer displayed
    results = ui_organizations.query_cards(
        lambda c: c.name.text.lower() == search_name)
    assert not results


def test_create_organization(factories, api_organizations_pg, ui_organization_add):
    """Basic end-to-end verification for creating a organization
    """
    # make some data
    name = fauxfactory.gen_alphanumeric()
    # populate the form
    ui_organization_add.details.name.set_value(name)
    ui_organization_add.details.description.set_value(fauxfactory.gen_alphanumeric())
    # save the organization
    ui_organization_add.details.save.click()
    ui_organization_add.wait_until_loaded()
    # verify the update took place api-side
    time.sleep(5)
    api_results = api_organizations_pg.get(name=name).results
    assert api_results, 'unable to verify creation of organization'
    # check for expected url content
    expected_url_content = '/#/organizations/{0}'.format(api_results[0].id)
    assert expected_url_content in ui_organization_add.driver.current_url
    # check that we find a row showing the updated organization name
    results = ui_organization_add.query_cards(lambda c: c.name.text.lower() == name.lower())
    assert results, 'unable to verify creation of organization'
    # check that the newly created resource has the card selection indicator
    assert ui_organization_add.selected_card.name.text.lower() == name.lower()

