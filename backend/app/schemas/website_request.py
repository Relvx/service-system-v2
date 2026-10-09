from datetime import datetime, timezone
from typing import Annotated, Literal
from uuid import UUID
import re
from pydantic import BaseModel, ConfigDict, Field, StrictBool, field_validator, model_validator

Name = Annotated[str, Field(min_length=1, max_length=100)]
Email = Annotated[str, Field(max_length=254)]
Phone = Annotated[str, Field(pattern=r'^\+?[0-9]{10,15}$', max_length=20)]
RequestStatus = Literal['new', 'in_progress', 'closed', 'spam']


class StrictModel(BaseModel):
    model_config = ConfigDict(extra='forbid')

    @field_validator('*', mode='before')
    @classmethod
    def postgres_safe_text(cls, value):
        if isinstance(value, str) and ('\x00' in value or any(0xD800 <= ord(c) <= 0xDFFF for c in value)):
            raise ValueError('Unsupported text characters')
        return value


class Consent(StrictModel):
    accepted: StrictBool
    accepted_at: datetime
    policy_version: Annotated[str, Field(min_length=1, max_length=100)]

    @field_validator('accepted')
    @classmethod
    def accepted_only(cls, value):
        if not value:
            raise ValueError('Consent is required')
        return value

    @field_validator('accepted_at')
    @classmethod
    def aware_time(cls, value):
        if value.tzinfo is None:
            raise ValueError('Timezone is required')
        try:
            return value.astimezone(timezone.utc)
        except OverflowError:
            raise ValueError('Datetime is outside the supported range') from None


class LegacyEquipment(StrictModel):
    description: Annotated[str, Field(max_length=300)] | None = None
    power: Annotated[str, Field(max_length=100)]


class WebsiteIntake(StrictModel):
    schema_version: Annotated[int, Field(strict=True, ge=1, le=1)]
    external_id: UUID
    website_reference: Annotated[str, Field(pattern=r'^AG-[0-9]{6,20}$', max_length=40)]
    submitted_at: datetime
    request_mode: Literal['callback', 'detailed']
    request_intent: Literal['general', 'documents', 'verification']
    customer_type: Literal['private', 'legal', 'budget', 'other'] | None = None
    contact_name: Name | None = None
    company_name: Annotated[str, Field(min_length=1, max_length=180)] | None = None
    phone: Phone
    email: Email | None = None
    service_category: Literal['boiler', 'gas', 'heat', 'other'] | None = None
    work_type: Literal['maintenance', 'diagnostics', 'repair', 'commissioning', 'verification', 'emergency', 'consultation', 'other'] | None = None
    cooperation_format: Literal['single', 'contract', 'undecided'] | None = None
    object_address: Annotated[str, Field(max_length=300)] | None = None
    message: Annotated[str, Field(max_length=3000)] | None = None
    source_page: Annotated[str, Field(pattern=r'^/(?:[a-zA-Z0-9_-]+/)*$', max_length=300)]
    legacy_form_type: Literal['lead_contact', 'lead_kp', 'lead_emergency', 'lead_to']
    legacy_equipment: LegacyEquipment | None = None
    consent: Consent

    @field_validator('submitted_at')
    @classmethod
    def aware_time(cls, value):
        return Consent.aware_time(value)

    @field_validator('email')
    @classmethod
    def valid_email(cls, value):
        if value is not None and not re.fullmatch(r'[^\s@]+@[^\s@]+\.[^\s@]+', value):
            raise ValueError('Invalid email')
        return value

    @model_validator(mode='after')
    def consistent(self):
        if self.customer_type in ('legal', 'budget') and not self.company_name:
            raise ValueError('Company is required')
        if self.request_mode == 'callback' and any(getattr(self, key) is not None for key in (
            'customer_type', 'contact_name', 'company_name', 'email', 'service_category',
            'work_type', 'cooperation_format', 'object_address', 'message', 'legacy_equipment')):
            raise ValueError('Callback has phone and intent only')
        return self


class WorkingData(StrictModel):
    contact_name: Name | None = None
    company_name: Annotated[str, Field(max_length=180)] | None = None
    phone: Phone | None = None
    email: Email | None = None
    object_address: Annotated[str, Field(max_length=300)] | None = None
    message: Annotated[str, Field(max_length=3000)] | None = None

    _email = field_validator('email')(WebsiteIntake.valid_email.__func__)


class RequestUpdate(StrictModel):
    version: Annotated[int, Field(strict=True, ge=1)]
    status: RequestStatus | None = None
    assigned_user_id: Annotated[int, Field(strict=True, gt=0)] | None = None
    working_data: WorkingData | None = None
    outcome: Annotated[str, Field(max_length=2000)] | None = None

    @model_validator(mode='after')
    def non_null_changes(self):
        for key in ('status', 'working_data'):
            if key in self.model_fields_set and getattr(self, key) is None:
                raise ValueError(f'{key} cannot be null')
        return self


class CommentInput(StrictModel):
    text: Annotated[str, Field(min_length=1, max_length=3000)]

    @field_validator('text')
    @classmethod
    def not_blank(cls, value):
        if not value.strip():
            raise ValueError('Comment cannot be blank')
        return value.strip()


class ConnectionInput(StrictModel):
    label: Annotated[str, Field(min_length=1, max_length=100)] = 'Сайт Аналит-ГАЗ'
    expires_days: Annotated[int, Field(strict=True, ge=1, le=365)] = 90


class NewClient(StrictModel):
    name: Annotated[str, Field(min_length=1, max_length=300)]


class NewContact(StrictModel):
    contact_name: Name
    phone: Phone | None = None
    email: Email | None = None

    _email = field_validator('email')(WebsiteIntake.valid_email.__func__)


class NewSite(StrictModel):
    title: Annotated[str, Field(min_length=1, max_length=300)]
    address: Annotated[str, Field(min_length=1, max_length=300)]


class LinkInput(StrictModel):
    command_id: UUID
    version: Annotated[int, Field(strict=True, ge=1)]
    client_id: Annotated[int, Field(strict=True, gt=0)] | None = None
    new_client: NewClient | None = None
    contact_id: Annotated[int, Field(strict=True, gt=0)] | None = None
    new_contact: NewContact | None = None
    site_id: Annotated[int, Field(strict=True, gt=0)] | None = None
    new_site: NewSite | None = None

    @model_validator(mode='after')
    def choices(self):
        if bool(self.client_id) == bool(self.new_client):
            raise ValueError('Choose an existing or new client')
        if self.contact_id and self.new_contact or self.site_id and self.new_site:
            raise ValueError('Choose existing or new entities, not both')
        return self
