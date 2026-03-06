"""
Тесты детальной страницы клиента (Блок 2).

GET    /api/clients/{id}               — детальная карточка (ClientDetailOut)
POST   /api/clients/{id}/contacts      — добавить контакт
PUT    /api/clients/{id}/contacts/{id} — обновить контакт
DELETE /api/clients/{id}/contacts/{id} — удалить контакт
PUT    /api/clients/{id}/legal         — создать/обновить реквизиты
"""

from httpx import AsyncClient
from tests.conftest import auth_headers

CLIENT_PAYLOAD = {
    "name": "__test_detail__ ООО Детали",
    "inn": "9876543210",
}

CONTACT_PAYLOAD = {
    "full_name": "Петров Пётр Петрович",
    "position": "Директор",
    "phone": "+7-900-111-22-33",
    "email": "petrov@test.local",
    "is_primary": True,
}

LEGAL_PAYLOAD = {
    "legal_address": "г. Москва, ул. Тестовая, д. 1",
    "bank": "ПАО Тестбанк",
    "bik": "044525225",
    "account": "40702810000000000001",
}


class TestClientDetail:
    async def test_get_detail_returns_structure(self, http_client: AsyncClient, admin_token: str):
        """GET /{id} возвращает ClientDetailOut с полями contacts, legal, sites, recent_visits."""
        headers = auth_headers(admin_token)

        res = await http_client.post("/api/clients", headers=headers, json=CLIENT_PAYLOAD)
        assert res.status_code == 201
        client_id = res.json()["id"]

        detail = await http_client.get(f"/api/clients/{client_id}", headers=headers)
        assert detail.status_code == 200
        data = detail.json()
        assert data["id"] == client_id
        assert "contact_persons" in data
        assert "legal" in data
        assert "sites" in data
        assert "recent_visits" in data
        assert isinstance(data["contact_persons"], list)
        assert isinstance(data["sites"], list)
        assert isinstance(data["recent_visits"], list)

        await http_client.delete(f"/api/clients/{client_id}", headers=headers)

    async def test_get_detail_not_found(self, http_client: AsyncClient, admin_token: str):
        """GET несуществующего клиента → 404."""
        fake_id = 999999
        res = await http_client.get(f"/api/clients/{fake_id}", headers=auth_headers(admin_token))
        assert res.status_code == 404


class TestClientContacts:
    async def test_add_contact(self, http_client: AsyncClient, admin_token: str):
        """POST /contacts создаёт контактное лицо."""
        headers = auth_headers(admin_token)

        res = await http_client.post("/api/clients", headers=headers, json=CLIENT_PAYLOAD)
        client_id = res.json()["id"]

        contact_res = await http_client.post(
            f"/api/clients/{client_id}/contacts", headers=headers, json=CONTACT_PAYLOAD
        )
        assert contact_res.status_code == 201
        data = contact_res.json()
        assert data["full_name"] == CONTACT_PAYLOAD["full_name"]
        assert data["is_primary"] is True
        assert data["client_id"] == client_id

        await http_client.delete(f"/api/clients/{client_id}", headers=headers)

    async def test_contact_appears_in_detail(self, http_client: AsyncClient, admin_token: str):
        """Добавленный контакт отображается в детальной карточке клиента."""
        headers = auth_headers(admin_token)

        res = await http_client.post("/api/clients", headers=headers, json=CLIENT_PAYLOAD)
        client_id = res.json()["id"]

        await http_client.post(
            f"/api/clients/{client_id}/contacts", headers=headers, json=CONTACT_PAYLOAD
        )

        detail = await http_client.get(f"/api/clients/{client_id}", headers=headers)
        contacts = detail.json()["contact_persons"]
        assert len(contacts) == 1
        assert contacts[0]["full_name"] == CONTACT_PAYLOAD["full_name"]

        await http_client.delete(f"/api/clients/{client_id}", headers=headers)

    async def test_update_contact(self, http_client: AsyncClient, admin_token: str):
        """PUT /contacts/{id} обновляет поля контакта."""
        headers = auth_headers(admin_token)

        res = await http_client.post("/api/clients", headers=headers, json=CLIENT_PAYLOAD)
        client_id = res.json()["id"]

        c_res = await http_client.post(
            f"/api/clients/{client_id}/contacts", headers=headers, json=CONTACT_PAYLOAD
        )
        contact_id = c_res.json()["id"]

        upd = await http_client.put(
            f"/api/clients/{client_id}/contacts/{contact_id}",
            headers=headers,
            json={"full_name": "Сидоров Сидор"},
        )
        assert upd.status_code == 200
        assert upd.json()["full_name"] == "Сидоров Сидор"

        await http_client.delete(f"/api/clients/{client_id}", headers=headers)

    async def test_delete_contact(self, http_client: AsyncClient, admin_token: str):
        """DELETE /contacts/{id} удаляет контакт."""
        headers = auth_headers(admin_token)

        res = await http_client.post("/api/clients", headers=headers, json=CLIENT_PAYLOAD)
        client_id = res.json()["id"]

        c_res = await http_client.post(
            f"/api/clients/{client_id}/contacts", headers=headers, json=CONTACT_PAYLOAD
        )
        contact_id = c_res.json()["id"]

        del_res = await http_client.delete(
            f"/api/clients/{client_id}/contacts/{contact_id}", headers=headers
        )
        assert del_res.status_code == 204

        detail = await http_client.get(f"/api/clients/{client_id}", headers=headers)
        assert detail.json()["contact_persons"] == []

        await http_client.delete(f"/api/clients/{client_id}", headers=headers)

    async def test_add_contact_client_not_found(self, http_client: AsyncClient, admin_token: str):
        """POST /contacts для несуществующего клиента → 404."""
        fake_id = 999999
        res = await http_client.post(
            f"/api/clients/{fake_id}/contacts",
            headers=auth_headers(admin_token),
            json=CONTACT_PAYLOAD,
        )
        assert res.status_code == 404


class TestClientLegal:
    async def test_upsert_legal_creates(self, http_client: AsyncClient, admin_token: str):
        """PUT /legal создаёт реквизиты если их нет."""
        headers = auth_headers(admin_token)

        res = await http_client.post("/api/clients", headers=headers, json=CLIENT_PAYLOAD)
        client_id = res.json()["id"]

        legal_res = await http_client.put(
            f"/api/clients/{client_id}/legal", headers=headers, json=LEGAL_PAYLOAD
        )
        assert legal_res.status_code == 200
        data = legal_res.json()
        assert data["bank"] == LEGAL_PAYLOAD["bank"]
        assert data["bik"] == LEGAL_PAYLOAD["bik"]
        assert data["client_id"] == client_id

        await http_client.delete(f"/api/clients/{client_id}", headers=headers)

    async def test_upsert_legal_updates(self, http_client: AsyncClient, admin_token: str):
        """PUT /legal обновляет существующие реквизиты."""
        headers = auth_headers(admin_token)

        res = await http_client.post("/api/clients", headers=headers, json=CLIENT_PAYLOAD)
        client_id = res.json()["id"]

        await http_client.put(
            f"/api/clients/{client_id}/legal", headers=headers, json=LEGAL_PAYLOAD
        )
        upd = await http_client.put(
            f"/api/clients/{client_id}/legal",
            headers=headers,
            json={"bank": "Другой банк"},
        )
        assert upd.status_code == 200
        assert upd.json()["bank"] == "Другой банк"

        await http_client.delete(f"/api/clients/{client_id}", headers=headers)

    async def test_legal_appears_in_detail(self, http_client: AsyncClient, admin_token: str):
        """Реквизиты отображаются в детальной карточке клиента."""
        headers = auth_headers(admin_token)

        res = await http_client.post("/api/clients", headers=headers, json=CLIENT_PAYLOAD)
        client_id = res.json()["id"]

        await http_client.put(
            f"/api/clients/{client_id}/legal", headers=headers, json=LEGAL_PAYLOAD
        )

        detail = await http_client.get(f"/api/clients/{client_id}", headers=headers)
        legal = detail.json()["legal"]
        assert legal is not None
        assert legal["bank"] == LEGAL_PAYLOAD["bank"]

        await http_client.delete(f"/api/clients/{client_id}", headers=headers)

    async def test_legal_client_not_found(self, http_client: AsyncClient, admin_token: str):
        """PUT /legal для несуществующего клиента → 404."""
        fake_id = 999999
        res = await http_client.put(
            f"/api/clients/{fake_id}/legal",
            headers=auth_headers(admin_token),
            json=LEGAL_PAYLOAD,
        )
        assert res.status_code == 404
