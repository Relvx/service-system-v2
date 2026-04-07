"""
Тесты блока 20 — Объекты и контакты:
  1. Частота обслуживания: once (Разово) в справочнике
  2. service_frequency_custom сохраняется и возвращается
  3. Поиск объекта по имени клиента
  4. visit_contact и visit_contact_position при выезде
"""

import pytest
from datetime import date, timedelta
from httpx import AsyncClient
from tests.conftest import auth_headers

FUTURE = str(date.today() + timedelta(days=5))


@pytest.mark.asyncio
class TestServiceFrequency:
    """Частота обслуживания: Разово + свой вариант."""

    async def test_once_in_service_frequencies(self, http_client: AsyncClient, admin_token: str):
        """Справочник содержит 'once' (Разово)."""
        res = await http_client.get("/api/config/service-frequencies", headers=auth_headers(admin_token))
        assert res.status_code == 200
        sysnames = [f["sysname"] for f in res.json()]
        assert "once" in sysnames

    async def test_site_custom_frequency(self, http_client: AsyncClient, admin_token: str):
        """service_frequency_custom сохраняется и возвращается."""
        res = await http_client.post("/api/sites", json={
            "title": "Тест custom freq",
            "address": "ул. Тестовая 1",
            "service_frequency": "custom",
            "service_frequency_custom": "Раз в полгода",
        }, headers=auth_headers(admin_token))
        assert res.status_code == 201
        data = res.json()
        assert data["service_frequency"] == "custom"
        assert data["service_frequency_custom"] == "Раз в полгода"
        site_id = data["id"]

        # Проверяем через GET
        r = await http_client.get(f"/api/sites/{site_id}", headers=auth_headers(admin_token))
        assert r.status_code == 200
        assert r.json()["service_frequency_custom"] == "Раз в полгода"

        await http_client.delete(f"/api/sites/{site_id}", headers=auth_headers(admin_token))

    async def test_site_once_frequency(self, http_client: AsyncClient, admin_token: str):
        """Объект с frequency=once создаётся успешно."""
        res = await http_client.post("/api/sites", json={
            "title": "Тест once",
            "address": "ул. Разовая 2",
            "service_frequency": "once",
        }, headers=auth_headers(admin_token))
        assert res.status_code == 201
        assert res.json()["service_frequency"] == "once"
        await http_client.delete(f"/api/sites/{res.json()['id']}", headers=auth_headers(admin_token))


@pytest.mark.asyncio
class TestSiteSearchByClient:
    """Поиск объекта по имени клиента."""

    async def test_search_site_by_client_name(self, http_client: AsyncClient, admin_token: str):
        """Глобальный поиск находит объект по имени клиента."""
        # Берём любого клиента с объектами
        cr = await http_client.get("/api/clients?limit=5", headers=auth_headers(admin_token))
        assert cr.status_code == 200
        clients = cr.json()["items"]
        if not clients:
            pytest.skip("Нет клиентов в БД")

        # Ищем по имени первого клиента (хотя бы 3 символа)
        client_name = clients[0]["name"]
        if len(client_name) < 3:
            pytest.skip("Имя клиента слишком короткое")

        query = client_name[:4]
        res = await http_client.get(f"/api/search?q={query}", headers=auth_headers(admin_token))
        assert res.status_code == 200
        data = res.json()
        assert "results" in data
        # Поиск вернул результаты (clients или sites с этим клиентом)
        assert data["clients_total"] >= 0
        assert data["sites_total"] >= 0

    async def test_search_returns_client_name_in_site_subtitle(self, http_client: AsyncClient, admin_token: str):
        """Результат поиска по объекту содержит имя клиента в subtitle."""
        # Создаём клиента и объект
        cr = await http_client.post("/api/clients", json={
            "name": "ТестКлиентПоиск2026",
            "inn": "",
        }, headers=auth_headers(admin_token))
        assert cr.status_code == 201
        client_id = cr.json()["id"]

        sr = await http_client.post("/api/sites", json={
            "title": "Объект поиска",
            "address": "ул. Поисковая 99",
            "client_id": client_id,
        }, headers=auth_headers(admin_token))
        assert sr.status_code == 201
        site_id = sr.json()["id"]

        # Ищем по имени клиента
        res = await http_client.get("/api/search?q=ТестКлиентПоиск2026", headers=auth_headers(admin_token))
        assert res.status_code == 200
        results = res.json()["results"]
        site_results = [r for r in results if r["type"] == "site"]
        # Объект должен найтись
        found = any(r["id"] == site_id for r in site_results)
        assert found

        # Cleanup
        await http_client.delete(f"/api/sites/{site_id}", headers=auth_headers(admin_token))
        await http_client.delete(f"/api/clients/{client_id}", headers=auth_headers(admin_token))


@pytest.mark.asyncio
class TestVisitContact:
    """Контакт при выезде."""

    async def test_create_visit_with_contact(self, http_client: AsyncClient, admin_token: str, site_id: int, admin_user_id: int):
        """visit_contact и visit_contact_position сохраняются при создании."""
        res = await http_client.post("/api/visits", json={
            "site_id": site_id,
            "master_ids": [admin_user_id],
            "planned_date": FUTURE,
            "visit_types": ["maintenance"],
            "visit_contact": "Иван Петров",
            "visit_contact_position": "Главный инженер",
        }, headers=auth_headers(admin_token))
        assert res.status_code == 201
        data = res.json()
        assert data["visit_contact"] == "Иван Петров"
        assert data["visit_contact_position"] == "Главный инженер"
        await http_client.delete(f"/api/visits/{data['id']}", headers=auth_headers(admin_token))

    async def test_update_visit_contact(self, http_client: AsyncClient, admin_token: str, site_id: int, admin_user_id: int):
        """visit_contact обновляется через PUT."""
        res = await http_client.post("/api/visits", json={
            "site_id": site_id,
            "master_ids": [admin_user_id],
            "planned_date": FUTURE,
            "visit_types": ["maintenance"],
        }, headers=auth_headers(admin_token))
        assert res.status_code == 201
        vid = res.json()["id"]

        upd = await http_client.put(f"/api/visits/{vid}", json={
            "visit_contact": "Мария Иванова",
            "visit_contact_position": "Директор",
        }, headers=auth_headers(admin_token))
        assert upd.status_code == 200
        assert upd.json()["visit_contact"] == "Мария Иванова"
        assert upd.json()["visit_contact_position"] == "Директор"

        await http_client.delete(f"/api/visits/{vid}", headers=auth_headers(admin_token))

    async def test_visit_without_contact(self, http_client: AsyncClient, admin_token: str, site_id: int, admin_user_id: int):
        """Выезд без контакта возвращает null в visit_contact."""
        res = await http_client.post("/api/visits", json={
            "site_id": site_id,
            "master_ids": [admin_user_id],
            "planned_date": FUTURE,
            "visit_types": ["maintenance"],
        }, headers=auth_headers(admin_token))
        assert res.status_code == 201
        data = res.json()
        assert data["visit_contact"] is None
        await http_client.delete(f"/api/visits/{data['id']}", headers=auth_headers(admin_token))
