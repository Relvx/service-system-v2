"""
Block 20 — AdminPage: удаление группы прав.

DELETE /admin/permission-groups/{sysname} — только admin_group.
"""
import pytest
from httpx import AsyncClient
from tests.conftest import auth_headers


@pytest.mark.asyncio
class TestDeletePermissionGroup:
    async def test_admin_can_delete_group(self, http_client: AsyncClient, admin_token: str):
        """Администратор может создать и удалить группу прав."""
        headers = auth_headers(admin_token)

        # Создаём группу
        res = await http_client.post("/api/admin/permission-groups", headers=headers, json={
            "sysname": "b20_test_group",
            "display_name": "B20 Test Group",
            "default_redirect": "/dashboard",
        })
        assert res.status_code == 201

        # Удаляем
        del_res = await http_client.delete("/api/admin/permission-groups/b20_test_group", headers=headers)
        assert del_res.status_code in (200, 204)

        # Убеждаемся, что группа исчезла
        list_res = await http_client.get("/api/admin/permission-groups", headers=headers)
        sysnames = [g["sysname"] for g in list_res.json()]
        assert "b20_test_group" not in sysnames

    async def test_office_cannot_delete_group(self, http_client: AsyncClient, office_token: str, admin_token: str):
        """Офис не может удалять группы прав."""
        admin_headers = auth_headers(admin_token)
        office_headers = auth_headers(office_token)

        # Создаём группу от имени admin
        res = await http_client.post("/api/admin/permission-groups", headers=admin_headers, json={
            "sysname": "b20_office_test",
            "display_name": "B20 Office Test",
            "default_redirect": "/dashboard",
        })
        assert res.status_code == 201

        try:
            # Офис пытается удалить — должен получить 403
            del_res = await http_client.delete(
                "/api/admin/permission-groups/b20_office_test",
                headers=office_headers,
            )
            assert del_res.status_code == 403
        finally:
            await http_client.delete("/api/admin/permission-groups/b20_office_test", headers=admin_headers)

    async def test_delete_nonexistent_group(self, http_client: AsyncClient, admin_token: str):
        """Удаление несуществующей группы возвращает 404."""
        res = await http_client.delete(
            "/api/admin/permission-groups/nonexistent_xyz_b20",
            headers=auth_headers(admin_token),
        )
        assert res.status_code == 404
