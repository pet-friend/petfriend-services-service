from tests.tests_setup import BaseAPITestCase


class TestAuth(BaseAPITestCase):
    # See BaseAPITestCase.mock_auth fixture
    async def test_get_stores_fails_if_no_auth(self, mock_auth_error: None) -> None:
        response = await self.client.get("/stores")
        assert response.status_code == 401
