"""
Тесты эндпоинтов закупок.

GET  /api/purchases        — список закупок
POST /api/purchases        — создание закупки
PUT  /api/purchases/{id}   — обновление / смена статуса закупки
"""

from httpx import AsyncClient
from tests.conftest import auth_headers

PURCHASE_PAYLOAD = {
    "item": "__test__ Тестовая запчасть",
    "qty": 2,
    "status": "draft",
    "notes": "Для тестирования",
}


class TestGetPurchases:
    async def test_list_returns_list(self, http_client: AsyncClient, admin_token: str):
        res = await http_client.get("/api/purchases", headers=auth_headers(admin_token))
        assert res.status_code == 200
        assert isinstance(res.json(), list)

    async def test_filter_by_status(self, http_client: AsyncClient, admin_token: str):
        res = await http_client.get("/api/purchases?status=draft",
                                    headers=auth_headers(admin_token))
        assert res.status_code == 200
        for p in res.json():
            assert p["status"] == "draft"

    async def test_list_unauthenticated(self, http_client: AsyncClient):
        res = await http_client.get("/api/purchases")
        assert res.status_code == 401


class TestPurchaseCRUD:
    async def test_create(self, http_client: AsyncClient, admin_token: str):
        headers = auth_headers(admin_token)

        res = await http_client.post("/api/purchases", headers=headers, json=PURCHASE_PAYLOAD)
        assert res.status_code == 201
        data = res.json()
        assert data["item"] == PURCHASE_PAYLOAD["item"]
        assert data["status"] == "draft"
        assert float(data["qty"]) == 2.0

    async def test_update_purchase(self, http_client: AsyncClient, admin_token: str):
        headers = auth_headers(admin_token)

        res = await http_client.post("/api/purchases", headers=headers, json=PURCHASE_PAYLOAD)
        purchase_id = res.json()["id"]

        upd = await http_client.put(f"/api/purchases/{purchase_id}", headers=headers,
                                     json={"notes": "Обновлённые заметки"})
        assert upd.status_code == 200
        assert upd.json()["notes"] == "Обновлённые заметки"

    async def test_change_status(self, http_client: AsyncClient, admin_token: str):
        headers = auth_headers(admin_token)

        res = await http_client.post("/api/purchases", headers=headers, json=PURCHASE_PAYLOAD)
        purchase_id = res.json()["id"]

        upd = await http_client.put(f"/api/purchases/{purchase_id}", headers=headers,
                                     json={"status": "approved"})
        assert upd.status_code == 200
        assert upd.json()["status"] == "approved"

    async def test_update_not_found(self, http_client: AsyncClient, admin_token: str):
        fake_id = "00000000-0000-0000-0000-000000000000"
        res = await http_client.put(f"/api/purchases/{fake_id}",
                                     headers=auth_headers(admin_token),
                                     json={"status": "approved"})
        assert res.status_code == 404
