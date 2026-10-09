"""Transactional intake and office workflow. No browser or report-bridge access."""
import hashlib
import json
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from app.models.website_request import WebsiteRequest, WebsiteRequestEvent, WebsiteRequestCommand, utcnow
from app.models.notification import Notification
from app.models.user import User
from app.models.config_tables import PermissionGroup
from app.models.client import Client
from app.models.client_contact import ClientContact
from app.models.site import Site
from app.models.log import Log
from app.models.history import ClientHistory, SiteHistory
from app.utils.audit import save_history, save_log

OFFICE = {'admin_group', 'office_group'}


def payload_hash(data):
    return hashlib.sha256(json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def event(db, row, kind, user=None, data=None):
    db.add(WebsiteRequestEvent(request_id=row.id, kind=kind, user_id=user.id if user else None,
                              author_name=user.full_name if user else 'Сайт', data=data or {}))
    db.add(Log(user_id=user.id if user else None, action_sysname='website_request_event',
               entity_type='website_request', entity_id=row.id, details={'kind': kind}))


async def receive(db, body, original_payload=None):
    canonical = body.model_dump(mode='json')
    snapshot = original_payload if original_payload is not None else canonical
    fingerprint = payload_hash(canonical)
    now = utcnow()
    result = await db.execute(insert(WebsiteRequest).values(
        external_id=body.external_id, website_reference=body.website_reference,
        submitted_at=body.submitted_at, received_at=now, updated_at=now,
        payload=snapshot, payload_hash=fingerprint, phone=body.phone,
        contact_name=body.contact_name, company_name=body.company_name,
        service_category=body.service_category, work_type=body.work_type,
        status='new', version=1, working_data={},
    ).on_conflict_do_nothing(index_elements=['external_id']).returning(WebsiteRequest.id))
    new_id = result.scalar_one_or_none()
    row = (await db.execute(select(WebsiteRequest).where(WebsiteRequest.external_id == body.external_id))).scalar_one()
    if new_id is None:
        if row.payload_hash != fingerprint:
            raise HTTPException(409, 'Этот external_id уже принят с другими данными')
        return row, False
    event(db, row, 'received')
    users = (await db.execute(select(User.id).where(User.is_active == True,
        User.groups.any(PermissionGroup.sysname.in_(OFFICE))))).scalars().all()
    for user_id in users:
        db.add(Notification(user_id=user_id, type='website_request_new', title='Новая заявка с сайта',
            message=f'Получено обращение {row.website_reference}', related_website_request_id=row.id))
    return row, True


async def load(db, request_id, lock=False):
    stmt = select(WebsiteRequest).where(WebsiteRequest.id == request_id)
    if lock:
        stmt = stmt.with_for_update()
    row = (await db.execute(stmt)).scalar_one_or_none()
    if row is None:
        raise HTTPException(404, 'Заявка не найдена')
    return row


async def eligible_user(db, user_id):
    user = (await db.execute(select(User).where(User.id == user_id, User.is_active == True,
        User.groups.any(PermissionGroup.sysname.in_(OFFICE))))).scalar_one_or_none()
    if user is None:
        raise HTTPException(422, 'Ответственный должен быть активным сотрудником офиса или администратором')
    return user


def check_version(row, version):
    if row.version != version:
        raise HTTPException(409, 'Заявка изменена другим сотрудником. Обновите карточку и проверьте изменения.')


async def update(db, row, body, user):
    check_version(row, body.version)
    changes = body.model_dump(exclude_unset=True, mode='json')
    changes.pop('version')
    if 'assigned_user_id' in changes and changes['assigned_user_id'] is not None:
        await eligible_user(db, changes['assigned_user_id'])
    outcome = changes.get('outcome', row.outcome)
    if changes.get('status', row.status) == 'closed' and not (outcome or '').strip():
        raise HTTPException(422, 'Укажите итог обращения перед закрытием')
    if 'outcome' in changes and outcome is not None:
        changes['outcome'] = outcome.strip() or None
    changes = {key: value for key, value in changes.items() if getattr(row, key) != value}
    if changes:
        before = {key: getattr(row, key) for key in changes}
        for key, value in changes.items():
            setattr(row, key, value)
        row.version += 1
        row.updated_at = utcnow()
        event(db, row, 'updated', user, {'before': before, 'after': changes})
    return row


async def active_entity(db, model, entity_id):
    # Lock selected records so archive/delete cannot race validation and linking.
    obj = (await db.execute(select(model).where(model.id == entity_id).with_for_update())).scalar_one_or_none()
    if obj is None or getattr(obj, 'is_archived', False) or not getattr(obj, 'is_active', True):
        raise HTTPException(422, 'Выбранная запись недоступна. Проверьте клиента, контакт и объект.')
    return obj


def required_text(value):
    if not value.strip():
        raise HTTPException(422, 'Название, имя и адрес не могут состоять из пробелов')
    return value.strip()


async def link(db, row, body, user):
    data = body.model_dump(mode='json')
    fingerprint = payload_hash(data)
    previous = await db.get(WebsiteRequestCommand, body.command_id)
    if previous:
        if previous.request_id != row.id or previous.payload_hash != fingerprint:
            raise HTTPException(409, 'Команда уже использована с другими данными')
        return previous.result
    check_version(row, body.version)
    if row.client_id and body.new_client:
        raise HTTPException(409, 'Клиент уже связан. Выберите существующего клиента.')
    client = await active_entity(db, Client, body.client_id) if body.client_id else Client(name=required_text(body.new_client.name))
    if not body.client_id:
        db.add(client)
        await db.flush()
        await save_history(db, ClientHistory, client, user.id, 'create')
        await save_log(db, user.id, 'client_create', 'client', client.id, {'source_request_id': row.id})
    contact = None
    if body.contact_id:
        contact = await active_entity(db, ClientContact, body.contact_id)
        if contact.client_id != client.id:
            raise HTTPException(422, 'Контакт принадлежит другому клиенту')
    elif body.new_contact:
        contact = ClientContact(client_id=client.id, full_name=required_text(body.new_contact.contact_name),
                                phone=body.new_contact.phone, email=body.new_contact.email, is_primary=False)
        db.add(contact)
        await db.flush()
    site = None
    if body.site_id:
        site = await active_entity(db, Site, body.site_id)
        if site.client_id != client.id:
            raise HTTPException(422, 'Объект принадлежит другому клиенту')
    elif body.new_site:
        site = Site(client_id=client.id, title=required_text(body.new_site.title), address=required_text(body.new_site.address))
        db.add(site)
        await db.flush()
        await save_history(db, SiteHistory, site, user.id, 'create')
        await save_log(db, user.id, 'site_create', 'site', site.id, {'source_request_id': row.id})
    before = {key: getattr(row, key) for key in ('client_id', 'contact_id', 'site_id')}
    row.client_id, row.contact_id, row.site_id = client.id, contact.id if contact else None, site.id if site else None
    row.version += 1
    row.updated_at = utcnow()
    result = {'client_id': row.client_id, 'contact_id': row.contact_id, 'site_id': row.site_id, 'version': row.version}
    event(db, row, 'linked', user, {'before': before, 'after': result})
    db.add(WebsiteRequestCommand(id=body.command_id, request_id=row.id, payload_hash=fingerprint, result=result))
    return result


def summary(row, assigned_name=None):
    working = row.working_data
    return {'id': row.id, 'external_id': str(row.external_id), 'website_reference': row.website_reference,
            'received_at': row.received_at, 'submitted_at': row.submitted_at, 'updated_at': row.updated_at,
            'phone': working.get('phone') or row.phone, 'contact_name': working.get('contact_name') or row.contact_name,
            'company_name': working.get('company_name') or row.company_name,
            'service_category': row.service_category, 'work_type': row.work_type,
            'request_mode': row.payload['request_mode'], 'request_intent': row.payload['request_intent'],
            'status': row.status, 'assigned_user_id': row.assigned_user_id, 'assigned_name': assigned_name,
            'version': row.version, 'client_id': row.client_id, 'contact_id': row.contact_id, 'site_id': row.site_id}


async def detail(db, row):
    assigned = await db.get(User, row.assigned_user_id) if row.assigned_user_id else None
    result = summary(row, assigned.full_name if assigned else None)
    events = (await db.execute(select(WebsiteRequestEvent).where(WebsiteRequestEvent.request_id == row.id)
                              .order_by(WebsiteRequestEvent.created_at, WebsiteRequestEvent.id))).scalars().all()
    result.update(payload=row.payload, working_data=row.working_data, outcome=row.outcome,
        events=[{'id': e.id, 'kind': e.kind, 'author_name': e.author_name, 'data': e.data, 'created_at': e.created_at} for e in events])
    result['links'] = {}
    for key, model, entity_id in [('client', Client, row.client_id), ('site', Site, row.site_id), ('contact', ClientContact, row.contact_id)]:
        obj = await db.get(model, entity_id) if entity_id else None
        if obj:
            result['links'][key] = {'id': obj.id, 'name': getattr(obj, 'name', None) or getattr(obj, 'title', None) or obj.full_name}
    return result
