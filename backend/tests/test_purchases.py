"""
Тесты эндпоинтов закупок.

GET    /api/purchases           — список закупок (с фильтрами status, site_id, show_archived)
POST   /api/purchases           — создание закупки
PUT    /api/purchases/{id}      — обновление / смена статуса закупки
PATCH  /api/purchases/{id}/archive   — архивирование
PATCH  /api/purchases/{id}/unarchive — восстановление из архива
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
        fake_id = 999999
        res = await http_client.put(f"/api/purchases/{fake_id}",
                                     headers=auth_headers(admin_token),
                                     json={"status": "approved"})
        assert res.status_code == 404


class TestPurchaseBlock5:
    """Блок 5: создание закупки с привязкой к дефекту и объекту."""

    async def test_create_with_site_id(self, http_client: AsyncClient, admin_token: str,
                                       site_id: int):
        """Создание закупки с site_id → site_title подтягивается из JOIN."""
        headers = auth_headers(admin_token)
        res = await http_client.post("/api/purchases", headers=headers, json={
            **PURCHASE_PAYLOAD,
            "site_id": site_id,
        })
        assert res.status_code == 201
        data = res.json()
        assert data["site_id"] == site_id
        assert data["site_title"] is not None

    async def test_create_with_defect_id(self, http_client: AsyncClient, admin_token: str):
        """Создание закупки с defect_id → defect_title подтягивается из JOIN."""
        headers = auth_headers(admin_token)
        # создаём дефект
        d_res = await http_client.post("/api/defects", headers=headers, json={
            "title": "__test__ Дефект для закупки",
            "priority": "medium",
            "action_type": "repair",
        })
        defect_id = d_res.json()["id"]

        res = await http_client.post("/api/purchases", headers=headers, json={
            **PURCHASE_PAYLOAD,
            "defect_id": defect_id,
        })
        assert res.status_code == 201
        data = res.json()
        assert data["defect_id"] == defect_id
        assert data["defect_title"] == "__test__ Дефект для закупки"

    async def test_create_linked_to_defect_and_site(self, http_client: AsyncClient,
                                                      admin_token: str, site_id: int):
        """Создание закупки из карточки дефекта: defect_id и site_id заполнены оба."""
        headers = auth_headers(admin_token)
        d_res = await http_client.post("/api/defects", headers=headers, json={
            "title": "__test__ Дефект + объект",
            "priority": "high",
            "action_type": "replace",
            "site_id": site_id,
        })
        defect_id = d_res.json()["id"]

        res = await http_client.post("/api/purchases", headers=headers, json={
            **PURCHASE_PAYLOAD,
            "defect_id": defect_id,
            "site_id": site_id,
        })
        assert res.status_code == 201
        data = res.json()
        assert data["defect_id"] == defect_id
        assert data["site_id"] == site_id
        assert data["defect_title"] is not None
        assert data["site_title"] is not None

    async def test_filter_by_defect_id(self, http_client: AsyncClient, admin_token: str):
        """GET /purchases?defect_id=... возвращает только закупки нужного дефекта."""
        headers = auth_headers(admin_token)
        d_res = await http_client.post("/api/defects", headers=headers, json={
            "title": "__test__ Дефект для фильтрации закупок",
            "priority": "low",
            "action_type": "repair",
        })
        defect_id = d_res.json()["id"]

        await http_client.post("/api/purchases", headers=headers, json={
            **PURCHASE_PAYLOAD, "defect_id": defect_id,
        })
        res = await http_client.get(f"/api/purchases?defect_id={defect_id}", headers=headers)
        assert res.status_code == 200
        data = res.json()
        assert len(data) >= 1
        for p in data:
            assert p["defect_id"] == defect_id


class TestPurchaseBlock6:
    """Блок 6: архивирование закупок, фильтр по объекту, is_archived в ответе."""

    async def test_archive_purchase(self, http_client: AsyncClient, admin_token: str):
        """PATCH /archive переводит закупку в архив (is_archived=true)."""
        headers = auth_headers(admin_token)
        res = await http_client.post("/api/purchases", headers=headers, json=PURCHASE_PAYLOAD)
        pid = res.json()["id"]

        arc = await http_client.patch(f"/api/purchases/{pid}/archive", headers=headers)
        assert arc.status_code == 200
        assert arc.json()["is_archived"] is True

    async def test_archived_hidden_by_default(self, http_client: AsyncClient, admin_token: str):
        """Архивированная закупка не попадает в стандартный список."""
        headers = auth_headers(admin_token)
        res = await http_client.post("/api/purchases", headers=headers, json={
            **PURCHASE_PAYLOAD, "item": "__test__ Архивная закупка"
        })
        pid = res.json()["id"]
        await http_client.patch(f"/api/purchases/{pid}/archive", headers=headers)

        lst = await http_client.get("/api/purchases", headers=headers)
        ids = [p["id"] for p in lst.json()]
        assert pid not in ids

    async def test_show_archived_param(self, http_client: AsyncClient, admin_token: str):
        """show_archived=true включает архивные закупки в список."""
        headers = auth_headers(admin_token)
        res = await http_client.post("/api/purchases", headers=headers, json={
            **PURCHASE_PAYLOAD, "item": "__test__ Показать архивную"
        })
        pid = res.json()["id"]
        await http_client.patch(f"/api/purchases/{pid}/archive", headers=headers)

        lst = await http_client.get("/api/purchases?show_archived=true", headers=headers)
        ids = [p["id"] for p in lst.json()]
        assert pid in ids

    async def test_unarchive_purchase(self, http_client: AsyncClient, admin_token: str):
        """PATCH /unarchive восстанавливает закупку из архива."""
        headers = auth_headers(admin_token)
        res = await http_client.post("/api/purchases", headers=headers, json=PURCHASE_PAYLOAD)
        pid = res.json()["id"]

        await http_client.patch(f"/api/purchases/{pid}/archive", headers=headers)
        una = await http_client.patch(f"/api/purchases/{pid}/unarchive", headers=headers)
        assert una.status_code == 200
        assert una.json()["is_archived"] is False

        # снова видна в обычном списке
        lst = await http_client.get("/api/purchases", headers=headers)
        ids = [p["id"] for p in lst.json()]
        assert pid in ids

    async def test_archive_not_found(self, http_client: AsyncClient, admin_token: str):
        """PATCH /archive несуществующей закупки → 404."""
        res = await http_client.patch("/api/purchases/999999/archive",
                                      headers=auth_headers(admin_token))
        assert res.status_code == 404

    async def test_filter_by_site_id(self, http_client: AsyncClient, admin_token: str,
                                     site_id: int):
        """GET /purchases?site_id=... возвращает только закупки нужного объекта."""
        headers = auth_headers(admin_token)
        await http_client.post("/api/purchases", headers=headers, json={
            **PURCHASE_PAYLOAD, "site_id": site_id,
        })
        res = await http_client.get(f"/api/purchases?site_id={site_id}", headers=headers)
        assert res.status_code == 200
        data = res.json()
        assert len(data) >= 1
        for p in data:
            assert p["site_id"] == site_id

    async def test_is_archived_field_present(self, http_client: AsyncClient, admin_token: str):
        """Поле is_archived присутствует в ответе при создании закупки."""
        headers = auth_headers(admin_token)
        res = await http_client.post("/api/purchases", headers=headers, json=PURCHASE_PAYLOAD)
        assert res.status_code == 201
        assert "is_archived" in res.json()
        assert res.json()["is_archived"] is False
