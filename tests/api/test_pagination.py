"""Tests for pagination."""
import random

import pytest

from tests.api import APITest


@pytest.mark.usefixtures('authtoken')
class TestPagination(APITest):

    @pytest.fixture(scope='class', autouse=True)
    def create_users(self, request, authtoken, v2_class):
        """Create 200+ users. MAX_PAGE_SIZE defaults to 200."""
        for _ in range(201):
            user = v2_class.users.create()
            request.addfinalizer(user.delete)

    def test_page_size(self, v2):
        """Ensure the user can specify the page size."""
        page_sizes = {random.randint(1, 199) for _ in range(3)}

        # let's add a page size equals MAX_PAGE_SIZE
        page_sizes.add(200)

        # let's add a page size greater than MAX_PAGE_SIZE to check if the
        # results will be caped at MAX_PAGE_SIZE.
        page_sizes.add(random.randint(201, 250))

        for page_size in page_sizes:
            response = v2.users.get(page_size=page_size)
            expected_page_size = page_size if page_size <= 200 else 200
            assert len(response['results']) == expected_page_size, response

    def test_next_page_page_size(self, v2):
        """Ensure the next url has the page_size equals to MAX_PAGE_SIZE.

        ``page_size`` parameter on the URL can't be greater than the
        MAX_PAGE_SIZE even if the user specify it otherwise.
        """
        response = v2.users.get(page_size=250)
        assert 'page_size=200' in response['next']
        assert response['previous'] is None

    def test_previous_page_page_size(self, v2):
        """Ensure the previous url has the page_size equals to MAX_PAGE_SIZE.

        ``page_size`` parameter on the URL can't be greater than the
        MAX_PAGE_SIZE even if the user specify it otherwise.
        """
        response = v2.users.get(page_size=250, page=2)
        assert 'page_size=200' in response['previous']
        assert response['next'] is None
