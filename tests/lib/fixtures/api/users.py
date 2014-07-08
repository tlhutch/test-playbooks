import pytest

@pytest.fixture(scope="class")
def admin_user(request, authtoken, api_users_pg):
    return api_users_pg.get(username__iexact='admin').results[0]
