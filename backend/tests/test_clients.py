"""
Тесты CRUD эндпоинтов клиентов.

GET    /api/clients           — список клиентов
GET    /api/clients/{id}      — клиент по ID
POST   /api/clients           — создание клиента
PUT    /api/clients/{id}      — обновление клиента
DELETE /api/clients/{id}      — удаление клиента
"""

import pytest
from httpx import AsyncClient

from tests.conftest import auth_headers

CLIENT_PAYLOAD = {
    "name": "__test__ ООО Тест",
    "inn": "1234567890",
    "kpp": "123456789",
    "contacts": "+7-900-000-00-00",
    "contact_person": "Иванов Иван",
    "notes": "Тестовый клиент",
}


class TestGetClients:
    async def test_list_returns_list(self, http_client: AsyncClient, admin_token: str):
        """GET /clients возвращает список."""
        res = await http_client.get("/api/clients", headers=auth_headers(admin_token))
        assert res.status_code == 200
        assert isinstance(res.json(), list)

    async def test_list_search(self, http_client: AsyncClient, admin_token: str):
        """Поиск по имени фильтрует результаты."""
        res = await http_client.get("/api/clients?search=nonexistent_xyz_12345",
                                    headers=auth_headers(admin_token))
        assert res.status_code == 200
        assert res.json() == []

    async def test_list_unauthenticated(self, http_client: AsyncClient):
        """Без токена → 401."""
        res = await http_client.get("/api/clients")
        assert res.status_code == 401


class TestClientCRUD:
    async def test_create_and_delete(self, http_client: AsyncClient, admin_token: str):
        """Создание клиента возвращает 201 с данными, затем удаление 204."""
        headers = auth_headers(admin_token)

        # create
        res = await http_client.post("/api/clients", headers=headers, json=CLIENT_PAYLOAD)
        assert res.status_code == 201
        data = res.json()
        client_id = data["id"]
        assert data["name"] == CLIENT_PAYLOAD["name"]
        assert data["inn"] == CLIENT_PAYLOAD["inn"]
        assert data["is_active"] is True

        # delete
        del_res = await http_client.delete(f"/api/clients/{client_id}", headers=headers)
        assert del_res.status_code == 204

    async def test_get_by_id(self, http_client: AsyncClient, admin_token: str):
        """GET /{id} возвращает созданного клиента."""
        headers = auth_headers(admin_token)

        res = await http_client.post("/api/clients", headers=headers, json=CLIENT_PAYLOAD)
        assert res.status_code == 201
        client_id = res.json()["id"]

        get_res = await http_client.get(f"/api/clients/{client_id}", headers=headers)
        assert get_res.status_code == 200
        assert get_res.json()["id"] == client_id

        await http_client.delete(f"/api/clients/{client_id}", headers=headers)

    async def test_get_not_found(self, http_client: AsyncClient, admin_token: str):
        """GET несуществующего ID → 404."""
        fake_id = "00000000-0000-0000-0000-000000000000"
        res = await http_client.get(f"/api/clients/{fake_id}", headers=auth_headers(admin_token))
        assert res.status_code == 404

    async def test_update_client(self, http_client: AsyncClient, admin_token: str):
        """PUT обновляет поля клиента."""
        headers = auth_headers(admin_token)

        res = await http_client.post("/api/clients", headers=headers, json=CLIENT_PAYLOAD)
        client_id = res.json()["id"]

        upd = await http_client.put(f"/api/clients/{client_id}", headers=headers,
                                     json={"name": "__test__ Обновлённый"})
        assert upd.status_code == 200
        assert upd.json()["name"] == "__test__ Обновлённый"

        await http_client.delete(f"/api/clients/{client_id}", headers=headers)

    async def test_delete_not_found(self, http_client: AsyncClient, admin_token: str):
        """DELETE несуществующего ID → 404."""
        fake_id = "00000000-0000-0000-0000-000000000001"
        res = await http_client.delete(f"/api/clients/{fake_id}", headers=auth_headers(admin_token))
        assert res.status_code == 404
