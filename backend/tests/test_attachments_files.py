"""
Тесты файловых вложений для клиентов и объектов (Block 11 — Files & Photos).

POST /api/attachments  — создание (client_id / site_id / visit_id)
GET  /api/attachments  — список по фильтру
DELETE /api/attachments/{id} — удаление
"""

from httpx import AsyncClient
from tests.conftest import auth_headers


class TestAttachmentsClient:
    async def test_create_for_client(
        self, http_client: AsyncClient, admin_token: str, client_id: int
    ):
        """Создаём вложение для клиента."""
        headers = auth_headers(admin_token)
        res = await http_client.post(
            "/api/attachments",
            headers=headers,
            json={
                "client_id": client_id,
                "kind": "document",
                "file_url": "https://res.cloudinary.com/test/raw/upload/contract.pdf",
                "file_name": "contract.pdf",
            },
        )
        assert res.status_code == 201
        data = res.json()
        assert data["client_id"] == client_id
        assert data["kind"] == "document"
        assert data["file_name"] == "contract.pdf"
        return data["id"]

    async def test_get_by_client(
        self, http_client: AsyncClient, admin_token: str, client_id: int
    ):
        """GET /api/attachments?client_id= возвращает файлы клиента."""
        headers = auth_headers(admin_token)

        # Создаём вложение
        await http_client.post(
            "/api/attachments",
            headers=headers,
            json={
                "client_id": client_id,
                "kind": "photo",
                "file_url": "https://res.cloudinary.com/test/image/upload/photo.jpg",
                "file_name": "photo.jpg",
            },
        )

        res = await http_client.get(
            f"/api/attachments?client_id={client_id}", headers=headers
        )
        assert res.status_code == 200
        data = res.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        assert all(a["client_id"] == client_id for a in data)

    async def test_delete_attachment(
        self, http_client: AsyncClient, admin_token: str, client_id: int
    ):
        """DELETE /api/attachments/{id} удаляет файл."""
        headers = auth_headers(admin_token)

        # Создаём
        create_res = await http_client.post(
            "/api/attachments",
            headers=headers,
            json={
                "client_id": client_id,
                "kind": "document",
                "file_url": "https://res.cloudinary.com/test/raw/upload/to_delete.pdf",
                "file_name": "to_delete.pdf",
            },
        )
        att_id = create_res.json()["id"]

        # Удаляем
        del_res = await http_client.delete(f"/api/attachments/{att_id}", headers=headers)
        assert del_res.status_code == 204

        # Проверяем исчез
        list_res = await http_client.get(
            f"/api/attachments?client_id={client_id}", headers=headers
        )
        ids = [a["id"] for a in list_res.json()]
        assert att_id not in ids

    async def test_delete_nonexistent(self, http_client: AsyncClient, admin_token: str):
        """DELETE несуществующего вложения — 404."""
        res = await http_client.delete(
            "/api/attachments/999999", headers=auth_headers(admin_token)
        )
        assert res.status_code == 404


class TestAttachmentsSite:
    async def test_create_for_site(
        self, http_client: AsyncClient, admin_token: str, site_id: int
    ):
        """Создаём вложение для объекта."""
        headers = auth_headers(admin_token)
        res = await http_client.post(
            "/api/attachments",
            headers=headers,
            json={
                "site_id": site_id,
                "kind": "photo",
                "file_url": "https://res.cloudinary.com/test/image/upload/site.jpg",
                "file_name": "site.jpg",
            },
        )
        assert res.status_code == 201
        data = res.json()
        assert data["site_id"] == site_id
        assert data["kind"] == "photo"

    async def test_get_by_site(
        self, http_client: AsyncClient, admin_token: str, site_id: int
    ):
        """GET /api/attachments?site_id= возвращает файлы объекта."""
        headers = auth_headers(admin_token)

        await http_client.post(
            "/api/attachments",
            headers=headers,
            json={
                "site_id": site_id,
                "kind": "document",
                "file_url": "https://res.cloudinary.com/test/raw/upload/act.pdf",
                "file_name": "act.pdf",
            },
        )

        res = await http_client.get(
            f"/api/attachments?site_id={site_id}", headers=headers
        )
        assert res.status_code == 200
        data = res.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        assert all(a["site_id"] == site_id for a in data)

    async def test_attachment_has_file_name_field(
        self, http_client: AsyncClient, admin_token: str, site_id: int
    ):
        """Поле file_name присутствует в ответе."""
        headers = auth_headers(admin_token)
        res = await http_client.post(
            "/api/attachments",
            headers=headers,
            json={
                "site_id": site_id,
                "kind": "document",
                "file_url": "https://res.cloudinary.com/test/raw/upload/named.pdf",
                "file_name": "Договор_2026.pdf",
            },
        )
        assert res.status_code == 201
        assert res.json()["file_name"] == "Договор_2026.pdf"

    async def test_unauthenticated_rejected(self, http_client: AsyncClient):
        """Неаутентифицированный запрос — 401."""
        res = await http_client.get("/api/attachments?site_id=1")
        assert res.status_code == 401


class TestAttachmentsDefect:
    async def test_create_for_defect(
        self, http_client: AsyncClient, admin_token: str, site_id: int
    ):
        """Создаём вложение для дефекта."""
        headers = auth_headers(admin_token)

        defect_res = await http_client.post("/api/defects", headers=headers, json={
            "site_id": site_id, "title": "Тест дефект для фото",
            "priority": "medium", "action_type": "repair",
        })
        assert defect_res.status_code == 201
        defect_id = defect_res.json()["id"]

        res = await http_client.post("/api/attachments", headers=headers, json={
            "defect_id": defect_id,
            "kind": "photo",
            "file_url": "https://res.cloudinary.com/test/image/upload/defect.jpg",
            "file_name": "defect.jpg",
        })
        assert res.status_code == 201
        data = res.json()
        assert data["defect_id"] == defect_id
        assert data["kind"] == "photo"

    async def test_get_by_defect(
        self, http_client: AsyncClient, admin_token: str, site_id: int
    ):
        """GET /api/attachments?defect_id= возвращает фото дефекта."""
        headers = auth_headers(admin_token)

        defect_res = await http_client.post("/api/defects", headers=headers, json={
            "site_id": site_id, "title": "Тест дефект для get",
            "priority": "low", "action_type": "observation",
        })
        assert defect_res.status_code == 201
        defect_id = defect_res.json()["id"]

        await http_client.post("/api/attachments", headers=headers, json={
            "defect_id": defect_id, "kind": "photo",
            "file_url": "https://res.cloudinary.com/test/image/upload/d2.jpg",
            "file_name": "d2.jpg",
        })

        res = await http_client.get(f"/api/attachments?defect_id={defect_id}", headers=headers)
        assert res.status_code == 200
        data = res.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        assert all(a["defect_id"] == defect_id for a in data)
