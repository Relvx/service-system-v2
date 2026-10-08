"""Run only against an explicitly isolated PostgreSQL database ending in _test."""
import asyncio
import json
from copy import deepcopy
from datetime import datetime, timedelta, timezone
from uuid import uuid4
import pytest
import pytest_asyncio
from sqlalchemy import select, delete, func
from app.config import settings
from app.database import AsyncSessionLocal
from app.models.website_request import WebsiteRequest, WebsiteRequestEvent, WebsiteIntegrationConnection
from app.models.notification import Notification
from app.models.client import Client
from app.models.site import Site
from app.models.client_contact import ClientContact
from app.models.user import User
from app.models.config_tables import PermissionGroup
from app.models.log import Log
from app.utils.auth import create_token
from tests.conftest import auth_headers

INTAKE = '/api/integrations/website/service-requests'
OFFICE = '/api/website-requests'


def payload(**changes):
    now = datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
    body = dict(schema_version=1, external_id=str(uuid4()), website_reference='AG-900001', submitted_at=now,
        request_mode='callback', request_intent='general', customer_type=None, contact_name=None, company_name=None,
        phone='+79990000000', email=None, service_category=None, work_type=None, cooperation_format=None,
        object_address=None, message=None, source_page='/concepts/editorial/', legacy_form_type='lead_contact',
        legacy_equipment=None, consent={'accepted': True, 'accepted_at': now, 'policy_version': 'privacy-v1'})
    body.update(changes)
    return body


@pytest_asyncio.fixture(autouse=True)
async def isolated_cleanup():
    assert settings.DB_NAME.endswith('_test'), 'Website integration tests require an isolated *_test database'
    yield
    async with AsyncSessionLocal() as db:
        await db.execute(delete(Notification).where(Notification.type == 'website_request_new'))
        await db.execute(delete(WebsiteRequest))
        await db.execute(delete(WebsiteIntegrationConnection))
        await db.execute(delete(Log).where(Log.entity_type == 'website_request'))
        await db.execute(delete(Site).where(Site.title.like('__website_test_%')))
        await db.execute(delete(Client).where(Client.name.like('__website_test_%')))
        await db.commit()


@pytest_asyncio.fixture
async def connection(http_client, admin_token):
    r = await http_client.post(OFFICE + '/connections', headers=auth_headers(admin_token), json={})
    assert r.status_code == 201, r.text
    assert r.headers['cache-control'] == 'no-store'
    return r.json()


async def post(http_client, connection, body, **kwargs):
    headers = {**auth_headers(connection['token']), 'Idempotency-Key': body['external_id'], 'Content-Type': 'application/json'}
    headers.update(kwargs.pop('headers', {}))
    return await http_client.post(INTAKE, content=json.dumps(body, ensure_ascii=True).encode(), headers=headers, **kwargs)


@pytest_asyncio.fixture
async def received(http_client, connection):
    body = payload()
    r = await post(http_client, connection, body)
    assert r.status_code == 201, r.text
    return {**r.json(), 'body': body}


async def test_callback_is_saved_without_client_or_visit(http_client, admin_token, received):
    r = await http_client.get(f"{OFFICE}/{received['id']}", headers=auth_headers(admin_token))
    assert r.status_code == 200, r.text
    data = r.json()
    assert data['payload'] == received['body']
    assert data['client_id'] is None and data['site_id'] is None
    assert data['status'] == 'new' and data['version'] == 1
    assert data['events'][0]['kind'] == 'received'


async def test_original_time_format_is_preserved_but_hash_is_canonical(http_client, connection, admin_token):
    body = payload(submitted_at='2026-10-08T08:00:00.123Z')
    body['consent']['accepted_at'] = '2026-10-08T08:00:00.123Z'
    first = await post(http_client, connection, body)
    assert first.status_code == 201
    alternate = deepcopy(body)
    alternate['submitted_at'] = '2026-10-08T11:00:00.123000+03:00'
    alternate['consent']['accepted_at'] = '2026-10-08T08:00:00.123000+00:00'
    assert (await post(http_client, connection, alternate)).status_code == 200
    detail = (await http_client.get(f"{OFFICE}/{first.json()['id']}", headers=auth_headers(admin_token))).json()
    assert detail['payload'] == body


async def test_repeat_and_concurrent_delivery_are_atomic(http_client, connection, admin_token):
    body = payload()
    replies = await asyncio.gather(*(post(http_client, connection, body) for _ in range(5)))
    assert sorted(r.status_code for r in replies) == [200, 200, 200, 200, 201]
    assert len({r.json()['id'] for r in replies}) == 1
    async with AsyncSessionLocal() as db:
        assert (await db.execute(select(func.count()).select_from(WebsiteRequest))).scalar_one() == 1
        assert (await db.execute(select(func.count()).select_from(WebsiteRequestEvent))).scalar_one() == 1
        notifications = (await db.execute(select(Notification).where(Notification.type == 'website_request_new'))).scalars().all()
        assert notifications
        ids = [n.user_id for n in notifications]
        assert len(ids) == len(set(ids))
        for n in notifications:
            user = await db.get(User, n.user_id)
            assert {g.sysname for g in user.groups} & {'office_group', 'admin_group'}
            assert body['phone'] not in n.message
    changed = deepcopy(body); changed['request_intent'] = 'documents'
    assert (await post(http_client, connection, changed)).status_code == 409
    assert (await post(http_client, connection, dict(reversed(list(body.items()))))).status_code == 200


@pytest.mark.parametrize('changes', [
    {'schema_version': 2}, {'schema_version': True}, {'external_id': 'wrong'}, {'phone': '+7 (999) 000-00-00'},
    {'phone': '123'}, {'source_page': 'https://example.com/'}, {'source_page': '/?phone=secret'},
    {'website_reference': 'wrong'}, {'company_name': 'Unexpected callback details'},
    {'consent': {'accepted': False, 'accepted_at': datetime.now(timezone.utc).isoformat(), 'policy_version': 'privacy-v1'}},
    {'consent': {'accepted': 'true', 'accepted_at': datetime.now(timezone.utc).isoformat(), 'policy_version': 'privacy-v1'}},
    {'submitted_at': '2026-10-08T08:00:00'}, {'extra_private_field': 'should not be accepted'},
    {'request_mode': 'detailed', 'message': 'Bad\x00text'},
    {'request_mode': 'detailed', 'message': '\ud800'},
])
async def test_invalid_intake_is_not_saved(http_client, connection, changes):
    r = await post(http_client, connection, payload(**changes))
    assert r.status_code == 422, r.text
    async with AsyncSessionLocal() as db:
        assert (await db.execute(select(func.count()).select_from(WebsiteRequest))).scalar_one() == 0


async def test_body_and_key_limits(http_client, connection):
    body = payload()
    assert (await post(http_client, connection, body, headers={'Idempotency-Key': str(uuid4())})).status_code == 422
    headers = {**auth_headers(connection['token']), 'Idempotency-Key': body['external_id'], 'Content-Type': 'application/json'}
    assert (await http_client.post(INTAKE, content=b' ' * 32769, headers=headers)).status_code == 413
    assert (await http_client.post(INTAKE, content=b'{', headers=headers)).status_code == 422
    headers['Content-Type'] = 'text/plain'
    assert (await http_client.post(INTAKE, content=b'{}', headers=headers)).status_code == 415


@pytest.mark.parametrize('intent', ['general', 'documents', 'verification'])
async def test_callback_intents_survive(http_client, connection, intent):
    assert (await post(http_client, connection, payload(request_intent=intent))).status_code == 201


async def test_detailed_and_legacy_contract(http_client, connection):
    detail = payload(request_mode='detailed', customer_type='private', contact_name='Тестовый заказчик',
        email='a' * 240 + '@example.test', service_category='heat', work_type='verification',
        cooperation_format='single', object_address='Тестовый адрес', message='Поверка через партнёра')
    assert len(detail['email']) <= 254
    assert (await post(http_client, connection, detail)).status_code == 201
    legal = payload(request_mode='detailed', customer_type='legal', contact_name='Тест', service_category='gas', work_type='repair')
    assert (await post(http_client, connection, legal)).status_code == 422
    legal['company_name'] = 'Тестовая организация'
    assert (await post(http_client, connection, legal)).status_code == 201
    old = payload(request_mode='detailed', legacy_form_type='lead_kp', service_category='other',
                  legacy_equipment={'description': 'Промышленный котёл', 'power': '100 кВт'})
    assert (await post(http_client, connection, old)).status_code == 201


async def test_access_is_separate_from_report_keys_and_human_tokens(http_client, connection, received, admin_token, office_token, master_token):
    for token, expected in [(admin_token, 200), (office_token, 200), (master_token, 403), (connection['token'], 401)]:
        h = auth_headers(token)
        assert (await http_client.get(OFFICE, headers=h)).status_code == expected
        assert (await http_client.get(f"{OFFICE}/{received['id']}", headers=h)).status_code == expected
    assert (await http_client.get(OFFICE)).status_code == 401
    assert (await http_client.post(INTAKE, headers={**auth_headers(admin_token), 'Idempotency-Key': str(uuid4())}, json=payload())).status_code == 401
    report_key = (await http_client.post('/api/work-reports/connections', headers=auth_headers(admin_token))).json()['token']
    assert (await post(http_client, {'token': report_key}, payload())).status_code == 401
    assert (await http_client.get('/api/work-reports', headers=auth_headers(connection['token']))).status_code == 401
    assert (await http_client.post(OFFICE + '/connections', headers=auth_headers(office_token), json={})).status_code == 403
    rows = (await http_client.get(OFFICE + '/connections', headers=auth_headers(admin_token))).json()
    assert all('token' not in r and 'token_hash' not in r for r in rows)


async def test_revocation_expiration_and_rotation_keep_idempotency(http_client, connection, admin_token, received):
    new_key = (await http_client.post(OFFICE + '/connections', headers=auth_headers(admin_token), json={})).json()
    r = await post(http_client, new_key, received['body'])
    assert r.status_code == 200 and r.json()['id'] == received['id']
    assert (await http_client.delete(f"{OFFICE}/connections/{connection['id']}", headers=auth_headers(admin_token))).status_code == 204
    assert (await post(http_client, connection, payload())).status_code == 401
    async with AsyncSessionLocal() as db:
        key = await db.get(WebsiteIntegrationConnection, new_key['id'])
        key.expires_at = datetime.now(timezone.utc) - timedelta(seconds=1)
        await db.commit()
    assert (await post(http_client, new_key, payload())).status_code == 401


async def test_office_changes_keep_original_and_detect_stale_versions(http_client, received, office_token, master_token):
    url, h = f"{OFFICE}/{received['id']}", auth_headers(office_token)
    r = await http_client.patch(url, headers=h, json={'version': 1, 'status': 'in_progress', 'working_data': {'contact_name': 'Уточнённое имя', 'phone': '+79991111111'}})
    assert r.status_code == 200, r.text
    assert r.json()['version'] == 2 and r.json()['payload'] == received['body']
    assert (await http_client.patch(url, headers=h, json={'version': 1, 'status': 'spam'})).status_code == 409
    assert (await http_client.patch(url, headers=h, json={'version': 2, 'status': 'closed'})).status_code == 422
    r = await http_client.patch(url, headers=h, json={'version': 2, 'status': 'closed', 'outcome': 'Клиент отказался'})
    assert r.status_code == 200 and r.json()['version'] == 3
    r = await http_client.post(url + '/comments', headers=h, json={'text': 'Проверено офисом'})
    assert r.status_code == 201 and r.json()['events'][-1]['data']['text'] == 'Проверено офисом'
    assert (await http_client.post(url + '/comments', headers=h, json={'text': ' '})).status_code == 422
    assert (await http_client.patch(url, headers=auth_headers(master_token), json={'version': 3, 'status': 'new'})).status_code == 403
    async with AsyncSessionLocal() as db:
        master = (await db.execute(select(User).where(User.username == 'master1'))).scalar_one()
    assert (await http_client.patch(url, headers=h, json={'version': 3, 'assigned_user_id': master.id})).status_code == 422
    people = (await http_client.get(OFFICE + '/assignees', headers=h)).json()
    assert master.id not in [p['id'] for p in people]


async def test_link_create_is_atomic_and_idempotent(http_client, received, office_token):
    command = {'command_id': str(uuid4()), 'version': 1, 'new_client': {'name': '__website_test_client'},
               'new_contact': {'contact_name': 'Тестовый контакт', 'phone': '+79990000000', 'email': 'a' * 240 + '@example.test'},
               'new_site': {'title': '__website_test_site', 'address': 'Тестовый адрес'}}
    url, h = f"{OFFICE}/{received['id']}/link", auth_headers(office_token)
    responses = await asyncio.gather(*(http_client.post(url, headers=h, json=command) for _ in range(3)))
    assert all(r.status_code == 200 for r in responses), [r.text for r in responses]
    result = responses[0].json()
    assert all(r.json() == result for r in responses)
    async with AsyncSessionLocal() as db:
        assert (await db.execute(select(func.count()).select_from(Client).where(Client.name == '__website_test_client'))).scalar_one() == 1
        contact = await db.get(ClientContact, result['contact_id'])
        assert contact.email == command['new_contact']['email']
    command['new_client']['name'] = '__website_test_changed'
    assert (await http_client.post(url, headers=h, json=command)).status_code == 409
    data = (await http_client.get(f"{OFFICE}/{received['id']}", headers=h)).json()
    assert data['status'] == 'new' and data['links']['site']['name'] == '__website_test_site'


async def test_failed_link_rolls_back_created_client(http_client, received, office_token):
    h = auth_headers(office_token)
    r = await http_client.post(f"{OFFICE}/{received['id']}/link", headers=h, json={
        'command_id': str(uuid4()), 'version': 1, 'new_client': {'name': '__website_test_rollback'}, 'site_id': 999999999})
    assert r.status_code == 422
    async with AsyncSessionLocal() as db:
        assert (await db.execute(select(func.count()).select_from(Client).where(Client.name == '__website_test_rollback'))).scalar_one() == 0
        row = await db.get(WebsiteRequest, received['id'])
        assert row.version == 1 and row.client_id is None


async def test_cross_client_links_rejected(http_client, received, office_token):
    async with AsyncSessionLocal() as db:
        a, b = Client(name='__website_test_a'), Client(name='__website_test_b')
        db.add_all([a, b]); await db.flush()
        site = Site(client_id=b.id, title='__website_test_foreign', address='Тест')
        contact = ClientContact(client_id=b.id, full_name='Чужой контакт')
        db.add_all([site, contact]); await db.commit()
    for field, value in [('site_id', site.id), ('contact_id', contact.id)]:
        r = await http_client.post(f"{OFFICE}/{received['id']}/link", headers=auth_headers(office_token), json={
            'command_id': str(uuid4()), 'version': 1, 'client_id': a.id, field: value})
        assert r.status_code == 422


async def test_list_search_dates_filters_and_pagination(http_client, connection, office_token):
    for i in range(3):
        r = await post(http_client, connection, payload(website_reference=f'AG-90000{i}'))
        assert r.status_code == 201
    h = auth_headers(office_token)
    r = await http_client.get(OFFICE, headers=h, params={'limit': 2, 'offset': 0, 'status': 'new', 'q': 'AG-900'})
    assert r.json()['total'] == 3 and len(r.json()['items']) == 2
    ids = {item['id'] for item in r.json()['items']}
    r = await http_client.get(OFFICE, headers=h, params={'limit': 2, 'offset': 2})
    assert not ids & {item['id'] for item in r.json()['items']}
    assert (await http_client.get(OFFICE, headers=h, params={'q': '%'})).json()['total'] == 0
    assert (await http_client.get(OFFICE, headers=h, params={'date_from': '2026-12-01', 'date_to': '2026-01-01'})).status_code == 422
    assert (await http_client.get(OFFICE, headers=h, params={'limit': 1000})).status_code == 422
    assert (await http_client.get(OFFICE, headers=h, params={'date_to': '9999-12-31'})).status_code == 422


async def test_demoted_viewer_cannot_see_alerts_or_office_data(http_client, connection):
    async with AsyncSessionLocal() as db:
        office = (await db.execute(select(PermissionGroup).where(PermissionGroup.sysname == 'office_group'))).scalar_one()
        viewer = (await db.execute(select(PermissionGroup).where(PermissionGroup.sysname == 'viewer_group'))).scalar_one()
        user = User(username='__website_test_user', email='website-test@example.test', full_name='Тестовый офис', password_hash='unused', groups=[office])
        db.add(user); await db.commit()
        user_id = user.id
    token = create_token(str(user_id), user.email, ['office_group'])
    try:
        r = await post(http_client, connection, payload()); assert r.status_code == 201
        h = auth_headers(token)
        notifications = (await http_client.get('/api/notifications', headers=h)).json()
        alert = next(n for n in notifications if n['related_website_request_id'] == r.json()['id'])
        async with AsyncSessionLocal() as db:
            u = await db.get(User, user_id); u.groups = [await db.get(PermissionGroup, viewer.id)]; await db.commit()
        assert (await http_client.get(OFFICE, headers=h)).status_code == 403
        assert (await http_client.get(f"{OFFICE}/{r.json()['id']}", headers=h)).status_code == 403
        assert not (await http_client.get('/api/notifications', headers=h)).json()
        assert (await http_client.get('/api/notifications/unread-count', headers=h)).json()['count'] == 0
        assert (await http_client.put(f"/api/notifications/{alert['id']}/read", headers=h)).status_code == 404
    finally:
        async with AsyncSessionLocal() as db:
            await db.execute(delete(User).where(User.id == user_id)); await db.commit()


async def test_notification_ownership(http_client, received, office_token, admin_token):
    admin_alerts = (await http_client.get('/api/notifications', headers=auth_headers(admin_token))).json()
    alert = next(n for n in admin_alerts if n['related_website_request_id'] == received['id'])
    for action in ['read', 'unread']:
        assert (await http_client.put(f"/api/notifications/{alert['id']}/{action}", headers=auth_headers(office_token))).status_code == 404
