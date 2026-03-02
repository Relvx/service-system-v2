"""
Тесты эндпоинтов аутентификации.

POST /api/auth/login         — вход по email/password, возврат JWT
GET  /api/auth/me            — профиль текущего пользователя
PUT  /api/auth/change-password — смена пароля
"""

import pytest
from httpx import AsyncClient

from tests.conftest import auth_headers


class TestLogin:
    async def test_login_success(self, http_client: AsyncClient):
        """Успешный вход возвращает access_token и данные пользователя."""
        res = await http_client.post("/api/auth/login", json={
            "email": "admin@system.local",
            "password": "admin123",
        })
        assert res.status_code == 200
        data = res.json()
        assert "token" in data
        assert data["user"]["email"] == "admin@system.local"
        assert "groups" in data["user"]

    async def test_login_wrong_password(self, http_client: AsyncClient):
        """Неверный пароль → 401."""
        res = await http_client.post("/api/auth/login", json={
            "email": "admin@system.local",
            "password": "wrongpassword",
        })
        assert res.status_code == 401

    async def test_login_unknown_email(self, http_client: AsyncClient):
        """Несуществующий пользователь → 401."""
        res = await http_client.post("/api/auth/login", json={
            "email": "nobody@nowhere.com",
            "password": "admin123",
        })
        assert res.status_code == 401

    async def test_login_missing_fields(self, http_client: AsyncClient):
        """Пустое тело запроса → 422."""
        res = await http_client.post("/api/auth/login", json={})
        assert res.status_code == 422


class TestGetMe:
    async def test_get_me_authenticated(self, http_client: AsyncClient, admin_token: str):
        """GET /me возвращает профиль текущего пользователя."""
        res = await http_client.get("/api/auth/me", headers=auth_headers(admin_token))
        assert res.status_code == 200
        data = res.json()
        assert data["email"] == "admin@system.local"
        assert isinstance(data["groups"], list)

    async def test_get_me_unauthenticated(self, http_client: AsyncClient):
        """Без токена → 401."""
        res = await http_client.get("/api/auth/me")
        assert res.status_code == 401

    async def test_get_me_invalid_token(self, http_client: AsyncClient):
        """Невалидный токен → 403."""
        res = await http_client.get("/api/auth/me", headers={"Authorization": "Bearer invalid.token.here"})
        assert res.status_code in (401, 403)


class TestChangePassword:
    async def test_change_password_wrong_current(self, http_client: AsyncClient, office_token: str):
        """Неверный текущий пароль → 401."""
        res = await http_client.put("/api/auth/change-password",
            headers=auth_headers(office_token),
            json={"current_password": "wrongpass", "new_password": "newpass123"},
        )
        assert res.status_code == 401
