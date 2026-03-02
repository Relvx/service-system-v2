"""
Тесты эндпоинта аудит-лога.

GET /api/logs   — список записей (admin + office)
Поддерживаемые фильтры:
  entity_type, action_sysname, entity_id_search, user_name_search, limit, offset
"""

from httpx import AsyncClient
from tests.conftest import auth_headers


class TestGetLogs:
    async def test_admin_can_read_logs(self, http_client: AsyncClient, admin_token: str):
        """Администратор видит журнал."""
        res = await http_client.get("/api/logs", headers=auth_headers(admin_token))
        assert res.status_code == 200
        assert isinstance(res.json(), list)

    async def test_office_can_read_logs(self, http_client: AsyncClient, office_token: str):
        """Офис видит журнал."""
        res = await http_client.get("/api/logs", headers=auth_headers(office_token))
        assert res.status_code == 200

    async def test_master_forbidden(self, http_client: AsyncClient, master_token: str):
        """Мастер не имеет доступа к журналу."""
        res = await http_client.get("/api/logs", headers=auth_headers(master_token))
        assert res.status_code == 403

    async def test_unauthenticated_forbidden(self, http_client: AsyncClient):
        res = await http_client.get("/api/logs")
        assert res.status_code == 401

    async def test_filter_by_entity_type(self, http_client: AsyncClient, admin_token: str):
        """Фильтр по entity_type возвращает только записи нужного типа."""
        res = await http_client.get("/api/logs?entity_type=visit",
                                    headers=auth_headers(admin_token))
        assert res.status_code == 200
        for log in res.json():
            assert log["entity_type"] == "visit"

    async def test_filter_by_action_sysname(self, http_client: AsyncClient, admin_token: str):
        """Фильтр по action_sysname возвращает только нужные действия."""
        res = await http_client.get("/api/logs?action_sysname=visit_create",
                                    headers=auth_headers(admin_token))
        assert res.status_code == 200
        for log in res.json():
            assert log["action_sysname"] == "visit_create"

    async def test_search_by_user_name(self, http_client: AsyncClient, admin_token: str):
        """Поиск по имени пользователя работает без ошибок."""
        res = await http_client.get("/api/logs?user_name_search=Администратор",
                                    headers=auth_headers(admin_token))
        assert res.status_code == 200
        assert isinstance(res.json(), list)

    async def test_pagination_limit(self, http_client: AsyncClient, admin_token: str):
        """Параметр limit ограничивает количество результатов."""
        res = await http_client.get("/api/logs?limit=5", headers=auth_headers(admin_token))
        assert res.status_code == 200
        assert len(res.json()) <= 5

    async def test_pagination_offset(self, http_client: AsyncClient, admin_token: str):
        """Параметр offset смещает выборку."""
        res_page1 = await http_client.get("/api/logs?limit=3&offset=0",
                                           headers=auth_headers(admin_token))
        res_page2 = await http_client.get("/api/logs?limit=3&offset=3",
                                           headers=auth_headers(admin_token))
        assert res_page1.status_code == 200
        assert res_page2.status_code == 200
        # Если записей достаточно — страницы не совпадают
        ids1 = {r["id"] for r in res_page1.json()}
        ids2 = {r["id"] for r in res_page2.json()}
        assert ids1.isdisjoint(ids2) or len(ids1) == 0

    async def test_log_entry_structure(self, http_client: AsyncClient, admin_token: str):
        """Записи лога содержат обязательные поля."""
        res = await http_client.get("/api/logs?limit=1", headers=auth_headers(admin_token))
        assert res.status_code == 200
        if res.json():
            log = res.json()[0]
            assert "id" in log
            assert "entity_type" in log
            assert "entity_id" in log
            assert "action_sysname" in log
            assert "created_at" in log
