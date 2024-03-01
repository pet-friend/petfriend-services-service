import pytest

from tests.tests_setup import BaseAPITestCase


class TestAuth(BaseAPITestCase):
    # See BaseAPITestCase.mock_auth fixture
    @pytest.mark.noauth
    async def test_get_stores_fails_if_no_auth(self) -> None:
        response = await self.client.get("/stores")
        assert response.status_code == 401
