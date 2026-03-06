"""
Тесты CRUD эндпоинтов объектов обслуживания.

GET    /api/sites           — список объектов
GET    /api/sites/{id}      — объект по ID
POST   /api/sites           — создание объекта
PUT    /api/sites/{id}      — обновление объекта
DELETE /api/sites/{id}      — удаление объекта
"""

from httpx import AsyncClient
from tests.conftest import auth_headers

SITE_PAYLOAD = {
    "title": "__test__ Тестовый объект",
    "address": "г. Тест, ул. Тестовая, д. 1",
    "latitude": 55.7558,
    "longitude": 37.6173,
    "access_notes": "Вход через КПП",
    "service_frequency": "monthly",
}


class TestGetSites:
    async def test_list_returns_list(self, http_client: AsyncClient, admin_token: str):
        res = await http_client.get("/api/sites", headers=auth_headers(admin_token))
        assert res.status_code == 200
        assert isinstance(res.json(), list)

    async def test_list_search_empty(self, http_client: AsyncClient, admin_token: str):
        res = await http_client.get("/api/sites?search=xyz_nonexistent_12345",
                                    headers=auth_headers(admin_token))
        assert res.status_code == 200
        assert res.json() == []

    async def test_list_unauthenticated(self, http_client: AsyncClient):
        res = await http_client.get("/api/sites")
        assert res.status_code == 401


class TestSiteCRUD:
    async def test_create_and_delete(self, http_client: AsyncClient, admin_token: str):
        headers = auth_headers(admin_token)

        res = await http_client.post("/api/sites", headers=headers, json=SITE_PAYLOAD)
        assert res.status_code == 201
        data = res.json()
        site_id = data["id"]
        assert data["title"] == SITE_PAYLOAD["title"]
        assert data["is_active"] is True

        del_res = await http_client.delete(f"/api/sites/{site_id}", headers=headers)
        assert del_res.status_code == 204

    async def test_get_by_id(self, http_client: AsyncClient, admin_token: str):
        headers = auth_headers(admin_token)

        res = await http_client.post("/api/sites", headers=headers, json=SITE_PAYLOAD)
        site_id = res.json()["id"]

        get_res = await http_client.get(f"/api/sites/{site_id}", headers=headers)
        assert get_res.status_code == 200
        assert get_res.json()["id"] == site_id

        await http_client.delete(f"/api/sites/{site_id}", headers=headers)

    async def test_get_not_found(self, http_client: AsyncClient, admin_token: str):
        fake_id = 999999
        res = await http_client.get(f"/api/sites/{fake_id}", headers=auth_headers(admin_token))
        assert res.status_code == 404

    async def test_update_site(self, http_client: AsyncClient, admin_token: str):
        headers = auth_headers(admin_token)

        res = await http_client.post("/api/sites", headers=headers, json=SITE_PAYLOAD)
        site_id = res.json()["id"]

        upd = await http_client.put(f"/api/sites/{site_id}", headers=headers,
                                     json={"title": "__test__ Обновлённый объект"})
        assert upd.status_code == 200
        assert upd.json()["title"] == "__test__ Обновлённый объект"

        await http_client.delete(f"/api/sites/{site_id}", headers=headers)

    async def test_filter_by_client(self, http_client: AsyncClient, admin_token: str):
        """Фильтр по несуществующему client_id возвращает пустой список."""
        fake_id = 999999
        res = await http_client.get(f"/api/sites?client_id={fake_id}",
                                    headers=auth_headers(admin_token))
        assert res.status_code == 200
        assert res.json() == []


class TestSiteArchive:
    async def test_archive_site(self, http_client: AsyncClient, admin_token: str):
        """PATCH /archive устанавливает is_archived=true."""
        headers = auth_headers(admin_token)

        res = await http_client.post("/api/sites", headers=headers, json=SITE_PAYLOAD)
        site_id = res.json()["id"]

        arc = await http_client.patch(f"/api/sites/{site_id}/archive", headers=headers)
        assert arc.status_code == 200
        assert arc.json()["is_archived"] is True

        await http_client.delete(f"/api/sites/{site_id}", headers=headers)

    async def test_archived_hidden_by_default(self, http_client: AsyncClient, admin_token: str):
        """Архивированный объект не появляется в стандартном списке."""
        headers = auth_headers(admin_token)

        res = await http_client.post("/api/sites", headers=headers, json={
            **SITE_PAYLOAD, "title": "__test__ Архивный объект"
        })
        site_id = res.json()["id"]
        await http_client.patch(f"/api/sites/{site_id}/archive", headers=headers)

        list_res = await http_client.get("/api/sites", headers=headers)
        ids = [s["id"] for s in list_res.json()]
        assert site_id not in ids

        await http_client.delete(f"/api/sites/{site_id}", headers=headers)

    async def test_show_archived_param(self, http_client: AsyncClient, admin_token: str):
        """show_archived=true включает архивные объекты в список."""
        headers = auth_headers(admin_token)

        res = await http_client.post("/api/sites", headers=headers, json={
            **SITE_PAYLOAD, "title": "__test__ Показать архивный объект"
        })
        site_id = res.json()["id"]
        await http_client.patch(f"/api/sites/{site_id}/archive", headers=headers)

        list_res = await http_client.get("/api/sites?show_archived=true", headers=headers)
        ids = [s["id"] for s in list_res.json()]
        assert site_id in ids

        await http_client.delete(f"/api/sites/{site_id}", headers=headers)
