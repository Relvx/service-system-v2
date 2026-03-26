"""
Тесты блока 14 — Гриды: фильтрация клиентов / объектов / договоров.

Проверяем:
- Счётчики sites_count/visits_count/contracts_count в /clients
- Счётчик sites_count в /contracts
- Фильтры search, active_only, show_archived для /clients
- Фильтры search для /sites и /contracts
- Фильтр status для /contracts
"""

import pytest
from httpx import AsyncClient
from tests.conftest import auth_headers


@pytest.mark.asyncio
class TestClientCounters:
    """ClientOut содержит корректные счётчики."""

    async def test_clients_have_counter_fields(self, http_client: AsyncClient, admin_token: str):
        res = await http_client.get("/api/clients?limit=5", headers=auth_headers(admin_token))
        assert res.status_code == 200
        items = res.json()["items"]
        if items:
            item = items[0]
            assert "sites_count" in item
            assert "visits_count" in item
            assert "contracts_count" in item
            assert isinstance(item["sites_count"], int)
            assert isinstance(item["visits_count"], int)
            assert isinstance(item["contracts_count"], int)

    async def test_clients_counters_are_non_negative(self, http_client: AsyncClient, admin_token: str):
        res = await http_client.get("/api/clients?limit=20", headers=auth_headers(admin_token))
        assert res.status_code == 200
        for item in res.json()["items"]:
            assert item["sites_count"] >= 0
            assert item["visits_count"] >= 0
            assert item["contracts_count"] >= 0

    async def test_client_create_has_zero_counters(self, http_client: AsyncClient, admin_token: str):
        """Новый клиент имеет нулевые счётчики."""
        # Создаём тестового клиента
        create_res = await http_client.post("/api/clients", headers=auth_headers(admin_token), json={
            "name": "TEST_BLOCK14_CLIENT_COUNTERS"
        })
        assert create_res.status_code == 201
        client_id = create_res.json()["id"]

        try:
            res = await http_client.get("/api/clients?search=TEST_BLOCK14_CLIENT_COUNTERS", headers=auth_headers(admin_token))
            assert res.status_code == 200
            items = res.json()["items"]
            assert len(items) >= 1
            found = next((c for c in items if c["id"] == client_id), None)
            assert found is not None
            assert found["sites_count"] == 0
            assert found["visits_count"] == 0
            assert found["contracts_count"] == 0
        finally:
            await http_client.delete(f"/api/clients/{client_id}", headers=auth_headers(admin_token))


@pytest.mark.asyncio
class TestClientFilters:
    """Фильтры в /api/clients работают корректно."""

    async def test_search_by_name(self, http_client: AsyncClient, admin_token: str):
        """Поиск по имени возвращает только совпадения."""
        # Создаём клиента с уникальным именем
        create_res = await http_client.post("/api/clients", headers=auth_headers(admin_token), json={
            "name": "ZZZTEST_UNIQUE_SEARCH_NAME_B14"
        })
        assert create_res.status_code == 201
        client_id = create_res.json()["id"]
        try:
            res = await http_client.get("/api/clients?search=ZZZTEST_UNIQUE_SEARCH", headers=auth_headers(admin_token))
            assert res.status_code == 200
            items = res.json()["items"]
            assert any(c["id"] == client_id for c in items)
        finally:
            await http_client.delete(f"/api/clients/{client_id}", headers=auth_headers(admin_token))

    async def test_search_no_match(self, http_client: AsyncClient, admin_token: str):
        res = await http_client.get("/api/clients?search=XXXXNOMATCH_B14ZZZZ", headers=auth_headers(admin_token))
        assert res.status_code == 200
        assert res.json()["items"] == []
        assert res.json()["total"] == 0

    async def test_show_archived_false_excludes_archived(self, http_client: AsyncClient, admin_token: str):
        """show_archived=false (по умолчанию) не показывает архивные."""
        # Создаём клиента и архивируем его
        create_res = await http_client.post("/api/clients", headers=auth_headers(admin_token), json={
            "name": "TEST_BLOCK14_ARCHIVE_FILTER"
        })
        assert create_res.status_code == 201
        client_id = create_res.json()["id"]
        await http_client.patch(f"/api/clients/{client_id}/archive", headers=auth_headers(admin_token))
        try:
            # По умолчанию архивные скрыты
            res = await http_client.get("/api/clients?search=TEST_BLOCK14_ARCHIVE_FILTER", headers=auth_headers(admin_token))
            assert res.status_code == 200
            ids = [c["id"] for c in res.json()["items"]]
            assert client_id not in ids

            # С show_archived=true — виден
            res2 = await http_client.get(
                "/api/clients?search=TEST_BLOCK14_ARCHIVE_FILTER&show_archived=true",
                headers=auth_headers(admin_token)
            )
            assert res2.status_code == 200
            ids2 = [c["id"] for c in res2.json()["items"]]
            assert client_id in ids2
        finally:
            await http_client.delete(f"/api/clients/{client_id}", headers=auth_headers(admin_token))


@pytest.mark.asyncio
class TestContractCounters:
    """ContractOut содержит sites_count."""

    async def test_contracts_have_sites_count(self, http_client: AsyncClient, admin_token: str):
        res = await http_client.get("/api/contracts?limit=5", headers=auth_headers(admin_token))
        assert res.status_code == 200
        items = res.json()["items"]
        if items:
            assert "sites_count" in items[0]
            assert isinstance(items[0]["sites_count"], int)
            assert items[0]["sites_count"] >= 0

    async def test_contract_sites_count_matches_detail(self, http_client: AsyncClient, admin_token: str):
        """sites_count в списке совпадает с количеством объектов в детальной карточке."""
        # Создаём тестовый договор
        create_res = await http_client.post("/api/contracts", headers=auth_headers(admin_token), json={
            "contract_number": "TEST-B14-SITESCNT"
        })
        assert create_res.status_code == 201
        contract_id = create_res.json()["id"]
        try:
            # Смотрим в списке
            list_res = await http_client.get(f"/api/contracts?search=TEST-B14-SITESCNT", headers=auth_headers(admin_token))
            assert list_res.status_code == 200
            found = next((c for c in list_res.json()["items"] if c["id"] == contract_id), None)
            assert found is not None
            assert found["sites_count"] == 0

            # Смотрим в деталях
            detail_res = await http_client.get(f"/api/contracts/{contract_id}", headers=auth_headers(admin_token))
            assert detail_res.status_code == 200
            assert len(detail_res.json()["sites"]) == 0
        finally:
            await http_client.patch(
                f"/api/contracts/{contract_id}",
                headers=auth_headers(admin_token),
                json={"is_archived": True}
            )


@pytest.mark.asyncio
class TestContractFilters:
    """Фильтры /api/contracts работают корректно."""

    async def test_search_by_contract_number(self, http_client: AsyncClient, admin_token: str):
        create_res = await http_client.post("/api/contracts", headers=auth_headers(admin_token), json={
            "contract_number": "ZZZTEST_UNIQUE_NUMBER_B14"
        })
        assert create_res.status_code == 201
        contract_id = create_res.json()["id"]
        try:
            res = await http_client.get(
                "/api/contracts?search=ZZZTEST_UNIQUE_NUMBER_B14",
                headers=auth_headers(admin_token)
            )
            assert res.status_code == 200
            ids = [c["id"] for c in res.json()["items"]]
            assert contract_id in ids
        finally:
            await http_client.patch(
                f"/api/contracts/{contract_id}",
                headers=auth_headers(admin_token),
                json={"is_archived": True}
            )

    async def test_filter_by_status_active(self, http_client: AsyncClient, admin_token: str):
        res = await http_client.get("/api/contracts?status=active&limit=10", headers=auth_headers(admin_token))
        assert res.status_code == 200
        for item in res.json()["items"]:
            assert item["status"] == "active"

    async def test_filter_by_status_closed(self, http_client: AsyncClient, admin_token: str):
        # Создаём договор, закрываем его
        create_res = await http_client.post("/api/contracts", headers=auth_headers(admin_token), json={
            "contract_number": "TEST-B14-CLOSED"
        })
        assert create_res.status_code == 201
        contract_id = create_res.json()["id"]
        await http_client.patch(
            f"/api/contracts/{contract_id}",
            headers=auth_headers(admin_token),
            json={"status": "closed"}
        )
        try:
            res = await http_client.get("/api/contracts?status=closed", headers=auth_headers(admin_token))
            assert res.status_code == 200
            ids = [c["id"] for c in res.json()["items"]]
            assert contract_id in ids
            for item in res.json()["items"]:
                assert item["status"] == "closed"
        finally:
            await http_client.patch(
                f"/api/contracts/{contract_id}",
                headers=auth_headers(admin_token),
                json={"is_archived": True}
            )

    async def test_search_no_match(self, http_client: AsyncClient, admin_token: str):
        res = await http_client.get("/api/contracts?search=XXXXNOMATCH_B14ZZZZ", headers=auth_headers(admin_token))
        assert res.status_code == 200
        assert res.json()["items"] == []


@pytest.mark.asyncio
class TestSiteFilters:
    """Фильтры /api/sites работают корректно."""

    async def test_search_by_title(self, http_client: AsyncClient, admin_token: str):
        # Создаём объект с уникальным названием
        create_res = await http_client.post("/api/sites", headers=auth_headers(admin_token), json={
            "title": "ZZZTEST_UNIQUE_TITLE_B14",
            "address": "Тестовый адрес B14"
        })
        assert create_res.status_code == 201
        site_id = create_res.json()["id"]
        try:
            res = await http_client.get(
                "/api/sites?search=ZZZTEST_UNIQUE_TITLE_B14",
                headers=auth_headers(admin_token)
            )
            assert res.status_code == 200
            ids = [s["id"] for s in res.json()["items"]]
            assert site_id in ids
        finally:
            await http_client.patch(f"/api/sites/{site_id}/archive", headers=auth_headers(admin_token))

    async def test_search_no_match(self, http_client: AsyncClient, admin_token: str):
        res = await http_client.get("/api/sites?search=XXXXNOMATCH_B14ZZZZ", headers=auth_headers(admin_token))
        assert res.status_code == 200
        assert res.json()["items"] == []

    async def test_show_archived_false_excludes_archived(self, http_client: AsyncClient, admin_token: str):
        create_res = await http_client.post("/api/sites", headers=auth_headers(admin_token), json={
            "title": "TEST_BLOCK14_SITE_ARCHIVE",
            "address": "Тест архив B14"
        })
        assert create_res.status_code == 201
        site_id = create_res.json()["id"]
        await http_client.patch(f"/api/sites/{site_id}/archive", headers=auth_headers(admin_token))
        try:
            res = await http_client.get(
                "/api/sites?search=TEST_BLOCK14_SITE_ARCHIVE",
                headers=auth_headers(admin_token)
            )
            assert res.status_code == 200
            ids = [s["id"] for s in res.json()["items"]]
            assert site_id not in ids

            res2 = await http_client.get(
                "/api/sites?search=TEST_BLOCK14_SITE_ARCHIVE&show_archived=true",
                headers=auth_headers(admin_token)
            )
            assert res2.status_code == 200
            ids2 = [s["id"] for s in res2.json()["items"]]
            assert site_id in ids2
        finally:
            pass  # уже заархивирован

    async def test_sites_have_client_name_field(self, http_client: AsyncClient, admin_token: str):
        """SiteOut содержит client_name."""
        res = await http_client.get("/api/sites?limit=5", headers=auth_headers(admin_token))
        assert res.status_code == 200
        items = res.json()["items"]
        if items:
            assert "client_name" in items[0]
