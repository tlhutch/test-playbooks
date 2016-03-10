import fauxfactory
import pytest


@pytest.fixture
def populate_job_templates(
    authtoken,
    total_rows,
    api_job_templates_pg,
    job_template
):
    payload = job_template.json
    remaining = total_rows - api_job_templates_pg.get().count

    for _ in xrange(remaining):
        payload.update(name='ui-%s' % fauxfactory.gen_utf8())
        api_job_templates_pg.post(payload)


@pytest.fixture
def populate_teams(
    authtoken,
    total_rows,
    organization,
    api_teams_pg
):
    remaining = total_rows - api_teams_pg.get().count

    for _ in xrange(remaining):
        organization.get_related('teams').post({
            'name': 'ui-team-%s' % fauxfactory.gen_utf8(),
            'description': fauxfactory.gen_utf8(),
            'organization': organization.id
        })


@pytest.fixture
def populate_jobs(
    authtoken,
    install_enterprise_license_unlimited,
    total_rows,
    api_jobs_pg,
    job_template_ping
):
    remaining = total_rows - api_jobs_pg.get().count

    for _ in xrange(remaining):
        job_template_ping.launch()
    job_template_ping.launch().wait_until_completed()


@pytest.fixture
def populate_users(
    authtoken,
    total_rows,
    api_users_pg,
    user_password
):
    remaining = total_rows - api_users_pg.get().count

    for _ in xrange(remaining):
        api_users_pg.post({
            'username': 'anonymous_%s' % fauxfactory.gen_alphanumeric(),
            'first_name': fauxfactory.gen_utf8(),
            'last_name': fauxfactory.gen_utf8(),
            'email': fauxfactory.gen_email(),
            'password': user_password
        })


@pytest.fixture
def populate_inventories(
    authtoken,
    total_rows,
    default_organization,
    api_inventories_pg
):
    remaining = total_rows - api_inventories_pg.get().count

    for _ in xrange(remaining):
        api_inventories_pg.post({
            'name': 'ui-%s' % fauxfactory.gen_alphanumeric(),
            'description': fauxfactory.gen_utf8(),
            'organization': default_organization.id
        })


@pytest.fixture
def populate_projects(
    authtoken,
    total_rows,
    default_organization,
    api_projects_pg
):
    remaining = total_rows - api_projects_pg.get().count

    for _ in xrange(remaining):
        default_organization.get_related('projects').post({
            'name': "ansible-playbooks.git - %s" % fauxfactory.gen_utf8(),
            'scm_url': 'https://github.com/jlaska/ansible-playbooks.git',
            'scm_clean': False,
            'scm_delete_on_update': False,
            'scm_delete_on_launch': False
        })


@pytest.fixture
def populate_organizations(
    request,
    authtoken,
    total_rows,
    install_enterprise_license_unlimited,
    api_organizations_pg
):
    remaining = total_rows - api_organizations_pg.get().count

    for _ in xrange(remaining):
        data = {}
        data['name'] = 'ui-organization-%s' % fauxfactory.gen_utf8()
        data['description'] = fauxfactory.gen_utf8()

        api_organizations_pg.post(data)
