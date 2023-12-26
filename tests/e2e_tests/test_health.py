from tests.tests_setup import BaseAPITestCase


class TestHealth(BaseAPITestCase):
    async def test_get_server_health(self) -> None:
        response = await self.client.get("/health")
        assert response.status_code == 200
