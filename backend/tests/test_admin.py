"""
Тесты эндпоинтов административной панели.

GET    /api/admin/users                              — список пользователей
POST   /api/admin/users                              — создание пользователя
PUT    /api/admin/users/{id}                         — обновление пользователя
DELETE /api/admin/users/{id}                         — удаление пользователя
POST   /api/admin/users/{id}/groups/{sysname}        — добавить в группу
DELETE /api/admin/users/{id}/groups/{sysname}        — убрать из группы
GET    /api/admin/permission-groups                  — список групп прав
POST   /api/admin/permission-groups                  — создание группы прав
GET    /api/admin/permissions                        — список прав
"""

from httpx import AsyncClient
from tests.conftest import auth_headers


class TestAdminAccess:
    async def test_office_forbidden(self, http_client: AsyncClient, office_token: str):
        """Офис не имеет доступа к admin API."""
        res = await http_client.get("/api/admin/users", headers=auth_headers(office_token))
        assert res.status_code == 403

    async def test_master_forbidden(self, http_client: AsyncClient, master_token: str):
        res = await http_client.get("/api/admin/users", headers=auth_headers(master_token))
        assert res.status_code == 403

    async def test_unauthenticated_forbidden(self, http_client: AsyncClient):
        res = await http_client.get("/api/admin/users")
        assert res.status_code == 401


class TestAdminUsers:
    async def test_list_users(self, http_client: AsyncClient, admin_token: str):
        """Список пользователей возвращает массив с seed-данными."""
        res = await http_client.get("/api/admin/users", headers=auth_headers(admin_token))
        assert res.status_code == 200
        data = res.json()
        assert isinstance(data, list)
        assert len(data) > 0
        emails = [u["email"] for u in data]
        assert "admin@system.local" in emails

    async def test_user_has_groups(self, http_client: AsyncClient, admin_token: str):
        """Пользователи содержат список групп."""
        res = await http_client.get("/api/admin/users", headers=auth_headers(admin_token))
        for user in res.json():
            assert "groups" in user
            assert isinstance(user["groups"], list)

    async def test_create_and_delete_user(self, http_client: AsyncClient, admin_token: str):
        """Создание нового пользователя и удаление."""
        headers = auth_headers(admin_token)
        payload = {
            "email": "__test__user@system.local",
            "password": "testpass123",
            "full_name": "Тест Тестов",
        }

        res = await http_client.post("/api/admin/users", headers=headers, json=payload)
        assert res.status_code == 201
        user_id = res.json()["id"]
        assert res.json()["email"] == payload["email"]

        del_res = await http_client.delete(f"/api/admin/users/{user_id}", headers=headers)
        assert del_res.status_code == 204

    async def test_create_duplicate_email(self, http_client: AsyncClient, admin_token: str):
        """Дублирующийся email → 409."""
        headers = auth_headers(admin_token)
        res = await http_client.post("/api/admin/users", headers=headers, json={
            "email": "admin@system.local",
            "password": "admin123",
            "full_name": "Дубль",
        })
        assert res.status_code == 409

    async def test_update_user(self, http_client: AsyncClient, admin_token: str):
        """Обновление full_name пользователя."""
        headers = auth_headers(admin_token)

        res = await http_client.post("/api/admin/users", headers=headers, json={
            "email": "__test__upd@system.local",
            "password": "testpass123",
            "full_name": "Исходное Имя",
        })
        user_id = res.json()["id"]

        upd = await http_client.put(f"/api/admin/users/{user_id}", headers=headers,
                                     json={"full_name": "Новое Имя"})
        assert upd.status_code == 200
        assert upd.json()["full_name"] == "Новое Имя"

        await http_client.delete(f"/api/admin/users/{user_id}", headers=headers)


class TestAdminPermissionGroups:
    async def test_list_groups(self, http_client: AsyncClient, admin_token: str):
        res = await http_client.get("/api/admin/permission-groups",
                                    headers=auth_headers(admin_token))
        assert res.status_code == 200
        data = res.json()
        assert isinstance(data, list)
        sysnames = [g["sysname"] for g in data]
        assert "admin_group" in sysnames
        assert "office_group" in sysnames
        assert "master_group" in sysnames

    async def test_list_permissions(self, http_client: AsyncClient, admin_token: str):
        res = await http_client.get("/api/admin/permissions",
                                    headers=auth_headers(admin_token))
        assert res.status_code == 200
        data = res.json()
        assert isinstance(data, list)
        assert len(data) > 0
        perm = data[0]
        assert "sysname" in perm
        assert "resource" in perm
        assert "action" in perm

    async def test_create_and_delete_group(self, http_client: AsyncClient, admin_token: str):
        headers = auth_headers(admin_token)
        payload = {
            "sysname": "__test_group",
            "display_name": "Тестовая группа",
            "default_redirect": "/dashboard",
        }

        res = await http_client.post("/api/admin/permission-groups", headers=headers, json=payload)
        assert res.status_code == 201
        assert res.json()["sysname"] == "__test_group"

        del_res = await http_client.delete("/api/admin/permission-groups/__test_group",
                                            headers=headers)
        assert del_res.status_code == 204
