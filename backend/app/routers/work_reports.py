"""Completed reports, human review and scoped access for the desktop MCP bridge."""
import hashlib
import secrets
from datetime import date, datetime, timedelta, timezone
from typing import Literal
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, Field
from sqlalchemy import select, func, or_, exists, cast, String
from sqlalchemy.ext.asyncio import AsyncSession
from app.dependencies import get_db, get_current_user, require_groups
from app.models.visit import Visit
from app.models.site import Site
from app.models.user import User
from app.models.defect import Defect
from app.models.work_report import VisitReview, ReportProposal, ReportConnection
from app.routers.visits import _build_visit_query, _row_to_visit_out
from app.services.work_reports import ProposalInput, SOURCE_FIELDS, SOURCE_LABELS, report_hash, report_snapshot, validate_source, proposal_key, possible_duplicates
from app.utils.audit import save_log
from app.enums import enums

router = APIRouter(prefix='/work-reports', tags=['work-reports'])
human = require_groups('admin_group', 'office_group')


async def report_user(request: Request, db: AsyncSession = Depends(get_db)):
    header = request.headers.get('Authorization', '')
    token = header.removeprefix('Bearer ')
    if token.startswith('ssr_') and header.startswith('Bearer '):
        row = (await db.execute(select(ReportConnection).where(
            ReportConnection.token_hash == hashlib.sha256(token.encode()).hexdigest(),
            ReportConnection.revoked == False,
            ReportConnection.expires_at > datetime.now(timezone.utc)))).scalar_one_or_none()
        if not row:
            raise HTTPException(401, 'Подключение истекло или отозвано')
        user = (await db.execute(select(User).where(User.id == row.user_id, User.is_active == True))).scalar_one_or_none()
    else:
        user = await get_current_user(request, db)
    if not user or not {g.sysname for g in user.groups}.intersection({'admin_group', 'office_group'}):
        raise HTTPException(403, 'Доступ только для офиса и администратора')
    return user


async def load_visit(db, visit_id, lock=False):
    stmt = select(Visit).where(Visit.id == visit_id)
    if lock:
        stmt = stmt.with_for_update()
    visit = (await db.execute(stmt)).scalar_one_or_none()
    if not visit:
        raise HTTPException(404, 'Выезд не найден')
    if visit.status != 'done' or visit.is_archived:
        raise HTTPException(409, 'Нужен выполненный неархивный выезд')
    return visit


def proposal_out(p, visit, defects):
    return {'id': p.id, **p.data, 'status': p.status, 'source': p.source, 'defect_id': p.defect_id,
            'stale': p.report_hash != report_hash(visit),
            'possible_duplicate_ids': possible_duplicates(p.data['title'], defects)}


async def enrich(db, rows):
    visits = [_row_to_visit_out(row) for row in rows]
    ids = [v.id for v in visits]
    sites = [v.site_id for v in visits if v.site_id]
    defects = (await db.execute(select(Defect).where(Defect.site_id.in_(sites)))).scalars().all() if sites else []
    proposals = (await db.execute(select(ReportProposal).where(ReportProposal.visit_id.in_(ids)).order_by(ReportProposal.id))).scalars().all() if ids else []
    reviews = (await db.execute(select(VisitReview).where(VisitReview.visit_id.in_(ids)))).scalars().all() if ids else []
    result = []
    for v in visits:
        site_defects = [d for d in defects if d.site_id == v.site_id]
        fingerprint = report_hash(v)
        review = next((r for r in reviews if r.visit_id == v.id), None)
        result.append({'id': v.id, 'site_id': v.site_id, 'site_title': v.site_title,
            'site_address': v.site_address, 'client_name': v.client_name, 'planned_date': v.planned_date,
            'master_names': v.master_names or ([v.master_name] if v.master_name else []),
            **{field: getattr(v, field) for field in SOURCE_FIELDS}, 'defects_present': v.defects_present,
            'act_photos_count': v.act_photos_count, 'report_hash': fingerprint,
            'reviewed': bool(review and review.report_hash == fingerprint),
            'review_notes': review.notes if review and review.report_hash == fingerprint else '',
            'review_changed': bool(review and review.report_hash != fingerprint),
            'defects': [{'id': d.id, 'visit_id': d.visit_id, 'title': d.title, 'description': d.description,
                         'status': d.status} for d in site_defects],
            'proposals': [proposal_out(p, v, site_defects) for p in proposals if p.visit_id == v.id]})
    return result


@router.get('')
async def list_reports(date_from: date | None = None, date_to: date | None = None,
                       site_id: int | None = None, master_id: int | None = None,
                       review: Literal['all', 'reviewed', 'unreviewed'] = 'all',
                       q: str = Query('', max_length=200), limit: int = Query(20, ge=1, le=100),
                       offset: int = Query(0, ge=0), db: AsyncSession = Depends(get_db), user=Depends(report_user)):
    if date_from and date_to and date_to < date_from:
        raise HTTPException(422, 'Дата окончания раньше даты начала')
    stmt = _build_visit_query(master_id, site_id, 'done', date_from, date_to).where(Visit.is_archived == False)
    if q.strip():
        text = '%' + q.replace('\\', '\\\\').replace('%', '\\%').replace('_', '\\_') + '%'
        stmt = stmt.where(or_(*(getattr(Visit, f).ilike(text, escape='\\') for f in SOURCE_FIELDS), Site.title.ilike(text, escape='\\')))
    if review != 'all':
        snapshot = func.jsonb_build_object(
            'work_summary', func.coalesce(Visit.work_summary, ''),
            'defects_summary', func.coalesce(Visit.defects_summary, ''),
            'recommendations', func.coalesce(Visit.recommendations, ''),
            'site_id', Visit.site_id, 'status', Visit.status,
            'is_archived', Visit.is_archived, 'planned_date', cast(Visit.planned_date, String))
        checked = exists().where(VisitReview.visit_id == Visit.id, VisitReview.snapshot == snapshot)
        stmt = stmt.where(checked if review == 'reviewed' else ~checked)
    total = (await db.execute(select(func.count()).select_from(stmt.subquery()))).scalar() or 0
    rows = (await db.execute(stmt.order_by(Visit.planned_date.desc(), Visit.id.desc()).offset(offset).limit(limit))).all()
    return {'items': await enrich(db, rows), 'total': total, 'limit': limit, 'offset': offset}


@router.post('/proposals')
async def propose(body: ProposalInput, request: Request, db: AsyncSession = Depends(get_db), user=Depends(report_user)):
    visit = await load_visit(db, body.visit_id, lock=True)
    if not visit.site_id:
        raise HTTPException(409, 'У выезда отсутствует объект')
    try:
        validate_source(visit, body)
    except ValueError as exc:
        raise HTTPException(409, str(exc)) from exc
    key = proposal_key(body)
    existing = (await db.execute(select(ReportProposal).where(ReportProposal.proposal_key == key))).scalar_one_or_none()
    if existing:
        return {'proposal_id': existing.id, 'status': existing.status}
    source = 'chat' if request.headers.get('Authorization', '').startswith('Bearer ssr_') else 'manual'
    proposal = ReportProposal(visit_id=visit.id, report_hash=body.report_hash, proposal_key=key,
                              data=body.model_dump(), source=source, created_by=user.id)
    db.add(proposal)
    await db.flush()
    await save_log(db, user.id, 'report_proposal_create', 'report_proposal', proposal.id,
                   details={'stage': 'proposal', 'source': source, 'visit_id': visit.id})
    await db.commit()
    return {'proposal_id': proposal.id, 'status': proposal.status}


@router.post('/proposals/{proposal_id}/confirm')
async def confirm(proposal_id: int, db: AsyncSession = Depends(get_db), user=Depends(human)):
    p = (await db.execute(select(ReportProposal).where(ReportProposal.id == proposal_id).with_for_update())).scalar_one_or_none()
    if not p:
        raise HTTPException(404, 'Предложение не найдено')
    if p.status == 'created' and p.defect_id:
        return {'created': False, 'defect_id': p.defect_id}
    if p.status != 'pending':
        raise HTTPException(409, 'Предложение уже обработано')
    visit = await load_visit(db, p.visit_id, lock=True)
    body = ProposalInput.model_validate(p.data)
    try:
        validate_source(visit, body)
    except ValueError as exc:
        raise HTTPException(409, str(exc)) from exc
    if not visit.site_id:
        raise HTTPException(409, 'У выезда отсутствует объект')
    await db.execute(select(Site).where(Site.id == visit.site_id).with_for_update())
    defects = (await db.execute(select(Defect).where(Defect.site_id == visit.site_id))).scalars().all()
    duplicates = possible_duplicates(body.title, defects)
    if duplicates:
        raise HTTPException(409, f'Найден похожий дефект №{duplicates[0]}. Проверьте его и отклоните повтор.')
    label = 'Создано с помощью ИИ; подтверждено пользователем.' if p.source == 'chat' else 'Создано из итога выезда; подтверждено пользователем.'
    description = f'{body.description}\n\n{label}\nВыезд №{visit.id}, {visit.planned_date}. {SOURCE_LABELS[body.source_field]}:\n«{body.source_quote}»'
    if body.review_reason:
        description += '\nПримечание: ' + body.review_reason
    defect = Defect(visit_id=visit.id, site_id=visit.site_id, title=body.title, description=description,
                    priority=body.priority, action_type=body.action_type, suggested_parts=body.suggested_parts or None)
    db.add(defect)
    await db.flush()
    p.status, p.defect_id = 'created', defect.id
    await save_log(db, user.id, enums.log_actions.defect_create, 'defect', defect.id,
                   details={'source': p.source, 'proposal_id': p.id, 'visit_id': visit.id,
                            'source_quote': body.source_quote, 'proposed_by': p.created_by})
    await db.commit()
    return {'created': True, 'defect_id': defect.id}


@router.post('/proposals/{proposal_id}/dismiss')
async def dismiss(proposal_id: int, db: AsyncSession = Depends(get_db), user=Depends(human)):
    p = (await db.execute(select(ReportProposal).where(ReportProposal.id == proposal_id).with_for_update())).scalar_one_or_none()
    if not p:
        raise HTTPException(404, 'Предложение не найдено')
    if p.status != 'pending':
        raise HTTPException(409, 'Предложение уже обработано')
    p.status = 'dismissed'
    await save_log(db, user.id, 'report_proposal_dismiss', 'report_proposal', p.id)
    await db.commit()
    return {'status': p.status}


class ReviewInput(BaseModel):
    report_hash: str = Field(pattern=r'^[a-f0-9]{64}$')
    notes: str = Field(default='', max_length=3000)
    reviewed: bool = True


@router.put('/{visit_id}/review')
async def mark_review(visit_id: int, body: ReviewInput, db: AsyncSession = Depends(get_db), user=Depends(human)):
    visit = await load_visit(db, visit_id, lock=True)
    if body.report_hash != report_hash(visit):
        raise HTTPException(409, 'Отчёт изменился. Обновите страницу перед отметкой.')
    review = (await db.execute(select(VisitReview).where(VisitReview.visit_id == visit_id))).scalar_one_or_none()
    if not body.reviewed:
        if review:
            await db.delete(review)
    else:
        if not review:
            review = VisitReview(visit_id=visit_id)
            db.add(review)
        review.snapshot = report_snapshot(visit)
        review.report_hash, review.notes, review.reviewed_by = body.report_hash, body.notes, user.id
        review.reviewed_at = datetime.now(timezone.utc)
    await save_log(db, user.id, 'report_review', 'visit', visit_id, details={'reviewed': body.reviewed})
    await db.commit()
    return {'reviewed': body.reviewed}


@router.get('/connections')
async def connections(db: AsyncSession = Depends(get_db), user=Depends(human)):
    rows = (await db.execute(select(ReportConnection).where(ReportConnection.user_id == user.id).order_by(ReportConnection.id.desc()))).scalars().all()
    return [{'id': r.id, 'created_at': r.created_at, 'expires_at': r.expires_at, 'revoked': r.revoked} for r in rows]


@router.post('/connections')
async def connect(db: AsyncSession = Depends(get_db), user=Depends(human)):
    token = 'ssr_' + secrets.token_urlsafe(32)
    row = ReportConnection(user_id=user.id, token_hash=hashlib.sha256(token.encode()).hexdigest(),
                           expires_at=datetime.now(timezone.utc) + timedelta(days=30))
    db.add(row)
    await db.flush()
    await save_log(db, user.id, 'report_connection_create', 'report_connection', row.id)
    await db.commit()
    return {'id': row.id, 'token': token, 'expires_at': row.expires_at,
            'capabilities': ['read_completed_reports', 'read_site_defects', 'prepare_proposals']}


@router.delete('/connections/{connection_id}')
async def revoke(connection_id: int, db: AsyncSession = Depends(get_db), user=Depends(human)):
    row = (await db.execute(select(ReportConnection).where(ReportConnection.id == connection_id,
                                                         ReportConnection.user_id == user.id))).scalar_one_or_none()
    if not row:
        raise HTTPException(404, 'Подключение не найдено')
    row.revoked = True
    await save_log(db, user.id, 'report_connection_revoke', 'report_connection', row.id)
    await db.commit()
    return {'revoked': True}


@router.get('/{visit_id}')
async def get_report(visit_id: int, db: AsyncSession = Depends(get_db), user=Depends(report_user)):
    await load_visit(db, visit_id)
    rows = (await db.execute(_build_visit_query().where(Visit.id == visit_id))).all()
    return (await enrich(db, rows))[0]
