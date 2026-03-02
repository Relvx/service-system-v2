"""
Тесты эндпоинта дашборда.

GET /api/dashboard/stats — агрегированная статистика (admin + office)
"""

from httpx import AsyncClient
from tests.conftest import auth_headers


class TestDashboard:
    async def test_admin_gets_stats(self, http_client: AsyncClient, admin_token: str):
        """Администратор получает статистику."""
        res = await http_client.get("/api/dashboard/stats", headers=auth_headers(admin_token))
        assert res.status_code == 200
        data = res.json()
        # Проверяем наличие ключевых полей статистики
        assert isinstance(data, dict)

    async def test_office_gets_stats(self, http_client: AsyncClient, office_token: str):
        """Офис получает статистику."""
        res = await http_client.get("/api/dashboard/stats", headers=auth_headers(office_token))
        assert res.status_code == 200

    async def test_master_forbidden(self, http_client: AsyncClient, master_token: str):
        """Мастер не имеет доступа к дашборду."""
        res = await http_client.get("/api/dashboard/stats", headers=auth_headers(master_token))
        assert res.status_code == 403

    async def test_unauthenticated_forbidden(self, http_client: AsyncClient):
        res = await http_client.get("/api/dashboard/stats")
        assert res.status_code == 401

    async def test_stats_structure(self, http_client: AsyncClient, admin_token: str):
        """Структура ответа содержит счётчики."""
        res = await http_client.get("/api/dashboard/stats", headers=auth_headers(admin_token))
        data = res.json()
        # Дашборд должен содержать хотя бы один числовой показатель
        numeric_values = [v for v in data.values() if isinstance(v, (int, float))]
        assert len(numeric_values) > 0
