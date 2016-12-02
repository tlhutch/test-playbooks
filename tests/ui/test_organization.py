import fauxfactory
import pytest

from towerkit.exceptions import NotFound


pytestmark = [pytest.mark.ui]


@pytest.fixture(scope='module')
def organization(api_v1):
    obj = api_v1.organizations.create()
    yield obj
    obj.silent_cleanup()


@pytest.fixture(scope='module')
def organizations(api_v1):
    org_objects = [api_v1.organizations.create() for _ in xrange(30)]
    yield org_objects
    for obj in org_objects:
        obj.silent_cleanup()


@pytest.mark.github('https://github.com/ansible/ansible-tower/issues/2895')
def test_api_referential_integrity(v1, ui, organizations):
    """Peform basic end-to-end read-only verification of displayed page
    content against data returned by the organizations api
    """
    api_orgs = v1.organizations.get()
    orgs = ui.organizations.get()
    # get list of displayed organization cards
    org_cards = orgs.cards
    # check the list count badge against the count reported by the API
    assert str(api_orgs.count) == orgs.list_badge.text
    # compare the actual number of cards to the item count label
    count_label = orgs.pagination.item_range[1]
    assert str(len(org_cards)) == count_label, 'item count label != number of cards'
    # get the organization names displayed on each card
    actual = sorted([c.label.text.lower() for c in org_cards])
    # get a subset of api organization names corresponding to those we expect
    # to be displayed on the first page
    expected = sorted([r.name.lower() for r in api_orgs.results])
    expected = expected[:len(org_cards)]
    assert actual == expected, 'Unexpected names: {0} != {1}'.format(actual, expected)


def test_edit_organization(v1, ui, organization):
    """Basic end-to-end functional test for updating an existing organization
    """
    edit = ui.organization_edit.get(id=organization.id)
    # make some data
    name = fauxfactory.gen_alphanumeric()
    description = fauxfactory.gen_alphanumeric()
    # update the organization
    edit.details.name.value = name
    edit.details.description.value = description
    # save the organization
    edit.details.save.click()
    edit.wait_until_loaded()
    # get organization data api side
    organization.get()
    # verify the update took place
    assert organization.name.lower() == name.lower(), (
        'Unable to verify successful update of organization')
    assert organization.description.lower() == description.lower(), (
        'Unable to verify successful update of organization')
    # query the table for the edited organization
    edit.search(name)
    results = edit.query_cards(lambda c: c.label.text.lower() == name.lower())
    # check that we find a row showing the updated organization name
    assert len(results) == 1, 'Unable to find row of updated organization'


def test_delete_organization(v1, ui, organization):
    """End-to-end functional test for deleting a organization
    """
    org_page = ui.organizations.get()
    search_name = organization.name.lower()
    # add a search filter for the organization
    org_page.search(search_name)
    # query the list for the newly created organization
    results = org_page.query_cards(lambda c: c.label.text.lower() == search_name)
    assert results, 'unable to locate organization'
    # delete the organization
    with org_page.handle_dialog(lambda d: d.action.click()):
        results.pop().delete.click()
    # verify deletion api-side
    with pytest.raises(NotFound):
        organization.get()
    # verify that the deleted resource is no longer displayed
    org_page.search.clear()
    org_page.search(search_name)
    results = org_page.query_cards(lambda c: c.label.text.lower() == search_name)
    assert not results


def test_create_organization(v1, ui):
    """End-to-end functional test for creating a organization
    """
    add = ui.organization_add.get()
    # make some data
    name = fauxfactory.gen_alphanumeric()
    # populate the form
    add.details.name.value = name
    add.details.description.value = fauxfactory.gen_alphanumeric()
    # save the organization
    add.details.save.click()
    add.wait_until_loaded()
    # verify the update took place api-side
    api_results = v1.organizations.get(name=name).results
    assert len(api_results) == 1, 'unable to verify creation of organization'
    # check that we find a row showing the updated organization name
    add.search(name)
    results = add.query_cards(lambda c: c.label.text.lower() == name.lower())
    assert results, 'unable to verify creation of organization'
    # check that the newly created resource has the card selection indicator
    assert add.selected_card.label.text.lower() == name.lower()
