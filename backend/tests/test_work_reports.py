from datetime import date, datetime, timedelta, timezone
from uuid import uuid4

import pytest_asyncio
from sqlalchemy import select
from app.database import AsyncSessionLocal
from app.models.work_report import ReportConnection
from tests.conftest import auth_headers


@pytest_asyncio.fixture
async def report(http_client, admin_token, site_id, admin_user_id):
    headers = auth_headers(admin_token)
    created = await http_client.post('/api/visits', headers=headers, json={
        'planned_date': str(date.today()), 'site_id': site_id,
        'assigned_user_id': admin_user_id, 'visit_type': 'maintenance', 'priority': 'medium'})
    assert created.status_code == 201, created.text
    visit_id = created.json()['id']
    quote = 'Неисправен насос ' + uuid4().hex
    completed = await http_client.post(f'/api/visits/{visit_id}/complete', headers=headers,
        json={'work_summary': quote, 'recommendations': 'Нужна замена насоса', 'defects_present': True})
    assert completed.status_code == 200, completed.text
    response = await http_client.get(f'/api/work-reports/{visit_id}', headers=headers)
    assert response.status_code == 200, response.text
    yield response.json()
    await http_client.delete(f'/api/visits/{visit_id}', headers=headers)


def proposal(report, **extra):
    return {'visit_id': report['id'], 'report_hash': report['report_hash'],
            'title': report['work_summary'], 'source_field': 'work_summary',
            'source_quote': report['work_summary'], **extra}


async def test_done_filter_and_access(http_client, admin_token, master_token, report):
    headers = auth_headers(admin_token)
    cfg = (await http_client.get('/api/config/visit-statuses', headers=headers)).json()
    assert any(s['sysname'] == 'done' and s['display_name'] == 'Завершён' for s in cfg)
    assert not any(s['sysname'] == 'closed' for s in cfg)
    rows = (await http_client.get('/api/visits', headers=headers, params={'status': 'done'})).json()['items']
    assert any(v['id'] == report['id'] for v in rows)
    assert all(v['status'] == 'done' for v in rows)
    rows = (await http_client.get('/api/work-reports', headers=headers, params={'q': report['work_summary']})).json()
    assert rows['total'] == 1 and rows['items'][0]['id'] == report['id']
    assert (await http_client.get('/api/work-reports')).status_code == 401
    assert (await http_client.get('/api/work-reports', headers=auth_headers(master_token))).status_code == 403


async def test_proposal_quote_idempotency_and_creation(http_client, admin_token, report):
    headers = auth_headers(admin_token)
    invalid = await http_client.post('/api/work-reports/proposals', headers=headers,
                                     json=proposal(report, source_quote='Выдуманная неисправность'))
    assert invalid.status_code == 409
    invalid = await http_client.post('/api/work-reports/proposals', headers=headers,
                                     json=proposal(report, report_hash='0' * 64))
    assert invalid.status_code == 409
    response = await http_client.post('/api/work-reports/proposals', headers=headers, json=proposal(report))
    assert response.status_code == 200, response.text
    pid = response.json()['proposal_id']
    again = await http_client.post('/api/work-reports/proposals', headers=headers, json=proposal(report))
    assert again.json()['proposal_id'] == pid
    before = (await http_client.get(f"/api/work-reports/{report['id']}", headers=headers)).json()
    assert not any(d['title'] == report['work_summary'] for d in before['defects'])
    assert before['proposals'][0]['status'] == 'pending'
    confirmed = await http_client.post(f'/api/work-reports/proposals/{pid}/confirm', headers=headers)
    assert confirmed.status_code == 200, confirmed.text
    did = confirmed.json()['defect_id']
    assert confirmed.json()['created']
    again = await http_client.post(f'/api/work-reports/proposals/{pid}/confirm', headers=headers)
    assert again.json() == {'created': False, 'defect_id': did}
    defect = (await http_client.get(f'/api/defects/{did}', headers=headers)).json()
    assert report['work_summary'] in defect['description'] and defect['visit_id'] == report['id']
    another = await http_client.post('/api/work-reports/proposals', headers=headers,
                                     json=proposal(report, description='Повторное предложение'))
    rejected = await http_client.post(f"/api/work-reports/proposals/{another.json()['proposal_id']}/confirm", headers=headers)
    assert rejected.status_code == 409


async def test_changed_report_requires_new_review(http_client, admin_token, report):
    headers = auth_headers(admin_token)
    params = {'q': report['work_summary'], 'review': 'unreviewed'}
    assert (await http_client.get('/api/work-reports', headers=headers, params=params)).json()['total'] == 1
    marked = await http_client.put(f"/api/work-reports/{report['id']}/review", headers=headers,
        json={'report_hash': report['report_hash'], 'notes': 'Проверено вручную'})
    assert marked.status_code == 200, marked.text
    assert (await http_client.get('/api/work-reports', headers=headers, params=params)).json()['total'] == 0
    params['review'] = 'reviewed'
    assert (await http_client.get('/api/work-reports', headers=headers, params=params)).json()['total'] == 1
    pending = await http_client.post('/api/work-reports/proposals', headers=headers, json=proposal(report))
    changed = await http_client.put(f"/api/visits/{report['id']}", headers=headers,
                                    json={'work_summary': report['work_summary'] + '. Насос заменён.'})
    assert changed.status_code == 200
    rejected = await http_client.post(f"/api/work-reports/proposals/{pending.json()['proposal_id']}/confirm", headers=headers)
    assert rejected.status_code == 409
    assert (await http_client.get('/api/work-reports', headers=headers, params=params)).json()['total'] == 0
    current = (await http_client.get(f"/api/work-reports/{report['id']}", headers=headers)).json()
    assert current['review_changed'] and not current['reviewed']


async def test_scoped_connection_revocation_expiration(http_client, admin_token, report):
    headers = auth_headers(admin_token)
    conn = (await http_client.post('/api/work-reports/connections', headers=headers)).json()
    scoped = auth_headers(conn['token'])
    assert (await http_client.get('/api/work-reports', headers=scoped)).status_code == 200
    proposed = await http_client.post('/api/work-reports/proposals', headers=scoped, json=proposal(report))
    assert proposed.status_code == 200
    pid = proposed.json()['proposal_id']
    assert (await http_client.post(f'/api/work-reports/proposals/{pid}/confirm', headers=scoped)).status_code == 401
    assert (await http_client.post('/api/work-reports/connections', headers=scoped)).status_code == 401
    assert (await http_client.get('/api/visits', headers=scoped)).status_code == 401
    current = (await http_client.get(f"/api/work-reports/{report['id']}", headers=headers)).json()
    assert current['proposals'][0]['source'] == 'chat'
    await http_client.delete(f"/api/work-reports/connections/{conn['id']}", headers=headers)
    assert (await http_client.get('/api/work-reports', headers=scoped)).status_code == 401
    expired = (await http_client.post('/api/work-reports/connections', headers=headers)).json()
    async with AsyncSessionLocal() as db:
        row = (await db.execute(select(ReportConnection).where(ReportConnection.id == expired['id']))).scalar_one()
        row.expires_at = datetime.now(timezone.utc) - timedelta(seconds=1)
        await db.commit()
    assert (await http_client.get('/api/work-reports', headers=auth_headers(expired['token']))).status_code == 401
