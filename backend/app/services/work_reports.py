import hashlib
import json
import re
from difflib import SequenceMatcher
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field

SOURCE_FIELDS = ('work_summary', 'defects_summary', 'recommendations')
SOURCE_LABELS = {'work_summary': 'Итог работ', 'defects_summary': 'Обнаруженные дефекты', 'recommendations': 'Рекомендации'}


class ProposalInput(BaseModel):
    model_config = ConfigDict(extra='forbid')
    visit_id: int = Field(gt=0)
    report_hash: str = Field(pattern=r'^[a-f0-9]{64}$')
    title: str = Field(min_length=3, max_length=300)
    description: str = Field(default='', max_length=3000)
    source_field: Literal['work_summary', 'defects_summary', 'recommendations']
    source_quote: str = Field(min_length=3, max_length=5000)
    priority: Literal['low', 'medium', 'high', 'urgent'] = 'medium'
    action_type: Literal['repair', 'replace', 'monitor', 'other'] = 'repair'
    suggested_parts: str = Field(default='', max_length=1000)
    review_reason: str = Field(default='', max_length=1000)


def report_snapshot(visit):
    data = {field: getattr(visit, field) or '' for field in SOURCE_FIELDS}
    data.update(site_id=visit.site_id, status=visit.status, is_archived=visit.is_archived,
                planned_date=str(visit.planned_date))
    return data


def report_hash(visit):
    return hashlib.sha256(json.dumps(report_snapshot(visit), ensure_ascii=False, sort_keys=True).encode()).hexdigest()


def validate_source(visit, proposal):
    if proposal.report_hash != report_hash(visit):
        raise ValueError('Отчёт изменился. Получите текущий отчёт и повторите предложение.')
    if not proposal.title.strip() or not proposal.source_quote.strip():
        raise ValueError('Название и цитата не могут быть пустыми.')
    if proposal.source_quote not in (getattr(visit, proposal.source_field) or ''):
        raise ValueError('Цитата должна точно совпадать с текстом выбранного поля отчёта.')


def proposal_key(proposal):
    return hashlib.sha256(json.dumps(proposal.model_dump(), ensure_ascii=False, sort_keys=True).encode()).hexdigest()


def possible_duplicates(title, defects):
    def normalized(s):
        return re.sub(r'\W+', ' ', s.casefold()).strip()
    title = normalized(title)
    return [d.id for d in defects if re.findall(r'\d+', title) == re.findall(r'\d+', normalized(d.title))
            and SequenceMatcher(None, title, normalized(d.title)).ratio() >= 0.92]
