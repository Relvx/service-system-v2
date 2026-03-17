"""
Тесты для эндпоинтов договоров (блок 11).

GET    /api/contracts                    — список договоров
GET    /api/contracts/{id}              — карточка договора
POST   /api/contracts                    — создать договор
PATCH  /api/contracts/{id}              — обновить договор
POST   /api/contracts/{id}/sites/{sid}  — привязать объект
DELETE /api/contracts/{id}/sites/{sid}  — отвязать объект
GET    /api/contracts/by-client/{cid}   — договоры клиента
"""

import pytest
from httpx import AsyncClient

from tests.conftest import auth_headers

CONTRACT_PAYLOAD = {
    "contract_number": "__test__ ДГ-001/2024",
    "contract_date": "2024-01-15",
    "subject": "ТО газового оборудования",
    "amount": "75000.00",
    "status": "active",
    "notes": "Тестовый договор",
}


async def _create_client(http_client, headers):
    res = await http_client.post("/api/clients", headers=headers, json={
        "name": "__test__ Клиент для договора"
    })
    assert res.status_code == 201
    return res.json()["id"]


async def _create_site(http_client, headers, client_id):
    res = await http_client.post("/api/sites", headers=headers, json={
        "title": "__test__ Объект для договора",
        "address": "г. Тест, ул. Тестовая, д. 1",
        "client_id": client_id,
    })
    assert res.status_code == 201
    return res.json()["id"]


async def _create_contract(http_client, headers, client_id=None):
    payload = {**CONTRACT_PAYLOAD}
    if client_id:
        payload["client_id"] = client_id
    res = await http_client.post("/api/contracts", headers=headers, json=payload)
    assert res.status_code == 201
    return res.json()["id"]


class TestContractsList:
    async def test_list_returns_list(self, http_client: AsyncClient, admin_token: str):
        """GET /contracts возвращает список."""
        res = await http_client.get("/api/contracts", headers=auth_headers(admin_token))
        assert res.status_code == 200
        assert isinstance(res.json(), list)

    async def test_list_unauthenticated(self, http_client: AsyncClient):
        """Без токена → 401."""
        res = await http_client.get("/api/contracts")
        assert res.status_code == 401


class TestContractCRUD:
    async def test_create_returns_201(self, http_client: AsyncClient, admin_token: str):
        """POST создаёт договор и возвращает 201."""
        headers = auth_headers(admin_token)
        contract_id = await _create_contract(http_client, headers)
        data = (await http_client.get(f"/api/contracts/{contract_id}", headers=headers)).json()
        assert data["contract_number"] == CONTRACT_PAYLOAD["contract_number"]
        assert data["status"] == "active"

    async def test_create_with_client(self, http_client: AsyncClient, admin_token: str):
        """Создание договора с привязкой к клиенту."""
        headers = auth_headers(admin_token)
        client_id = await _create_client(http_client, headers)
        contract_id = await _create_contract(http_client, headers, client_id)

        res = await http_client.get(f"/api/contracts/{contract_id}", headers=headers)
        assert res.status_code == 200
        data = res.json()
        assert data["client_id"] == client_id
        assert data["client_name"] == "__test__ Клиент для договора"

        await http_client.delete(f"/api/clients/{client_id}", headers=headers)

    async def test_get_not_found(self, http_client: AsyncClient, admin_token: str):
        """GET несуществующего ID → 404."""
        res = await http_client.get("/api/contracts/999999", headers=auth_headers(admin_token))
        assert res.status_code == 404

    async def test_update_contract(self, http_client: AsyncClient, admin_token: str):
        """PATCH обновляет поля договора."""
        headers = auth_headers(admin_token)
        contract_id = await _create_contract(http_client, headers)

        res = await http_client.patch(
            f"/api/contracts/{contract_id}",
            headers=headers,
            json={"status": "closed", "notes": "Завершён"},
        )
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "closed"
        assert data["notes"] == "Завершён"

    async def test_filter_by_status(self, http_client: AsyncClient, admin_token: str):
        """Фильтр по статусу работает."""
        headers = auth_headers(admin_token)
        contract_id = await _create_contract(http_client, headers)
        await http_client.patch(f"/api/contracts/{contract_id}", headers=headers, json={"status": "cancelled"})

        res = await http_client.get("/api/contracts?status=cancelled", headers=headers)
        assert res.status_code == 200
        ids = [c["id"] for c in res.json()]
        assert contract_id in ids

    async def test_search_by_number(self, http_client: AsyncClient, admin_token: str):
        """Поиск по номеру договора."""
        headers = auth_headers(admin_token)
        await _create_contract(http_client, headers)

        res = await http_client.get("/api/contracts?search=__test__", headers=headers)
        assert res.status_code == 200
        assert len(res.json()) >= 1


class TestContractSiteLinks:
    async def test_add_and_remove_site(self, http_client: AsyncClient, admin_token: str):
        """Привязка объекта к договору и отвязка."""
        headers = auth_headers(admin_token)
        client_id = await _create_client(http_client, headers)
        site_id = await _create_site(http_client, headers, client_id)
        contract_id = await _create_contract(http_client, headers, client_id)

        # привязать объект
        res = await http_client.post(
            f"/api/contracts/{contract_id}/sites/{site_id}", headers=headers
        )
        assert res.status_code == 201

        # в карточке договора объект виден
        detail = (await http_client.get(f"/api/contracts/{contract_id}", headers=headers)).json()
        site_ids = [s["id"] for s in detail["sites"]]
        assert site_id in site_ids

        # отвязать объект
        res = await http_client.delete(
            f"/api/contracts/{contract_id}/sites/{site_id}", headers=headers
        )
        assert res.status_code == 200

        # объект больше не в договоре
        detail = (await http_client.get(f"/api/contracts/{contract_id}", headers=headers)).json()
        site_ids = [s["id"] for s in detail["sites"]]
        assert site_id not in site_ids

        await http_client.delete(f"/api/clients/{client_id}", headers=headers)

    async def test_duplicate_link_returns_409(self, http_client: AsyncClient, admin_token: str):
        """Повторная привязка того же объекта → 409."""
        headers = auth_headers(admin_token)
        client_id = await _create_client(http_client, headers)
        site_id = await _create_site(http_client, headers, client_id)
        contract_id = await _create_contract(http_client, headers, client_id)

        await http_client.post(f"/api/contracts/{contract_id}/sites/{site_id}", headers=headers)
        res = await http_client.post(
            f"/api/contracts/{contract_id}/sites/{site_id}", headers=headers
        )
        assert res.status_code == 409

        await http_client.delete(f"/api/clients/{client_id}", headers=headers)

    async def test_add_nonexistent_site_returns_404(self, http_client: AsyncClient, admin_token: str):
        """Привязка несуществующего объекта → 404."""
        headers = auth_headers(admin_token)
        contract_id = await _create_contract(http_client, headers)
        res = await http_client.post(
            f"/api/contracts/{contract_id}/sites/999999", headers=headers
        )
        assert res.status_code == 404


class TestContractsByClient:
    async def test_get_by_client(self, http_client: AsyncClient, admin_token: str):
        """GET /by-client/{id} возвращает договоры клиента."""
        headers = auth_headers(admin_token)
        client_id = await _create_client(http_client, headers)
        contract_id = await _create_contract(http_client, headers, client_id)

        res = await http_client.get(f"/api/contracts/by-client/{client_id}", headers=headers)
        assert res.status_code == 200
        ids = [c["id"] for c in res.json()]
        assert contract_id in ids

        await http_client.delete(f"/api/clients/{client_id}", headers=headers)

    async def test_get_by_client_empty(self, http_client: AsyncClient, admin_token: str):
        """Клиент без договоров возвращает пустой список."""
        headers = auth_headers(admin_token)
        client_id = await _create_client(http_client, headers)

        res = await http_client.get(f"/api/contracts/by-client/{client_id}", headers=headers)
        assert res.status_code == 200
        assert res.json() == []

        await http_client.delete(f"/api/clients/{client_id}", headers=headers)

    async def test_sites_count_in_by_client(self, http_client: AsyncClient, admin_token: str):
        """sites_count отражает количество привязанных объектов."""
        headers = auth_headers(admin_token)
        client_id = await _create_client(http_client, headers)
        site_id = await _create_site(http_client, headers, client_id)
        contract_id = await _create_contract(http_client, headers, client_id)

        await http_client.post(f"/api/contracts/{contract_id}/sites/{site_id}", headers=headers)

        res = await http_client.get(f"/api/contracts/by-client/{client_id}", headers=headers)
        contracts = res.json()
        c = next(x for x in contracts if x["id"] == contract_id)
        assert c["sites_count"] == 1

        await http_client.delete(f"/api/clients/{client_id}", headers=headers)
