"""
Тесты эндпоинтов справочников (config).

GET /api/config/visit-statuses
GET /api/config/visit-types
GET /api/config/priorities
GET /api/config/defect-statuses
GET /api/config/defect-action-types
GET /api/config/attachment-kinds
GET /api/config/purchase-statuses
GET /api/config/service-frequencies
GET /api/config/entity-types
POST/PUT/DELETE /api/config/{resource}/{sysname}  — только admin
"""

import pytest
from httpx import AsyncClient
from tests.conftest import auth_headers

CONFIG_ENDPOINTS = [
    "/api/config/visit-statuses",
    "/api/config/visit-types",
    "/api/config/priorities",
    "/api/config/defect-statuses",
    "/api/config/defect-action-types",
    "/api/config/attachment-kinds",
    "/api/config/purchase-statuses",
    "/api/config/service-frequencies",
    "/api/config/entity-types",
]


class TestConfigRead:
    @pytest.mark.parametrize("endpoint", CONFIG_ENDPOINTS)
    async def test_authenticated_gets_list(self, http_client: AsyncClient,
                                           admin_token: str, endpoint: str):
        """Каждый GET-эндпоинт конфига возвращает непустой список для авторизованного."""
        res = await http_client.get(endpoint, headers=auth_headers(admin_token))
        assert res.status_code == 200
        data = res.json()
        assert isinstance(data, list)
        assert len(data) > 0  # seed данные должны быть

    @pytest.mark.parametrize("endpoint", CONFIG_ENDPOINTS)
    async def test_unauthenticated_forbidden(self, http_client: AsyncClient, endpoint: str):
        """Без токена → 401."""
        res = await http_client.get(endpoint)
        assert res.status_code == 401

    async def test_visit_statuses_have_sysname(self, http_client: AsyncClient, admin_token: str):
        """Статусы выездов содержат sysname и display_name."""
        res = await http_client.get("/api/config/visit-statuses",
                                    headers=auth_headers(admin_token))
        for item in res.json():
            assert "sysname" in item
            assert "display_name" in item

    async def test_entity_types_contain_all_entities(self, http_client: AsyncClient, admin_token: str):
        """entity-types содержит все 5 типов документов."""
        res = await http_client.get("/api/config/entity-types",
                                    headers=auth_headers(admin_token))
        sysnames = {item["sysname"] for item in res.json()}
        assert {"client", "site", "visit", "defect", "purchase"}.issubset(sysnames)

    async def test_entity_types_have_plural(self, http_client: AsyncClient, admin_token: str):
        """entity-types содержит display_name_plural."""
        res = await http_client.get("/api/config/entity-types",
                                    headers=auth_headers(admin_token))
        for item in res.json():
            assert "display_name_plural" in item
            assert item["display_name_plural"]


class TestConfigAdminCRUD:
    async def test_create_config_item(self, http_client: AsyncClient, admin_token: str):
        """Admin может создать новый элемент справочника."""
        headers = auth_headers(admin_token)
        payload = {"sysname": "__test_status", "display_name": "Тестовый статус"}

        res = await http_client.post("/api/config/visit-statuses", headers=headers, json=payload)
        assert res.status_code == 201
        assert res.json()["sysname"] == "__test_status"

        # cleanup
        await http_client.delete("/api/config/visit-statuses/__test_status", headers=headers)

    async def test_create_duplicate_sysname(self, http_client: AsyncClient, admin_token: str):
        """Дублирующийся sysname → 409."""
        headers = auth_headers(admin_token)
        res = await http_client.post("/api/config/visit-statuses", headers=headers,
                                      json={"sysname": "planned", "display_name": "Дубль"})
        assert res.status_code == 409

    async def test_update_config_item(self, http_client: AsyncClient, admin_token: str):
        """Admin может обновить display_name."""
        headers = auth_headers(admin_token)

        await http_client.post("/api/config/visit-statuses", headers=headers,
                                json={"sysname": "__test_upd", "display_name": "Оригинал"})

        upd = await http_client.put("/api/config/visit-statuses/__test_upd", headers=headers,
                                     json={"display_name": "Обновлённый"})
        assert upd.status_code == 200
        assert upd.json()["display_name"] == "Обновлённый"

        await http_client.delete("/api/config/visit-statuses/__test_upd", headers=headers)

    async def test_office_cannot_create(self, http_client: AsyncClient, office_token: str):
        """Офис не может создавать элементы справочника."""
        res = await http_client.post("/api/config/visit-statuses",
                                      headers=auth_headers(office_token),
                                      json={"sysname": "__test_office", "display_name": "X"})
        assert res.status_code == 403
