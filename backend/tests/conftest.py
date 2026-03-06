"""
Конфигурация тестового окружения.

Тесты работают с реальной БД (service_system_v2) и реальными seed-данными.
Каждый тест сам создаёт и удаляет тестовые записи, не ломая общие справочники.

Фикстуры сессионного уровня (scope="session"):
  - http_client     — httpx AsyncClient подключённый к FastAPI приложению
  - admin_token     — JWT токен пользователя admin@system.local
  - office_token    — JWT токен пользователя office1@system.local
  - master_token    — JWT токен пользователя master1@system.local
  - site_id         — ID первого сайта из БД (для тестов создания выездов)
  - admin_user_id   — ID пользователя admin (для назначения на выезды)

Хелперы:
  - auth_headers(token) — dict с Authorization header
"""

import pytest_asyncio
from httpx import AsyncClient, ASGITransport

from app.main import app


@pytest_asyncio.fixture(scope="session")
async def http_client():
    """httpx AsyncClient, смонтированный на FastAPI приложение.

    Перед запуском тестов вручную вызываем load_enums(), так как
    ASGITransport не запускает lifespan приложения автоматически.
    """
    from app.database import AsyncSessionLocal
    from app.enums import load_enums

    async with AsyncSessionLocal() as db:
        await load_enums(db)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c


@pytest_asyncio.fixture(scope="session")
async def admin_token(http_client: AsyncClient) -> str:
    res = await http_client.post("/api/auth/login", json={
        "email": "admin@system.local",
        "password": "admin123",
    })
    assert res.status_code == 200, f"Admin login failed: {res.text}"
    return res.json()["token"]


@pytest_asyncio.fixture(scope="session")
async def office_token(http_client: AsyncClient) -> str:
    res = await http_client.post("/api/auth/login", json={
        "email": "office1@system.local",
        "password": "admin123",
    })
    assert res.status_code == 200, f"Office login failed: {res.text}"
    return res.json()["token"]


@pytest_asyncio.fixture(scope="session")
async def master_token(http_client: AsyncClient) -> str:
    res = await http_client.post("/api/auth/login", json={
        "email": "master1@system.local",
        "password": "admin123",
    })
    assert res.status_code == 200, f"Master login failed: {res.text}"
    return res.json()["token"]


@pytest_asyncio.fixture(scope="session")
async def site_id(http_client: AsyncClient, admin_token: str):
    """Создаёт тестовый клиент и объект, возвращает site_id (int). Удаляет после сессии."""
    headers = auth_headers(admin_token)

    client_res = await http_client.post("/api/clients", headers=headers,
                                        json={"name": "__conftest__ тестовый клиент"})
    assert client_res.status_code == 201, f"Create client failed: {client_res.text}"
    client_id = client_res.json()["id"]

    site_res = await http_client.post("/api/sites", headers=headers,
                                      json={"title": "__conftest__ тестовый объект",
                                            "address": "г. Тест, ул. Конфтест, д. 1",
                                            "client_id": client_id})
    assert site_res.status_code == 201, f"Create site failed: {site_res.text}"
    sid = site_res.json()["id"]

    yield sid

    await http_client.delete(f"/api/sites/{sid}", headers=headers)
    await http_client.delete(f"/api/clients/{client_id}", headers=headers)


@pytest_asyncio.fixture(scope="session")
async def admin_user_id(http_client: AsyncClient, admin_token: str) -> str:
    """ID пользователя admin для назначения на выезды."""
    res = await http_client.get("/api/auth/me", headers=auth_headers(admin_token))
    assert res.status_code == 200, f"Get me failed: {res.text}"
    return str(res.json()["id"])


def auth_headers(token: str) -> dict:
    """Вернуть заголовок Authorization для запросов."""
    return {"Authorization": f"Bearer {token}"}
