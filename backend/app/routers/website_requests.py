from datetime import date, datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo
import hashlib
import secrets
from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy import select, func, or_
from sqlalchemy.exc import IntegrityError
from app.dependencies import get_db, require_groups
from app.models.website_request import WebsiteRequest, WebsiteIntegrationConnection, utcnow
from app.models.user import User
from app.models.config_tables import PermissionGroup
from app.schemas.website_request import RequestUpdate, CommentInput, ConnectionInput, LinkInput, RequestStatus
from app.services import website_requests as service

router = APIRouter(prefix='/website-requests', tags=['website-requests'])
office = require_groups('admin_group', 'office_group')
admin = require_groups('admin_group')


@router.get('/assignees')
async def assignees(db=Depends(get_db), user=Depends(office)):
    users = (await db.execute(select(User).where(User.is_active == True,
        User.groups.any(PermissionGroup.sysname.in_(service.OFFICE))).order_by(User.full_name, User.id))).scalars().all()
    return [{'id': u.id, 'full_name': u.full_name} for u in users]


def connection_out(row):
    return {'id': row.id, 'label': row.label, 'created_at': row.created_at,
            'expires_at': row.expires_at, 'revoked': row.revoked}


@router.get('/connections')
async def connections(db=Depends(get_db), user=Depends(admin)):
    rows = (await db.execute(select(WebsiteIntegrationConnection).order_by(WebsiteIntegrationConnection.id.desc()))).scalars().all()
    return [connection_out(c) for c in rows]


@router.post('/connections', status_code=201)
async def create_connection(body: ConnectionInput, response: Response, db=Depends(get_db), user=Depends(admin)):
    if not body.label.strip():
        raise HTTPException(422, 'Укажите название подключения')
    token = 'ssw_' + secrets.token_urlsafe(32)
    row = WebsiteIntegrationConnection(token_hash=hashlib.sha256(token.encode()).hexdigest(),
        label=body.label.strip(), created_by=user.id, expires_at=utcnow() + timedelta(days=body.expires_days))
    db.add(row)
    await db.commit()
    response.headers['Cache-Control'] = 'no-store'
    return {**connection_out(row), 'token': token}


@router.delete('/connections/{connection_id}', status_code=204)
async def revoke_connection(connection_id: int, db=Depends(get_db), user=Depends(admin)):
    row = await db.get(WebsiteIntegrationConnection, connection_id)
    if row is None:
        raise HTTPException(404, 'Подключение не найдено')
    row.revoked = True
    await db.commit()


@router.get('')
async def requests_list(
    status: RequestStatus | None = None, assigned_user_id: int | None = None,
    service_category: str | None = Query(None, pattern='^(boiler|gas|heat|other)$'),
    date_from: date | None = None, date_to: date | None = None,
    q: str = Query('', max_length=200, pattern=r'^[^\x00]*$'), limit: int = Query(50, ge=1, le=100), offset: int = Query(0, ge=0),
    db=Depends(get_db), user=Depends(office),
):
    if date_from and date_to and date_to < date_from:
        raise HTTPException(422, 'Конец периода раньше начала')
    if date_to == date.max:
        raise HTTPException(422, 'Дата вне поддерживаемого диапазона')
    conditions = []
    if status:
        conditions.append(WebsiteRequest.status == status)
    if assigned_user_id is not None:
        conditions.append(WebsiteRequest.assigned_user_id == assigned_user_id if assigned_user_id else WebsiteRequest.assigned_user_id.is_(None))
    if service_category:
        conditions.append(WebsiteRequest.service_category == service_category)
    moscow = ZoneInfo('Europe/Moscow')
    if date_from:
        conditions.append(WebsiteRequest.received_at >= datetime.combine(date_from, time.min, moscow).astimezone(timezone.utc))
    if date_to:
        conditions.append(WebsiteRequest.received_at < datetime.combine(date_to + timedelta(days=1), time.min, moscow).astimezone(timezone.utc))
    if q.strip():
        needle = '%' + q.strip().replace('\\', '\\\\').replace('%', '\\%').replace('_', '\\_') + '%'
        fields = [WebsiteRequest.website_reference, WebsiteRequest.phone, WebsiteRequest.contact_name, WebsiteRequest.company_name,
                  WebsiteRequest.working_data['phone'].astext, WebsiteRequest.working_data['contact_name'].astext,
                  WebsiteRequest.working_data['company_name'].astext]
        conditions.append(or_(*(field.ilike(needle, escape='\\') for field in fields)))
    total = (await db.execute(select(func.count()).select_from(WebsiteRequest).where(*conditions))).scalar_one()
    rows = (await db.execute(select(WebsiteRequest, User.full_name).outerjoin(User, WebsiteRequest.assigned_user_id == User.id)
                            .where(*conditions).order_by(WebsiteRequest.received_at.desc(), WebsiteRequest.id.desc())
                            .limit(limit).offset(offset))).all()
    return {'items': [service.summary(row, name) for row, name in rows], 'total': total}


@router.get('/{request_id}')
async def request_detail(request_id: int, db=Depends(get_db), user=Depends(office)):
    return await service.detail(db, await service.load(db, request_id))


@router.patch('/{request_id}')
async def update_request(request_id: int, body: RequestUpdate, db=Depends(get_db), user=Depends(office)):
    row = await service.load(db, request_id, lock=True)
    await service.update(db, row, body, user)
    await db.commit()
    return await service.detail(db, row)


@router.post('/{request_id}/comments', status_code=201)
async def comment(request_id: int, body: CommentInput, db=Depends(get_db), user=Depends(office)):
    row = await service.load(db, request_id, lock=True)
    service.event(db, row, 'comment', user, {'text': body.text})
    row.updated_at = utcnow()
    await db.commit()
    return await service.detail(db, row)


@router.post('/{request_id}/link')
async def link_request(request_id: int, body: LinkInput, db=Depends(get_db), user=Depends(office)):
    row = await service.load(db, request_id, lock=True)
    try:
        result = await service.link(db, row, body, user)
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(409, 'Команда уже использована. Обновите карточку.') from None
    return result
