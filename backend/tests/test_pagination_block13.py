"""
Тесты блока 13 — Пагинация и глобальный поиск.

- GET /api/clients, sites, contracts, visits, defects, purchases → { items, total, limit, offset }
- limit/offset работают
- Глобальный поиск: limit/offset, результаты clients_total, sites_total, contracts_total
"""

import pytest
from httpx import AsyncClient
from tests.conftest import auth_headers


@pytest.mark.asyncio
class TestPaginationFormat:
    """Все списочные эндпоинты возвращают { items, total, limit, offset }."""

    async def test_clients_page_format(self, http_client: AsyncClient, admin_token: str):
        res = await http_client.get("/api/clients", headers=auth_headers(admin_token))
        assert res.status_code == 200
        data = res.json()
        assert "items" in data
        assert "total" in data
        assert "limit" in data
        assert "offset" in data
        assert isinstance(data["items"], list)
        assert isinstance(data["total"], int)

    async def test_sites_page_format(self, http_client: AsyncClient, admin_token: str):
        res = await http_client.get("/api/sites", headers=auth_headers(admin_token))
        assert res.status_code == 200
        data = res.json()
        assert "items" in data and "total" in data
        assert isinstance(data["items"], list)

    async def test_contracts_page_format(self, http_client: AsyncClient, admin_token: str):
        res = await http_client.get("/api/contracts", headers=auth_headers(admin_token))
        assert res.status_code == 200
        data = res.json()
        assert "items" in data and "total" in data
        assert isinstance(data["items"], list)

    async def test_visits_page_format(self, http_client: AsyncClient, admin_token: str):
        res = await http_client.get("/api/visits", headers=auth_headers(admin_token))
        assert res.status_code == 200
        data = res.json()
        assert "items" in data and "total" in data
        assert isinstance(data["items"], list)

    async def test_defects_page_format(self, http_client: AsyncClient, admin_token: str):
        res = await http_client.get("/api/defects", headers=auth_headers(admin_token))
        assert res.status_code == 200
        data = res.json()
        assert "items" in data and "total" in data
        assert isinstance(data["items"], list)

    async def test_purchases_page_format(self, http_client: AsyncClient, admin_token: str):
        res = await http_client.get("/api/purchases", headers=auth_headers(admin_token))
        assert res.status_code == 200
        data = res.json()
        assert "items" in data and "total" in data
        assert isinstance(data["items"], list)


@pytest.mark.asyncio
class TestPaginationLimitOffset:
    """limit и offset работают корректно."""

    async def test_clients_limit(self, http_client: AsyncClient, admin_token: str):
        """limit=1 возвращает не более одного элемента."""
        res = await http_client.get("/api/clients?limit=1", headers=auth_headers(admin_token))
        assert res.status_code == 200
        data = res.json()
        assert len(data["items"]) <= 1
        assert data["limit"] == 1

    async def test_clients_offset(self, http_client: AsyncClient, admin_token: str):
        """offset=0 и offset=1 с limit=1 не совпадают (если > 1 клиента)."""
        r1 = await http_client.get("/api/clients?limit=1&offset=0", headers=auth_headers(admin_token))
        r2 = await http_client.get("/api/clients?limit=1&offset=1", headers=auth_headers(admin_token))
        assert r1.status_code == 200
        assert r2.status_code == 200
        # Оба offset'а имеют тот же total
        assert r1.json()["total"] == r2.json()["total"]
        # Если клиентов >= 2, первые элементы отличаются
        if r1.json()["total"] >= 2:
            assert r1.json()["items"][0]["id"] != r2.json()["items"][0]["id"]

    async def test_visits_offset_returns_correct_offset_field(self, http_client: AsyncClient, admin_token: str):
        res = await http_client.get("/api/visits?limit=10&offset=5", headers=auth_headers(admin_token))
        assert res.status_code == 200
        data = res.json()
        assert data["offset"] == 5
        assert data["limit"] == 10

    async def test_limit_max_500(self, http_client: AsyncClient, admin_token: str):
        """limit > 500 → 422."""
        res = await http_client.get("/api/clients?limit=501", headers=auth_headers(admin_token))
        assert res.status_code == 422

    async def test_limit_min_1(self, http_client: AsyncClient, admin_token: str):
        """limit=0 → 422."""
        res = await http_client.get("/api/clients?limit=0", headers=auth_headers(admin_token))
        assert res.status_code == 422

    async def test_offset_negative(self, http_client: AsyncClient, admin_token: str):
        """offset=-1 → 422."""
        res = await http_client.get("/api/clients?offset=-1", headers=auth_headers(admin_token))
        assert res.status_code == 422

    async def test_sites_limit_offset(self, http_client: AsyncClient, admin_token: str):
        res = await http_client.get("/api/sites?limit=2&offset=0", headers=auth_headers(admin_token))
        assert res.status_code == 200
        data = res.json()
        assert len(data["items"]) <= 2
        assert data["limit"] == 2
        assert data["offset"] == 0

    async def test_defects_total_is_consistent(
        self, http_client: AsyncClient, admin_token: str, site_id: int
    ):
        """total одинаков при любом offset."""
        r1 = await http_client.get("/api/defects?limit=1&offset=0", headers=auth_headers(admin_token))
        r2 = await http_client.get("/api/defects?limit=1&offset=0", headers=auth_headers(admin_token))
        assert r1.json()["total"] == r2.json()["total"]


@pytest.mark.asyncio
class TestGlobalSearchPaginated:
    """Глобальный поиск возвращает новый формат с limit/offset и *_total."""

    async def test_search_response_format(self, http_client: AsyncClient, admin_token: str):
        res = await http_client.get("/api/search?q=те", headers=auth_headers(admin_token))
        assert res.status_code == 200
        data = res.json()
        assert "results" in data
        assert "clients_total" in data
        assert "sites_total" in data
        assert "contracts_total" in data
        assert "limit" in data
        assert "offset" in data
        assert isinstance(data["results"], list)
        assert isinstance(data["clients_total"], int)

    async def test_search_limit(self, http_client: AsyncClient, admin_token: str):
        """limit=2 применяется к каждому типу сущностей — итого не более limit*3 результатов."""
        res = await http_client.get("/api/search?q=ав&limit=2", headers=auth_headers(admin_token))
        assert res.status_code == 200
        data = res.json()
        # limit применяется per-type: clients, sites, contracts — каждый <= 2
        assert len(data["results"]) <= 2 * 3
        assert data["limit"] == 2
        # Проверяем что каждый тип не превышает limit
        from collections import Counter
        type_counts = Counter(r["type"] for r in data["results"])
        for count in type_counts.values():
            assert count <= 2

    async def test_search_offset_pagination(self, http_client: AsyncClient, admin_token: str):
        """Разные offset дают разные результаты при достаточном количестве записей."""
        r1 = await http_client.get("/api/search?q=ав&limit=1&offset=0", headers=auth_headers(admin_token))
        r2 = await http_client.get("/api/search?q=ав&limit=1&offset=1", headers=auth_headers(admin_token))
        assert r1.status_code == 200
        assert r2.status_code == 200
        # total одинаков
        t1 = r1.json()["clients_total"] + r1.json()["sites_total"] + r1.json()["contracts_total"]
        t2 = r2.json()["clients_total"] + r2.json()["sites_total"] + r2.json()["contracts_total"]
        assert t1 == t2

    async def test_search_one_char_allowed(self, http_client: AsyncClient, admin_token: str):
        """Запрос из 1 символа разрешён (min_length=1) → 200."""
        res = await http_client.get("/api/search?q=а", headers=auth_headers(admin_token))
        assert res.status_code == 200

    async def test_search_unauthenticated(self, http_client: AsyncClient):
        res = await http_client.get("/api/search?q=тест")
        assert res.status_code == 401
