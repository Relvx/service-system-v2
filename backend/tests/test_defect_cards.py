from datetime import date
import pytest
import pytest_asyncio
from sqlalchemy import select, func
from app.database import AsyncSessionLocal
from app.models.defect import DefectComment
from app.models.log import Log
from tests.conftest import auth_headers


@pytest_asyncio.fixture
async def card(http_client, admin_token, site_id):
    headers = auth_headers(admin_token)
    visit = await http_client.post('/api/visits', headers=headers, json={
        'planned_date': str(date.today()), 'site_id': site_id,
        'visit_type': 'maintenance', 'priority': 'medium'})
    assert visit.status_code == 201, visit.text
    created = await http_client.post('/api/defects', headers=headers, json={
        'title': '__test__ card', 'site_id': site_id, 'visit_id': visit.json()['id']})
    assert created.status_code == 201
    yield created.json()
    await http_client.delete(f"/api/defects/{created.json()['id']}", headers=headers)
    await http_client.delete(f"/api/visits/{visit.json()['id']}", headers=headers)


async def test_card_links_and_edit(http_client, admin_token, card):
    headers = auth_headers(admin_token)
    assert card['client_id'] and card['visit_id'] and card['client_name']
    change = {'title': 'Новое название', 'description': 'Новое описание',
              'priority': 'urgent', 'action_type': 'replace', 'suggested_parts': 'Насос'}
    updated = await http_client.put(f"/api/defects/{card['id']}", headers=headers, json=change)
    assert updated.status_code == 200, updated.text
    fresh = (await http_client.get(f"/api/defects/{card['id']}", headers=headers)).json()
    assert all(fresh[k] == v for k, v in change.items())
    assert fresh['client_id'] == card['client_id'] and fresh['visit_id'] == card['visit_id']


async def test_comments_author_persistence_isolation_and_cascade(http_client, admin_token, office_token, card):
    url = f"/api/defects/{card['id']}/comments"
    assert (await http_client.get(url, headers=auth_headers(admin_token))).json() == []
    for token, message in [(admin_token, ' Первый комментарий '), (office_token, 'Второй комментарий')]:
        res = await http_client.post(url, headers=auth_headers(token), json={'text': message})
        assert res.status_code == 201, res.text
        author = (await http_client.get('/api/auth/me', headers=auth_headers(token))).json()
        assert res.json()['user_id'] == author['id']
        assert res.json()['author_name'] == author['full_name']
        assert res.json()['text'] == message.strip()
    comments = (await http_client.get(url, headers=auth_headers(admin_token))).json()
    assert [c['text'] for c in comments] == ['Первый комментарий', 'Второй комментарий']
    other = await http_client.post('/api/defects', headers=auth_headers(admin_token), json={'title': '__test__ other'})
    other_id = other.json()['id']
    try:
        assert other.json()['client_id'] is None
        assert (await http_client.get(f'/api/defects/{other_id}/comments', headers=auth_headers(admin_token))).json() == []
    finally:
        await http_client.delete(f'/api/defects/{other_id}', headers=auth_headers(admin_token))
    async with AsyncSessionLocal() as db:
        logs = (await db.execute(select(Log).where(Log.entity_id == card['id'], Log.action_sysname == 'defect_comment_create'))).scalars().all()
        assert len(logs) == 2
    await http_client.delete(f"/api/defects/{card['id']}", headers=auth_headers(admin_token))
    async with AsyncSessionLocal() as db:
        assert (await db.execute(select(func.count()).select_from(DefectComment).where(DefectComment.defect_id == card['id']))).scalar() == 0


@pytest.mark.parametrize('text', ['', '   ', 'x' * 10001])
async def test_invalid_comment(http_client, admin_token, card, text):
    assert (await http_client.post(f"/api/defects/{card['id']}/comments", headers=auth_headers(admin_token), json={'text': text})).status_code == 422


async def test_comments_access_and_missing_defect(http_client, admin_token, master_token, card):
    url = f"/api/defects/{card['id']}/comments"
    assert (await http_client.get(url)).status_code == 401
    assert (await http_client.post(url, json={'text': 'test'})).status_code == 401
    assert (await http_client.post(url, headers=auth_headers(master_token), json={'text': 'test'})).status_code == 403
    for method in ('get', 'post'):
        kwargs = {'json': {'text': 'test'}} if method == 'post' else {}
        assert (await getattr(http_client, method)('/api/defects/999999999/comments', headers=auth_headers(admin_token), **kwargs)).status_code == 404
