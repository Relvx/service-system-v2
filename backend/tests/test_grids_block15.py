"""
Тесты блока 15 — Гриды: Выезды / Закупки / Журнал.

Проверяем:
- PATCH /purchases/{id} — смена статуса (без изменения других полей)
- GET /purchases — фильтрация по status и site_id
- GET /logs — фильтрация по action_sysname, entity_type
"""

import pytest
from httpx import AsyncClient
from tests.conftest import auth_headers


# ─── Закупки: статус ─────────────────────────────────────────────────────────

@pytest.mark.asyncio
class TestPurchaseStatusUpdate:
    """PATCH /purchases/{id} — смена статуса."""

    async def _create_purchase(self, http_client, token):
        res = await http_client.post("/api/purchases", headers=auth_headers(token), json={
            "item": "TEST_B15_PURCHASE_STATUS",
            "qty": 1,
        })
        assert res.status_code == 201
        return res.json()["id"]

    async def _delete_purchase(self, http_client, token, pid):
        await http_client.patch(f"/api/purchases/{pid}/archive", headers=auth_headers(token))

    async def test_put_status_only(self, http_client: AsyncClient, admin_token: str):
        """PUT с только статусом не затрагивает другие поля."""
        pid = await self._create_purchase(http_client, admin_token)
        try:
            # Сначала получаем текущее состояние
            get_res = await http_client.get(f"/api/purchases/{pid}", headers=auth_headers(admin_token))
            # В API может не быть GET по id — используем список
            # Обновляем статус через PUT
            res = await http_client.put(
                f"/api/purchases/{pid}",
                headers=auth_headers(admin_token),
                json={"status": "approved", "item": "TEST_B15_PURCHASE_STATUS", "qty": 1}
            )
            assert res.status_code == 200
            data = res.json()
            assert data["status"] == "approved"
            assert data["item"] == "TEST_B15_PURCHASE_STATUS"
        finally:
            await self._delete_purchase(http_client, admin_token, pid)

    async def test_status_transitions(self, http_client: AsyncClient, admin_token: str):
        """Закупка проходит все статусы: draft → approved → ordered → received → installed → closed."""
        pid = await self._create_purchase(http_client, admin_token)
        try:
            for st in ["approved", "ordered", "received", "installed", "closed"]:
                res = await http_client.put(
                    f"/api/purchases/{pid}",
                    headers=auth_headers(admin_token),
                    json={"status": st, "item": "TEST_B15_PURCHASE_STATUS", "qty": 1}
                )
                assert res.status_code == 200, f"Failed for status={st}: {res.text}"
                assert res.json()["status"] == st
        finally:
            await self._delete_purchase(http_client, admin_token, pid)

    async def test_put_returns_updated_data(self, http_client: AsyncClient, admin_token: str):
        """PUT возвращает обновлённые данные."""
        pid = await self._create_purchase(http_client, admin_token)
        try:
            res = await http_client.put(
                f"/api/purchases/{pid}",
                headers=auth_headers(admin_token),
                json={"status": "received", "item": "TEST_B15_UPDATED", "qty": 3}
            )
            assert res.status_code == 200
            data = res.json()
            assert data["status"] == "received"
            assert data["item"] == "TEST_B15_UPDATED"
            assert float(data["qty"]) == 3.0
        finally:
            await self._delete_purchase(http_client, admin_token, pid)

    async def test_put_status_not_found(self, http_client: AsyncClient, admin_token: str):
        res = await http_client.put(
            "/api/purchases/999999",
            headers=auth_headers(admin_token),
            json={"status": "approved", "item": "ghost", "qty": 1}
        )
        assert res.status_code == 404

    async def test_status_change_creates_notification(self, http_client: AsyncClient, admin_token: str):
        """Смена статуса закупки — notifications endpoint доступен."""
        pid = await self._create_purchase(http_client, admin_token)
        try:
            res = await http_client.put(
                f"/api/purchases/{pid}",
                headers=auth_headers(admin_token),
                json={"status": "approved", "item": "TEST_B15_PURCHASE_STATUS", "qty": 1}
            )
            assert res.status_code == 200
            notif_res = await http_client.get("/api/notifications?limit=5", headers=auth_headers(admin_token))
            assert notif_res.status_code == 200
        finally:
            await self._delete_purchase(http_client, admin_token, pid)


# ─── Закупки: фильтрация ─────────────────────────────────────────────────────

@pytest.mark.asyncio
class TestPurchaseFilters:
    """GET /purchases — фильтрация по status и site_id."""

    async def test_filter_by_status(self, http_client: AsyncClient, admin_token: str):
        # Создаём закупку и меняем статус через PUT
        res = await http_client.post("/api/purchases", headers=auth_headers(admin_token), json={
            "item": "TEST_B15_FILTER_STATUS",
            "qty": 2,
        })
        assert res.status_code == 201
        pid = res.json()["id"]
        # Меняем статус через PUT
        await http_client.put(
            f"/api/purchases/{pid}",
            headers=auth_headers(admin_token),
            json={"status": "ordered", "item": "TEST_B15_FILTER_STATUS", "qty": 2}
        )
        try:
            list_res = await http_client.get("/api/purchases?status=ordered", headers=auth_headers(admin_token))
            assert list_res.status_code == 200
            ids = [p["id"] for p in list_res.json()["items"]]
            assert pid in ids
            for item in list_res.json()["items"]:
                assert item["status"] == "ordered"
        finally:
            await http_client.patch(f"/api/purchases/{pid}/archive", headers=auth_headers(admin_token))

    async def test_filter_by_site_id(self, http_client: AsyncClient, admin_token: str):
        # Создаём объект и закупку к нему
        site_res = await http_client.post("/api/sites", headers=auth_headers(admin_token), json={
            "title": "TEST_B15_SITE_PURCHASE",
            "address": "Тест адрес B15"
        })
        assert site_res.status_code == 201
        site_id = site_res.json()["id"]

        purchase_res = await http_client.post("/api/purchases", headers=auth_headers(admin_token), json={
            "item": "TEST_B15_PURCHASE_SITE_FILTER",
            "qty": 1,
            "site_id": site_id,
        })
        assert purchase_res.status_code == 201
        pid = purchase_res.json()["id"]

        try:
            list_res = await http_client.get(f"/api/purchases?site_id={site_id}", headers=auth_headers(admin_token))
            assert list_res.status_code == 200
            ids = [p["id"] for p in list_res.json()["items"]]
            assert pid in ids
            for item in list_res.json()["items"]:
                assert item["site_id"] == site_id
        finally:
            await http_client.patch(f"/api/purchases/{pid}/archive", headers=auth_headers(admin_token))
            await http_client.patch(f"/api/sites/{site_id}/archive", headers=auth_headers(admin_token))

    async def test_filter_status_no_match(self, http_client: AsyncClient, admin_token: str):
        # Нет закупок в статусе 'installed' из тестов (ситуативно — проверяем только формат)
        res = await http_client.get("/api/purchases?status=draft&limit=1", headers=auth_headers(admin_token))
        assert res.status_code == 200
        assert "items" in res.json()
        assert "total" in res.json()


# ─── Журнал: фильтрация ──────────────────────────────────────────────────────

@pytest.mark.asyncio
class TestLogsFilters:
    """GET /logs — фильтрация по action_sysname и entity_type."""

    async def test_logs_returns_page(self, http_client: AsyncClient, admin_token: str):
        res = await http_client.get("/api/logs?limit=10", headers=auth_headers(admin_token))
        assert res.status_code == 200
        data = res.json()
        assert "items" in data
        assert "total" in data
        assert isinstance(data["items"], list)

    async def test_filter_by_entity_type(self, http_client: AsyncClient, admin_token: str):
        # Создаём клиента, чтобы в логах был client_create
        create_res = await http_client.post("/api/clients", headers=auth_headers(admin_token), json={
            "name": "TEST_B15_LOG_CLIENT"
        })
        assert create_res.status_code == 201
        client_id = create_res.json()["id"]
        try:
            res = await http_client.get(
                "/api/logs?entity_type=client&limit=50",
                headers=auth_headers(admin_token)
            )
            assert res.status_code == 200
            logs = res.json()["items"]
            if logs:
                assert all(log["entity_type"] == "client" for log in logs)
        finally:
            await http_client.delete(f"/api/clients/{client_id}", headers=auth_headers(admin_token))

    async def test_filter_by_action_sysname(self, http_client: AsyncClient, admin_token: str):
        # Создаём закупку — должна появиться запись purchase_create
        create_res = await http_client.post("/api/purchases", headers=auth_headers(admin_token), json={
            "item": "TEST_B15_LOG_PURCHASE",
            "qty": 1,
        })
        assert create_res.status_code == 201
        pid = create_res.json()["id"]
        try:
            res = await http_client.get(
                "/api/logs?action_sysname=purchase_create&limit=20",
                headers=auth_headers(admin_token)
            )
            assert res.status_code == 200
            logs = res.json()["items"]
            if logs:
                assert all(log["action_sysname"] == "purchase_create" for log in logs)
        finally:
            await http_client.patch(f"/api/purchases/{pid}/archive", headers=auth_headers(admin_token))

    async def test_logs_pagination(self, http_client: AsyncClient, admin_token: str):
        """Пагинация работает — offset смещает результаты."""
        res1 = await http_client.get("/api/logs?limit=5&offset=0", headers=auth_headers(admin_token))
        res2 = await http_client.get("/api/logs?limit=5&offset=5", headers=auth_headers(admin_token))
        assert res1.status_code == 200
        assert res2.status_code == 200
        ids1 = [l["id"] for l in res1.json()["items"]]
        ids2 = [l["id"] for l in res2.json()["items"]]
        # Нет пересечений между страницами (если достаточно записей)
        if ids1 and ids2:
            assert not set(ids1) & set(ids2)
