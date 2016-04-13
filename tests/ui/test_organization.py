import pytest

pytestmark = [pytest.mark.ui, pytest.mark.nondestructive]


@pytest.mark.github('https://github.com/ansible/ansible-tower/issues/1466')
@pytest.mark.usefixtures(
    'authtoken',
    'install_enterprise_license_unlimited',
    'populate_organizations',
    'maximized_window_size'
)
def test_api_referential_integrity(api_organizations_pg, ui_organizations):
    """Peform basic end-to-end read-only verification of displayed page
    content against data returned by the organizations api
    """
    api_organizations_pg.get()

    assert api_organizations_pg.count == ui_organizations.badge_number, (
        'organizations api count and displayed badge number '
        'unexpectedly different')

    # get the actual number of organization cards present on the page
    card_count = len(ui_organizations.displayed_card_labels)
    # get the item count indicated by the pagination label
    count_label = ui_organizations.pagination.item_range[1]

    assert card_count == count_label, (
        'The number of displayed organization cards differs '
        'from the list panel item count label')

    # get the organization names displayed on each card
    displayed_names = ui_organizations.displayed_card_labels
    displayed_names = sorted(map(ui_organizations._normalize_text, displayed_names))

    # retrieve organization names from the associated api endpoint
    expected_names = [r.name for r in api_organizations_pg.results]
    expected_names = sorted(map(ui_organizations._normalize_text, expected_names))

    # get a subset of api organization names corresponding to those we expect
    # to be displayed on the first page
    expected_names = expected_names[:card_count]

    assert displayed_names == expected_names, (
        'Unexpected card names: {0} != {1}'.format(
            displayed_names, expected_names))


@pytest.mark.usefixtures(
    'authtoken',
    'install_enterprise_license_unlimited',
    'another_organization',
    'supported_window_sizes'
)
def test_component_visibility(ui_organizations):
    """Verify basic page component visibility
    """
    default_card = ui_organizations.get_card('default')

    assert default_card.is_displayed(), (
        'Default organization card unexpectedly not displayed')

    assert default_card.edit.is_displayed(), (
        'Edit action button unexpectedly not displayed')

    assert default_card.edit.is_clickable(), (
        'Edit action button unexpectedly not clickable')

    assert default_card.delete.is_displayed(), (
        'Delete action button unexpectedly not displayed')

    assert default_card.delete.is_clickable(), (
        'Delete action button unexpectedly not clickable')

    assert ui_organizations.add_button.is_displayed(), (
        'Add button unexpectedly not displayed')

    assert ui_organizations.add_button.is_clickable(), (
        'Add button unexpectedly not displayed')

    expected_links = [
        'users',
        'teams',
        'inventories',
        'projects',
        'job templates',
        'admins'
    ]

    displayed_links = [n.lower() for n in default_card.displayed_link_names]

    for expected_name in expected_links:
        assert expected_name in displayed_links, (
            'Card link with name {0} unexpectedly not displayed'.format(
                expected_name))

    for displayed_name in displayed_links:
        assert displayed_name in expected_links, (
            'Card link with name {0} unexpectedly displayed'.format(
                displayed_name))

    assert displayed_links == expected_links, (
        'Unexpected card link ordering: {0} != {1}'.format(
            displayed_links, expected_links))

    for link_name in displayed_links:
        assert default_card.get_link(link_name).is_clickable(), (
            'Card link with name {0} unexpectedly not clickable'.format(
                link_name))


@pytest.mark.skipif(True, reason='not implemented')
@pytest.mark.usefixtures('authtoken')
def test_create_organization(api_organizations_pg, ui_organizations_add):
    """Basic end-to-end verification for creating an organization
    """
    pass  # TODO: implement


@pytest.mark.skipif(True, reason='not implemented')
@pytest.mark.usefixtures('authtoken')
def test_update_organization(organization,
                             api_organizations_pg, ui_organizations):
    """Basic end-to-end verification for updating an organization
    """
    pass  # TODO: implement


@pytest.mark.skipif(True, reason='not implemented')
@pytest.mark.usefixtures(
    'authtoken',
    'install_enterprise_license_unlimited',
)
def test_delete_organization(organization,
                             api_organizations_pg, ui_organizations):
    """Basic end-to-end verification for deleting an organization
    """
    pass  # TODO: implement


@pytest.mark.skipif(True, reason='not implemented')
@pytest.mark.usefixtures('authtoken')
def test_associate_user(organization, anonymous_user, ui_organizations):
    """Verify basic operation of associating users
    """
    pass  # TODO: implement


@pytest.mark.skipif(True, reason='not implemented')
@pytest.mark.usefixtures('authtoken')
def test_associate_admin(organization,
                         anonymous_user, org_user, ui_organizations):
    """Verify basic operation of associating administrators
    """
    pass  # TODO: implement
