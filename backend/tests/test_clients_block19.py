"""
Block 19 — Баги клиентов.

Тесты покрывают:
1. show_archived=true возвращает ТОЛЬКО архивных клиентов
2. inactive_only=true возвращает только неактивных
3. Архивированный клиент доступен по GET /clients/{id}
4. Переключение is_active через PUT /clients/{id}
"""
import pytest
from httpx import AsyncClient
from tests.conftest import auth_headers


@pytest.mark.asyncio
class TestShowArchivedFilter:
    """show_archived=true должен возвращать ТОЛЬКО архивных."""

    async def test_show_archived_returns_only_archived(
        self, http_client: AsyncClient, admin_token: str
    ):
        headers = auth_headers(admin_token)

        # Создаём двух клиентов
        r1 = await http_client.post("/api/clients", headers=headers, json={"name": "B19_ACTIVE_CLIENT"})
        assert r1.status_code == 201
        active_id = r1.json()["id"]

        r2 = await http_client.post("/api/clients", headers=headers, json={"name": "B19_ARCHIVED_CLIENT"})
        assert r2.status_code == 201
        archived_id = r2.json()["id"]

        # Архивируем второго
        await http_client.patch(f"/api/clients/{archived_id}/archive", headers=headers)

        try:
            # show_archived=true — должны прийти только архивные
            res = await http_client.get(
                "/api/clients?show_archived=true&search=B19_ARCHIVED_CLIENT&limit=50",
                headers=headers,
            )
            assert res.status_code == 200
            ids = [c["id"] for c in res.json()["items"]]
            assert archived_id in ids
            assert active_id not in ids
            # Все клиенты в ответе должны быть архивными
            for c in res.json()["items"]:
                assert c["is_archived"] is True

        finally:
            await http_client.delete(f"/api/clients/{active_id}", headers=headers)
            await http_client.delete(f"/api/clients/{archived_id}", headers=headers)

    async def test_show_archived_false_excludes_archived(
        self, http_client: AsyncClient, admin_token: str
    ):
        headers = auth_headers(admin_token)

        r = await http_client.post("/api/clients", headers=headers, json={"name": "B19_TO_ARCHIVE"})
        assert r.status_code == 201
        cid = r.json()["id"]
        await http_client.patch(f"/api/clients/{cid}/archive", headers=headers)

        try:
            res = await http_client.get("/api/clients?search=B19_TO_ARCHIVE&limit=50", headers=headers)
            assert res.status_code == 200
            ids = [c["id"] for c in res.json()["items"]]
            assert cid not in ids
        finally:
            await http_client.delete(f"/api/clients/{cid}", headers=headers)


@pytest.mark.asyncio
class TestInactiveOnlyFilter:
    """inactive_only=true возвращает только неактивных (не архивных)."""

    async def test_inactive_only_returns_inactive(
        self, http_client: AsyncClient, admin_token: str
    ):
        headers = auth_headers(admin_token)

        # Создаём активного и деактивируем его
        r = await http_client.post("/api/clients", headers=headers, json={"name": "B19_INACTIVE_CLIENT"})
        assert r.status_code == 201
        cid = r.json()["id"]

        # Деактивируем через PUT
        upd = await http_client.put(f"/api/clients/{cid}", headers=headers, json={
            "name": "B19_INACTIVE_CLIENT", "is_active": False
        })
        assert upd.status_code == 200
        assert upd.json()["is_active"] is False

        try:
            res = await http_client.get(
                "/api/clients?inactive_only=true&search=B19_INACTIVE_CLIENT&limit=50",
                headers=headers,
            )
            assert res.status_code == 200
            ids = [c["id"] for c in res.json()["items"]]
            assert cid in ids
            for c in res.json()["items"]:
                assert c["is_active"] is False
                assert c["is_archived"] is False
        finally:
            await http_client.delete(f"/api/clients/{cid}", headers=headers)


@pytest.mark.asyncio
class TestArchivedClientAccess:
    """Архивированный клиент доступен по GET /clients/{id}."""

    async def test_get_archived_client_by_id(
        self, http_client: AsyncClient, admin_token: str
    ):
        headers = auth_headers(admin_token)

        r = await http_client.post("/api/clients", headers=headers, json={"name": "B19_ARCHIVE_ACCESS"})
        assert r.status_code == 201
        cid = r.json()["id"]
        await http_client.patch(f"/api/clients/{cid}/archive", headers=headers)

        try:
            res = await http_client.get(f"/api/clients/{cid}", headers=headers)
            assert res.status_code == 200
            assert res.json()["is_archived"] is True
        finally:
            await http_client.delete(f"/api/clients/{cid}", headers=headers)


@pytest.mark.asyncio
class TestToggleActive:
    """Переключение is_active через PUT /clients/{id}."""

    async def test_deactivate_client(self, http_client: AsyncClient, admin_token: str):
        headers = auth_headers(admin_token)

        r = await http_client.post("/api/clients", headers=headers, json={"name": "B19_TOGGLE_ACTIVE"})
        assert r.status_code == 201
        cid = r.json()["id"]
        assert r.json()["is_active"] is True

        try:
            upd = await http_client.put(f"/api/clients/{cid}", headers=headers, json={
                "name": "B19_TOGGLE_ACTIVE", "is_active": False
            })
            assert upd.status_code == 200
            assert upd.json()["is_active"] is False
        finally:
            await http_client.delete(f"/api/clients/{cid}", headers=headers)

    async def test_activate_client(self, http_client: AsyncClient, admin_token: str):
        headers = auth_headers(admin_token)

        r = await http_client.post("/api/clients", headers=headers, json={"name": "B19_ACTIVATE"})
        assert r.status_code == 201
        cid = r.json()["id"]

        # Сначала деактивируем
        await http_client.put(f"/api/clients/{cid}", headers=headers, json={
            "name": "B19_ACTIVATE", "is_active": False
        })

        try:
            upd = await http_client.put(f"/api/clients/{cid}", headers=headers, json={
                "name": "B19_ACTIVATE", "is_active": True
            })
            assert upd.status_code == 200
            assert upd.json()["is_active"] is True
        finally:
            await http_client.delete(f"/api/clients/{cid}", headers=headers)
