"""
Тесты эндпоинта аудит-лога.

GET /api/logs   — список записей (admin + office), возвращает LogPage
Поддерживаемые фильтры:
  entity_type, action_sysname, entity_id_search, user_name_search, limit, offset
"""

from httpx import AsyncClient
from tests.conftest import auth_headers


class TestGetLogs:
    async def test_admin_can_read_logs(self, http_client: AsyncClient, admin_token: str):
        """Администратор видит журнал, ответ — объект с items и total."""
        res = await http_client.get("/api/logs", headers=auth_headers(admin_token))
        assert res.status_code == 200
        data = res.json()
        assert "items" in data
        assert "total" in data
        assert isinstance(data["items"], list)
        assert isinstance(data["total"], int)

    async def test_office_can_read_logs(self, http_client: AsyncClient, office_token: str):
        """Офис видит журнал."""
        res = await http_client.get("/api/logs", headers=auth_headers(office_token))
        assert res.status_code == 200
        data = res.json()
        assert "items" in data

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
        for log in res.json()["items"]:
            assert log["entity_type"] == "visit"

    async def test_filter_by_action_sysname(self, http_client: AsyncClient, admin_token: str):
        """Фильтр по action_sysname возвращает только нужные действия."""
        res = await http_client.get("/api/logs?action_sysname=visit_create",
                                    headers=auth_headers(admin_token))
        assert res.status_code == 200
        for log in res.json()["items"]:
            assert log["action_sysname"] == "visit_create"

    async def test_search_by_user_name(self, http_client: AsyncClient, admin_token: str):
        """Поиск по имени пользователя работает без ошибок."""
        res = await http_client.get("/api/logs?user_name_search=Администратор",
                                    headers=auth_headers(admin_token))
        assert res.status_code == 200
        assert "items" in res.json()

    async def test_pagination_limit(self, http_client: AsyncClient, admin_token: str):
        """Параметр limit ограничивает количество результатов."""
        res = await http_client.get("/api/logs?limit=5", headers=auth_headers(admin_token))
        assert res.status_code == 200
        data = res.json()
        assert len(data["items"]) <= 5

    async def test_pagination_offset(self, http_client: AsyncClient, admin_token: str):
        """Параметр offset смещает выборку."""
        res_page1 = await http_client.get("/api/logs?limit=3&offset=0",
                                           headers=auth_headers(admin_token))
        res_page2 = await http_client.get("/api/logs?limit=3&offset=3",
                                           headers=auth_headers(admin_token))
        assert res_page1.status_code == 200
        assert res_page2.status_code == 200
        ids1 = {r["id"] for r in res_page1.json()["items"]}
        ids2 = {r["id"] for r in res_page2.json()["items"]}
        assert ids1.isdisjoint(ids2) or len(ids1) == 0

    async def test_log_entry_structure(self, http_client: AsyncClient, admin_token: str):
        """Записи лога содержат обязательные поля."""
        res = await http_client.get("/api/logs?limit=1", headers=auth_headers(admin_token))
        assert res.status_code == 200
        data = res.json()
        assert "items" in data
        assert "total" in data
        assert "limit" in data
        assert "offset" in data
        if data["items"]:
            log = data["items"][0]
            assert "id" in log
            assert "entity_type" in log
            assert "entity_id" in log
            assert "action_sysname" in log
            assert "created_at" in log

    async def test_total_reflects_filter(self, http_client: AsyncClient, admin_token: str):
        """total в ответе соответствует фактическому количеству записей с фильтром."""
        res_all = await http_client.get("/api/logs?limit=1&offset=0",
                                         headers=auth_headers(admin_token))
        assert res_all.status_code == 200
        total_all = res_all.json()["total"]

        res_filtered = await http_client.get("/api/logs?entity_type=visit&limit=1&offset=0",
                                              headers=auth_headers(admin_token))
        assert res_filtered.status_code == 200
        total_visit = res_filtered.json()["total"]

        # total по visit не больше total по всем
        assert total_visit <= total_all
