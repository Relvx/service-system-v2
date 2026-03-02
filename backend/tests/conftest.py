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
async def site_id(http_client: AsyncClient, admin_token: str) -> str:
    """ID первого сайта из БД для использования при создании выездов."""
    res = await http_client.get("/api/sites", headers=auth_headers(admin_token))
    assert res.status_code == 200, f"Get sites failed: {res.text}"
    sites = res.json()
    assert len(sites) > 0, "No sites in DB — seed data missing"
    return str(sites[0]["id"])


@pytest_asyncio.fixture(scope="session")
async def admin_user_id(http_client: AsyncClient, admin_token: str) -> str:
    """ID пользователя admin для назначения на выезды."""
    res = await http_client.get("/api/auth/me", headers=auth_headers(admin_token))
    assert res.status_code == 200, f"Get me failed: {res.text}"
    return str(res.json()["id"])


def auth_headers(token: str) -> dict:
    """Вернуть заголовок Authorization для запросов."""
    return {"Authorization": f"Bearer {token}"}
