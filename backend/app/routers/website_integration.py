import hashlib
import json
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from app.dependencies import get_db
from app.models.website_request import WebsiteIntegrationConnection, utcnow
from app.schemas.website_request import WebsiteIntake
from app.services.website_requests import receive

router = APIRouter(prefix='/integrations/website', tags=['website-integration'])
MAX_BYTES = 32768


async def intake_connection(request: Request, db=Depends(get_db)):
    authorization = request.headers.get('Authorization', '')
    if not authorization.startswith('Bearer ssw_') or len(authorization) > 200:
        raise HTTPException(401, 'Нужен отдельный ключ приёма заявок')
    token = authorization[len('Bearer '):]
    try:
        connection = (await db.execute(select(WebsiteIntegrationConnection).where(
            WebsiteIntegrationConnection.token_hash == hashlib.sha256(token.encode()).hexdigest(),
            WebsiteIntegrationConnection.revoked == False,
            WebsiteIntegrationConnection.expires_at > utcnow()))).scalar_one_or_none()
    except SQLAlchemyError:
        await db.rollback()
        raise HTTPException(503, 'Приём временно недоступен') from None
    if connection is None:
        raise HTTPException(401, 'Ключ истёк, отозван или неверен')
    return connection


@router.post('/service-requests')
async def intake(request: Request, response: Response, db=Depends(get_db), connection=Depends(intake_connection)):
    if request.headers.get('content-type', '').split(';')[0].strip().lower() != 'application/json':
        raise HTTPException(415, 'Нужен application/json')
    chunks = bytearray()
    async for chunk in request.stream():
        chunks.extend(chunk)
        if len(chunks) > MAX_BYTES:
            raise HTTPException(413, 'Заявка слишком большая')
    try:
        original_payload = json.loads(chunks)
        body = WebsiteIntake.model_validate(original_payload)
        key = UUID(request.headers.get('Idempotency-Key', ''))
    except (ValidationError, ValueError, TypeError, UnicodeDecodeError, RecursionError):
        # Never echo the rejected contact payload into error diagnostics.
        raise HTTPException(422, 'Некорректный контракт заявки или Idempotency-Key') from None
    if key != body.external_id:
        raise HTTPException(422, 'Idempotency-Key не совпадает с external_id')
    try:
        row, created = await receive(db, body, original_payload)
        await db.commit()
    except SQLAlchemyError:
        await db.rollback()
        raise HTTPException(503, 'Не удалось подтвердить сохранение. Повторите с тем же external_id.') from None
    response.status_code = 201 if created else 200
    response.headers['Cache-Control'] = 'no-store'
    return {'id': row.id, 'external_id': str(row.external_id)}
