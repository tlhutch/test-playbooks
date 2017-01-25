import fauxfactory
import pytest

pytestmark = [pytest.mark.ui]


@pytest.fixture(scope='module')
def job(session_job_template):
    obj = session_job_template.launch().wait_until_completed()
    yield obj
    obj.silent_cleanup()


@pytest.mark.github('https://github.com/ansible/ansible-tower/issues/4860')
class BaseTestSearchTags(object):

    def test_multi_tag_add_remove(self, search):
        search('foo')
        search('bar')
        search('fiz')

        assert len(search.tags) == 3
        assert 'foo' in search.tags[0].text
        assert 'bar' in search.tags[1].text
        assert 'fiz' in search.tags[2].text

        search.tags.pop().delete.click()
        search.tags.pop().delete.click()
        search.tags.pop().delete.click()

        assert len(search.tags) == 0

    def test_multi_tag_add_clear(self, search):
        [search(fauxfactory.gen_alphanumeric()) for _ in xrange(5)]
        assert len(search.tags) == 5

        search.clear()
        assert len(search.tags) == 0


class TestJobResultSearchTags(BaseTestSearchTags):

    @pytest.fixture
    def search(self, ui, job):
        yield ui.job_details.get(id=job.id).search


class TestJobTemplateSearchTags(BaseTestSearchTags):

    @pytest.fixture
    def search(self, ui):
        yield ui.job_templates.get().search


class TestActivityStreamSearchTags(BaseTestSearchTags):

    @pytest.fixture
    def search(self, ui, job):
        yield ui.activity_stream.get().search


class TestProjectSearchTags(BaseTestSearchTags):

    @pytest.fixture
    def search(self, ui, session_project):
        yield ui.projects.get().search


class TestUserSearchTags(BaseTestSearchTags):

    @pytest.fixture
    def search(self, ui, session_user):
        yield ui.users.get().search


class TestInventorySearchTags(BaseTestSearchTags):

    @pytest.fixture
    def search(self, ui, session_inventory):
        yield ui.inventories.get().search


class TestCredentialSearchTags(BaseTestSearchTags):

    @pytest.fixture
    def search(self, ui, session_machine_credential):
        yield ui.credentials.get().search


class TestOrganizationSearchTags(BaseTestSearchTags):

    @pytest.fixture
    def search(self, ui, session_org):
        yield ui.organizations.get().search


class TestTeamSearchTags(BaseTestSearchTags):

    @pytest.fixture
    def search(self, ui, session_team):
        yield ui.teams.get().search
